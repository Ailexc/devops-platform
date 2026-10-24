package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// CMDBModel mock-cmdb 数据模型
type CMDBModel struct {
	ID               uint64         `json:"id"`
	Name             string         `json:"name"`
	Code             string         `json:"code"`
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
		if _, err := c.repo.UpsertModel(&model.ResourceModel{
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
	total, written, skipped := 0, 0, 0
	for _, m := range models {
		var insts []CMDBInstance
		if err := c.getJSON(ctx, "/api/v1/models/"+m.Code+"/instances", &insts); err != nil {
			c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return err
		}
		for _, inst := range insts {
			ok, err := c.repo.UpsertInstance(&model.ResourceInstance{
				ModelID:           m.ID,
				ExternalID:        fmt.Sprintf("%s-%d", m.Code, inst.ID),
				Name:              inst.Name,
				Attributes:        inst.Attributes,
				OwnerID:           inst.OwnerID,
				UpstreamUpdatedAt: parseUpstreamTS(inst.UpdatedAt),
				SyncedAt:          &now,
			})
			if err != nil {
				c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
				return err
			}
			if ok {
				written++
			} else {
				skipped++
			}
		}
		total += len(insts)
	}
	c.syncs.FinishJob(job.ID, 2, map[string]any{"instances": total, "written": written, "skipped": skipped})
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
		_, err = c.repo.UpsertInstance(&model.ResourceInstance{
			ModelID:           m.ID,
			ExternalID:        fmt.Sprintf("%s-%d", m.Code, inst.ID),
			Name:              inst.Name,
			Attributes:        inst.Attributes,
			OwnerID:           inst.OwnerID,
			UpstreamUpdatedAt: parseUpstreamTS(inst.UpdatedAt),
			SyncedAt:          &now,
		})
		return err
	case "delete":
		return c.repo.DeleteInstanceByExternal(m.ID, instID)
	}
	return nil
}

// parseUpstreamTS 解析上游 updated_at → 对账基准（单调守卫与 A4 水位的比对依据）。
// 解析失败/缺省返回 nil：未知时间戳不参与单调守卫（fp 去重仍生效），不阻塞同步。
func parseUpstreamTS(s string) *time.Time {
	if s == "" {
		return nil
	}
	t, err := time.Parse(time.RFC3339, s) // RFC3339 解析自动接受小数秒（A3 升毫秒后兼容）
	if err != nil {
		return nil
	}
	return &t
}

// FingerprintInfo 集合指纹端点响应（契约算法见 mock /sync/fingerprint 注释，两侧必须逐字一致）
type FingerprintInfo struct {
	Version       uint64 `json:"version"`
	Count         int    `json:"count"`
	MaxUpdatedAt  string `json:"max_updated_at"`
	HashIDs       string `json:"hash_ids"`
	HashUpdatedAt string `json:"hash_updated_at"`
	Fingerprint   string `json:"fingerprint"`
}

// FetchFingerprint 拉上游集合指纹（巡检脏检 / 强一致档指纹快查）
func (c *CMDBConnector) FetchFingerprint(ctx context.Context, modelCode string) (*FingerprintInfo, error) {
	var out FingerprintInfo
	if err := c.getJSON(ctx, "/sync/fingerprint?model="+url.QueryEscape(modelCode), &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// EnsureFresh 强一致档（清单 2.3 强一致档 / A6）：指纹快查 → 失配触发前置同步。
// 判定主体仍是权限中心，上游永不判定；带超时兜底——超时按本地投影判定，不阻塞热路径。
// 返回 (changed, err)：err 非空=超时/不可达（调用方降级按本地判 + warning）
func (c *CMDBConnector) EnsureFresh(ctx context.Context, modelCode string, timeout time.Duration) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	up, err := c.FetchFingerprint(ctx, modelCode)
	if err != nil {
		return false, err
	}
	localIDs, localTS, _, err := c.repo.SetFingerprint(modelCode)
	if err != nil {
		return false, err
	}
	if localIDs == up.HashIDs && localTS == up.HashUpdatedAt {
		return false, nil // 已新鲜，无需同步
	}
	_, _, _, _, err = c.SyncInstancesSince(ctx, modelCode, nil, 0)
	return err == nil, err
}

// SyncInstancesSince 增量水位同步（清单 A4，水位推进三句语义的"拉取+写库"半段）：
//   - after = 水位回拨重叠窗口（watermark=nil → 从零时刻起，等价首轮全量）
//   - queryStart = 首次请求发起时刻 = 返回给调用方的新水位（**不是批内 max(updated_at)**）
//   - 分页拉取（page_size=100），逐条 upsert（fp 去重 + 单调守卫，重叠区幂等）
//
// 调用方（巡检）负责：本函数返回 nil（=全部写成功）后才 UpdateWatermark(queryStart)——批末推进。
func (c *CMDBConnector) SyncInstancesSince(ctx context.Context, modelCode string, watermark *time.Time, overlap time.Duration) (written, skipped, total int, queryStart time.Time, err error) {
	m, err := c.repo.ModelByCode(modelCode)
	if err != nil {
		return 0, 0, 0, queryStart, err
	}
	after := time.Time{}
	if watermark != nil {
		after = watermark.Add(-overlap)
	}
	queryStart = time.Now()
	job := &model.SyncJob{Type: model.SyncCMDBInst, Status: 1}
	ts := queryStart
	job.StartedAt = &ts
	c.syncs.CreateJob(job)
	defer func() {
		if err != nil {
			c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return
		}
		c.syncs.FinishJob(job.ID, 2, map[string]any{
			"since": after.Format(time.RFC3339Nano), "written": written, "skipped": skipped, "total": total,
		})
	}()
	page := 1
	for {
		var insts []CMDBInstance
		path := fmt.Sprintf("/api/v1/models/%s/instances?updated_after=%s&page=%d&page_size=100",
			m.Code, url.QueryEscape(after.Format(time.RFC3339Nano)), page)
		if err = c.getJSON(ctx, path, &insts); err != nil {
			return
		}
		for _, inst := range insts {
			ok, uerr := c.repo.UpsertInstance(&model.ResourceInstance{
				ModelID:           m.ID,
				ExternalID:        fmt.Sprintf("%s-%d", m.Code, inst.ID),
				Name:              inst.Name,
				Attributes:        inst.Attributes,
				OwnerID:           inst.OwnerID,
				UpstreamUpdatedAt: parseUpstreamTS(inst.UpdatedAt),
				SyncedAt:          &ts,
			})
			if uerr != nil {
				err = uerr
				return
			}
			if ok {
				written++
			} else {
				skipped++
			}
			total++
		}
		if len(insts) < 100 {
			break
		}
		page++
	}
	return
}

// FetchAllInstances 全量分页拉取（不带过滤；深对账"先取后比再写"的取数半段，清单 A5b）
func (c *CMDBConnector) FetchAllInstances(ctx context.Context, modelCode string) ([]CMDBInstance, error) {
	var all []CMDBInstance
	page := 1
	for {
		var insts []CMDBInstance
		path := fmt.Sprintf("/api/v1/models/%s/instances?page=%d&page_size=100", modelCode, page)
		if err := c.getJSON(ctx, path, &insts); err != nil {
			return nil, err
		}
		all = append(all, insts...)
		if len(insts) < 100 {
			break
		}
		page++
	}
	return all, nil
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
