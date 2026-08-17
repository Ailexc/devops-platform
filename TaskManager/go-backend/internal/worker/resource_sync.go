package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/cmdbstore"
	"cmdb-go/internal/pkg/result"
	"cmdb-go/internal/tasktypes"

	"github.com/hibiken/asynq"
	"gorm.io/gorm"
)

// ResourceSyncHandler handles resource synchronization tasks.
type ResourceSyncHandler struct {
	db       *gorm.DB
	store    *cmdbstore.Store
	registry *orchestrator.Registry
}

// NewResourceSyncHandler creates a new resource sync handler.
func NewResourceSyncHandler(db *gorm.DB, store *cmdbstore.Store, registry *orchestrator.Registry) *ResourceSyncHandler {
	return &ResourceSyncHandler{db: db, store: store, registry: registry}
}

// HandleTask processes asynq resource sync tasks.
func (h *ResourceSyncHandler) HandleTask(ctx context.Context, t *asynq.Task) error {
	var payload tasktypes.ResourceSyncPayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	slog.Info("resource_sync: starting",
		"execution_id", payload.ExecutionID,
		"resource", payload.Resource,
		"account", payload.Account,
		"region", payload.Region,
	)

	result, err := h.SyncResource(ctx, payload.Account, payload.Region, payload.Resource, payload.Mode, payload.ExecutionID)
	if err != nil {
		return err
	}

	slog.Info("resource_sync: completed",
		"resource", payload.Resource,
		"result", result,
	)

	return nil
}

// SyncResource performs resource synchronization for a given resource type.
func (h *ResourceSyncHandler) SyncResource(ctx context.Context, account, region, resourceType, mode string, executionID int64) (map[string]interface{}, error) {
	rb := result.New()
	rb.Log("开始资源同步")
	rb.Log(fmt.Sprintf("account: %s, region: %s, resource: %s, mode: %s", account, region, resourceType, mode))

	// 1. Read CMDB存量
	rb.Log("① 读取CMDB存量数据")
	existingKeys, _ := h.store.ListByModule(ctx, resourceType)
	rb.AddStat("cmdb_existing", "CMDB存量", len(existingKeys), "个")

	// 2. 采集AWS数据 (stub - would use aws-sdk-go-v2)
	rb.Log("② 采集AWS资源数据")
	rb.Log("（demo模式：使用模拟数据）")
	var awsItems []map[string]interface{}

	// 3. Diff对比
	rb.Log("③ 对比Diff")
	adds, updates, deletes := h.store.Diff(ctx, resourceType, extractKeys(awsItems, h.getBindKey(resourceType)))
	rb.AddStat("adds", "新增", len(adds), "个")
	rb.AddStat("updates", "更新", len(updates), "个")
	rb.AddStat("deletes", "删除", len(deletes), "个")

	// 4. 批量写入
	rb.Log("④ 批量写入CMDB")
	if len(awsItems) > 0 {
		count, _ := h.store.BatchPut(ctx, resourceType, awsItems, h.getBindKey(resourceType))
		rb.AddStat("synced", "同步写入", count, "个")
	}
	rb.AddStat("total", "资源总量", len(existingKeys)+len(adds), "个")

	rb.Log("资源同步完成")

	return rb.Build(), nil
}

func (h *ResourceSyncHandler) getBindKey(resourceType string) string {
	res := h.registry.GetResource(resourceType)
	if res != nil {
		return res.BindKey
	}
	return "id"
}

func extractKeys(items []map[string]interface{}, keyField string) []string {
	var keys []string
	for _, item := range items {
		if k, ok := item[keyField].(string); ok {
			keys = append(keys, k)
		}
	}
	return keys
}
