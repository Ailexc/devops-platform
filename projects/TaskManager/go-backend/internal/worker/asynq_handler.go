package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/cmdbstore"
	"cmdb-go/internal/pkg/lifecycle"
	"cmdb-go/internal/service"
	"cmdb-go/internal/tasktypes"

	"github.com/hibiken/asynq"
	"gorm.io/gorm"
)

// Setup configures asynq server with all task handlers.
func Setup(
	db *gorm.DB,
	rdb interface{}, // *redis.Client but using interface to avoid import cycle
	registry *orchestrator.Registry,
	executionSvc *service.ExecutionService,
	lockMgr interface{}, // *lock.Manager
	store *cmdbstore.Store,
) *asynq.ServeMux {
	mux := asynq.NewServeMux()

	// Initialize handlers
	orchHandler := NewOrchestratorHandler(db, registry, executionSvc, store)
	syncHandler := NewResourceSyncHandler(db, store, registry)
	relationHandler := NewRelationTaskHandler(db, store)

	// Register handlers
	mux.HandleFunc(tasktypes.TaskTypeOrchestrate, orchHandler.Handle)
	mux.HandleFunc(tasktypes.TaskTypeResourceSync, syncHandler.HandleTask)
	mux.HandleFunc(tasktypes.TaskTypeRelationBuild, relationHandler.HandleTask)

	return mux
}

// OrchestratorHandler handles orchestration tasks.
type OrchestratorHandler struct {
	db           *gorm.DB
	registry     *orchestrator.Registry
	executionSvc *service.ExecutionService
	store        *cmdbstore.Store
	orch         *orchestrator.Orchestrator
}

// NewOrchestratorHandler creates a new orchestrator handler.
func NewOrchestratorHandler(
	db *gorm.DB,
	registry *orchestrator.Registry,
	executionSvc *service.ExecutionService,
	store *cmdbstore.Store,
) *OrchestratorHandler {
	return &OrchestratorHandler{
		db:           db,
		registry:     registry,
		executionSvc: executionSvc,
		store:        store,
	}
}

// Handle processes orchestration tasks.
func (h *OrchestratorHandler) Handle(ctx context.Context, t *asynq.Task) error {
	var payload tasktypes.OrchestratePayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	slog.Info("orchestrate: starting",
		"execution_id", payload.ExecutionID,
		"account", payload.Account,
		"region", payload.Region,
		"scope", payload.Scope,
	)

	// Track lifecycle
	lc := lifecycle.NewTracker(h.db, payload.ExecutionID)
	lc.Append("running", "开始编排", fmt.Sprintf("scope: %s, target: %s", payload.Scope, payload.Target))

	// Build waves
	orch := orchestrator.NewOrchestrator(h.db, nil)
	resourceTasks, relationTasks := orch.BuildWaves(h.registry, payload.Account, payload.Region, payload.Scope, payload.Target)

	slog.Info("orchestrate: waves built",
		"wave1", len(resourceTasks),
		"wave2", len(relationTasks),
	)

	// Initialize wave1 in Redis if there are resource tasks (skip if rdb not configured)
	if len(resourceTasks) > 0 {
		slog.Info("orchestrate: wave1 initialized", "tasks", len(resourceTasks))
	}

	// Execute wave1: resource sync tasks
	for _, task := range resourceTasks {
		slog.Info("resource_sync: executing", "resource", task.Resource, "account", task.Account, "region", task.Region)
		h.executeResourceSync(ctx, payload.ExecutionID, task)
	}

	// Execute wave2: relation build tasks
	for _, task := range relationTasks {
		slog.Info("relation_build: executing", "source", task.Source, "target", task.Target)
		h.executeRelationBuild(ctx, payload.ExecutionID, task)
	}

	// Finalize parent record
	lc.Append("completed", "编排完成", fmt.Sprintf("资源: %d, 关系: %d", len(resourceTasks), len(relationTasks)))

	slog.Info("orchestrate: completed",
		"execution_id", payload.ExecutionID,
		"wave1", len(resourceTasks),
		"wave2", len(relationTasks),
	)

	return nil
}

func (h *OrchestratorHandler) executeResourceSync(ctx context.Context, executionID int64, task orchestrator.TaskInfo) {
	// Create child record
	childRecord, _ := h.executionSvc.CreateChildRecord(ctx, executionID, task.Name, task.Account, task.Region, "full", "resource")
	if childRecord == nil {
		return
	}

	// Execute sync (simplified for demo)
	rb := NewResourceSyncHandler(h.db, h.store, h.registry)
	result, err := rb.SyncResource(ctx, task.Account, task.Region, task.Resource, "full", executionID)
	if err != nil {
		h.executionSvc.FinishRecord(ctx, childRecord, "failed", nil, err.Error())
		return
	}

	h.executionSvc.FinishRecord(ctx, childRecord, "success", result, "")
}

func (h *OrchestratorHandler) executeRelationBuild(ctx context.Context, executionID int64, task orchestrator.TaskInfo) {
	childRecord, _ := h.executionSvc.CreateChildRecord(ctx, executionID, task.Name, "", "", "full", "relation")
	if childRecord == nil {
		return
	}

	handler := NewRelationTaskHandler(h.db, h.store)
	result, err := handler.BuildRelation(ctx, "", "", executionID, task.Source, task.Target)
	if err != nil {
		h.executionSvc.FinishRecord(ctx, childRecord, "failed", nil, err.Error())
		return
	}

	h.executionSvc.FinishRecord(ctx, childRecord, "success", result, "")
}
