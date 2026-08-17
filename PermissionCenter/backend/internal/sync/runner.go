package sync

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// OpenAPISyncer 拉取应用 OpenAPI 文档 → 生成权限点 + 板块模板
type OpenAPISyncer struct {
	client *http.Client
	acc    *store.AccessRepo
	syncs  *store.SyncRepo
}

func NewOpenAPISyncer(acc *store.AccessRepo, syncs *store.SyncRepo) *OpenAPISyncer {
	return &OpenAPISyncer{client: &http.Client{Timeout: 10 * time.Second}, acc: acc, syncs: syncs}
}

// Sync 执行 OpenAPI 同步
// deny-by-default：新增权限点默认不授予任何角色/策略
func (s *OpenAPISyncer) Sync(ctx context.Context, app *model.App) (map[string]any, error) {
	job := &model.SyncJob{Type: model.SyncOpenAPI, Status: 1}
	now := time.Now()
	job.StartedAt = &now
	s.syncs.CreateJob(job)

	raw, err := s.fetch(ctx, app.OpenAPIURL)
	if err != nil {
		s.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return nil, err
	}
	actions, err := ParseOpenAPI(raw, app.Code)
	if err != nil {
		s.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return nil, err
	}

	// 按 tag 分组 → 模板
	tagActions := map[string][]*model.Action{}
	var actionByID = map[uint64]string{}
	for _, a := range actions {
		act := &model.Action{
			AppID:        app.ID,
			Code:         a.Code,
			Name:         a.Name,
			Resource:     a.Resource,
			Operation:    a.Operation,
			Method:       a.Method,
			Path:         a.Path,
			IsGeneric:    a.IsGeneric,
			ResourceSlot: a.ResourceSlot,
			// 接口契约（v12）：请求/响应示例
			ReqExample:  a.ReqExample,
			RespExample: a.RespExample,
		}
		if err := s.acc.UpsertAction(act); err != nil {
			s.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return nil, err
		}
		// 幂等：取回 id
		saved, err := s.acc.ActionByCode(app.ID, a.Code)
		if err != nil {
			continue
		}
		actionByID[saved.ID] = a.Code
		tag := a.Tag
		if tag == "" {
			tag = "未分类"
		}
		tagActions[tag] = append(tagActions[tag], saved)
	}

	// 模板幂等：按 app+name 查/建
	templates, err := s.acc.Templates(app.ID)
	if err != nil {
		s.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return nil, err
	}
	existing := map[string]uint64{}
	for _, t := range templates {
		existing[t.Name] = t.ID
	}
	for tag, acts := range tagActions {
		tid, ok := existing[tag]
		if !ok {
			t := &model.PermissionTemplate{AppID: app.ID, Name: tag}
			if err := s.acc.CreateTemplate(t); err != nil {
				continue
			}
			tid = t.ID
		}
		ids := make([]uint64, 0, len(acts))
		for _, a := range acts {
			ids = append(ids, a.ID)
		}
		s.acc.SetTemplateActions(tid, ids)
	}

	res := map[string]any{"actions": len(actions), "templates": len(tagActions)}
	s.syncs.FinishJob(job.ID, 2, res)
	return res, nil
}

func (s *OpenAPISyncer) fetch(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("fetch %s -> %d", url, resp.StatusCode)
	}
	return io.ReadAll(resp.Body)
}

// FetchRaw 拉取 OpenAPI 原始文档（能力声明推断 / 契约测试用）
func (s *OpenAPISyncer) FetchRaw(ctx context.Context, url string) ([]byte, error) {
	return s.fetch(ctx, url)
}
