package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// CMDBModel mock-cmdb 数据模型
type CMDBModel struct {
	ID              uint64         `json:"id"`
	Name            string         `json:"name"`
	Code            string         `json:"code"`
	AttributesSchema map[string]any `json:"attributes_schema"`
}

// CMDBInstance mock-cmdb 实例
type CMDBInstance struct {
	ID         uint64         `json:"id"`
	Name       string         `json:"name"`
	Attributes map[string]any `json:"attributes"`
	OwnerID    *uint64        `json:"owner_id"`
	UpdatedAt  string         `json:"updated_at"`
}

// CMDBConnector 同步 mock-cmdb 模型/实例 → 本地资源索引（解耦数据源）
type CMDBConnector struct {
	baseURL string
	client  *http.Client
	repo    *store.ResourceRepo
	syncs   *store.SyncRepo
	appID   uint64 // 资源归属应用（模型投影的 app 维度）
}

// SetAppID 设置资源归属应用（用于"我接入了谁"展示对方数据模型）
func (c *CMDBConnector) SetAppID(id uint64) { c.appID = id }

func NewCMDBConnector(baseURL string, repo *store.ResourceRepo, syncs *store.SyncRepo) *CMDBConnector {
	return &CMDBConnector{
		baseURL: baseURL,
		client:  &http.Client{Timeout: 10 * time.Second},
		repo:    repo,
		syncs:   syncs,
	}
}

// SyncModels 全量同步模型
func (c *CMDBConnector) SyncModels(ctx context.Context) error {
	job := &model.SyncJob{Type: model.SyncCMDBModel, Status: 1}
	now := time.Now()
	job.StartedAt = &now
	c.syncs.CreateJob(job)

	var models []CMDBModel
	if err := c.getJSON(ctx, "/api/v1/models", &models); err != nil {
		c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return err
	}
	for _, m := range models {
		if err := c.repo.UpsertModel(&model.ResourceModel{
			SourceID:         m.ID,
			AppID:            c.appID,
			Name:             m.Name,
			Code:             m.Code,
			AttributesSchema: m.AttributesSchema,
			SyncedAt:         &now,
		}); err != nil {
			c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return err
		}
	}
	c.syncs.FinishJob(job.ID, 2, map[string]any{"models": len(models)})
	return nil
}

// SyncInstances 全量同步实例到索引
func (c *CMDBConnector) SyncInstances(ctx context.Context) error {
	job := &model.SyncJob{Type: model.SyncCMDBInst, Status: 1}
	now := time.Now()
	job.StartedAt = &now
	c.syncs.CreateJob(job)

	models, err := c.repo.Models()
	if err != nil {
		return err
	}
	total := 0
	for _, m := range models {
		var insts []CMDBInstance
		if err := c.getJSON(ctx, "/api/v1/models/"+m.Code+"/instances", &insts); err != nil {
			c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return err
		}
		for _, inst := range insts {
			if err := c.repo.UpsertInstance(&model.ResourceInstance{
				ModelID:    m.ID,
				ExternalID: fmt.Sprintf("%s-%d", m.Code, inst.ID),
				Name:       inst.Name,
				Attributes: inst.Attributes,
				OwnerID:    inst.OwnerID,
				SyncedAt:   &now,
			}); err != nil {
				c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
				return err
			}
		}
		total += len(insts)
	}
	c.syncs.FinishJob(job.ID, 2, map[string]any{"instances": total})
	return nil
}

// HandleEvent 处理 CMDB 变更事件（webhook / Redis Streams 统一入口）
func (c *CMDBConnector) HandleEvent(ctx context.Context, event map[string]any) error {
	evType, _ := event["type"].(string)
	modelCode, _ := event["model"].(string)
	instID, _ := event["instance_id"].(string)

	m, err := c.repo.ModelByCode(modelCode)
	if err != nil {
		return fmt.Errorf("model not found: %s", modelCode)
	}
	switch evType {
	case "create", "update":
		// 增量：从 CMDB 拉最新实例补写
		var inst CMDBInstance
		if err := c.getJSON(ctx, fmt.Sprintf("/api/v1/models/%s/instances/%s", modelCode, instID), &inst); err != nil {
			return err
		}
		now := time.Now()
		return c.repo.UpsertInstance(&model.ResourceInstance{
			ModelID:    m.ID,
			ExternalID: fmt.Sprintf("%s-%d", m.Code, inst.ID),
			Name:       inst.Name,
			Attributes: inst.Attributes,
			OwnerID:    inst.OwnerID,
			SyncedAt:   &now,
		})
	case "delete":
		return c.repo.DeleteInstanceByExternal(m.ID, instID)
	}
	return nil
}

func (c *CMDBConnector) getJSON(ctx context.Context, path string, out any) error {
	url := strings.TrimRight(c.baseURL, "/") + path
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("cmdb %s -> %d", path, resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, out)
}
