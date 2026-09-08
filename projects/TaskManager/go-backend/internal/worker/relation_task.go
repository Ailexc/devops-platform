package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"cmdb-go/internal/pkg/cmdbstore"
	"cmdb-go/internal/pkg/result"
	"cmdb-go/internal/tasktypes"

	"github.com/hibiken/asynq"
	"gorm.io/gorm"
)

// RelationTaskHandler handles relationship computation tasks.
type RelationTaskHandler struct {
	db    *gorm.DB
	store *cmdbstore.Store
}

// NewRelationTaskHandler creates a new relation task handler.
func NewRelationTaskHandler(db *gorm.DB, store *cmdbstore.Store) *RelationTaskHandler {
	return &RelationTaskHandler{db: db, store: store}
}

// HandleTask processes asynq relation build tasks.
func (h *RelationTaskHandler) HandleTask(ctx context.Context, t *asynq.Task) error {
	var payload tasktypes.RelationBuildPayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	slog.Info("relation_build: starting",
		"execution_id", payload.ExecutionID,
		"source", payload.Source,
		"target", payload.Target,
	)

	res, err := h.BuildRelation(ctx, payload.Account, payload.Region, payload.ExecutionID, payload.Source, payload.Target)
	if err != nil {
		return err
	}

	slog.Info("relation_build: completed",
		"source", payload.Source,
		"target", payload.Target,
		"result", res,
	)

	return nil
}

// BuildRelation computes relationships between two resource types.
func (h *RelationTaskHandler) BuildRelation(ctx context.Context, account, region string, executionID int64, source, target string) (map[string]interface{}, error) {
	rb := result.New()
	rb.Log(fmt.Sprintf("开始关系计算: %s → %s", source, target))

	// Read source resources
	rb.Log("读取源端资源")
	sourceItems, err := h.store.ListAllByModule(ctx, source)
	if err != nil {
		rb.Fail(fmt.Sprintf("读取源端资源失败: %v", err))
		return rb.Build(), nil
	}
	rb.AddStat("source_count", "源端资源数", len(sourceItems), "个")

	// Read target resources
	rb.Log("读取目标端资源")
	targetItems, err := h.store.ListAllByModule(ctx, target)
	if err != nil {
		rb.Fail(fmt.Sprintf("读取目标端资源失败: %v", err))
		return rb.Build(), nil
	}
	rb.AddStat("target_count", "目标端资源数", len(targetItems), "个")

	// Compute bindings (simplified)
	rb.Log("计算资源绑定关系")
	bindingCount := 0
	for _, src := range sourceItems {
		if vpcID, ok := src["vpc_id"].(string); ok && vpcID != "" {
			for _, tgt := range targetItems {
				if tgtVpcID, ok := tgt["vpc_id"].(string); ok && tgtVpcID == vpcID {
					bindingCount++
					break
				}
			}
		}
	}
	rb.AddStat("bindings", "绑定关系数", bindingCount, "对")

	slog.Info("relation_task: completed",
		"source", source,
		"target", target,
		"bindings", bindingCount,
	)

	rb.Log("关系计算完成")
	return rb.Build(), nil
}
