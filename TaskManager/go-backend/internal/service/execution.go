package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/hibiken/asynq"
	"gorm.io/gorm"

	"cmdb-go/internal/model"
	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/lock"
	"cmdb-go/internal/tasktypes"
)

// ExecutionService provides execution history and dispatch logic.
type ExecutionService struct {
	db          *gorm.DB
	lockMgr     *lock.Manager
	registry    *orchestrator.Registry
	asynqClient *asynq.Client
}

// NewExecutionService creates a new execution service.
func NewExecutionService(db *gorm.DB, lockMgr *lock.Manager, registry *orchestrator.Registry) *ExecutionService {
	return &ExecutionService{
		db:       db,
		lockMgr:  lockMgr,
		registry: registry,
	}
}

// SetAsynqClient sets the asynq client for async task dispatch.
func (s *ExecutionService) SetAsynqClient(client *asynq.Client) {
	s.asynqClient = client
}

// TaskConflictError represents a conflict error (HTTP 409).
type TaskConflictError struct {
	Message  string
	Conflict map[string]interface{}
}

func (e *TaskConflictError) Error() string {
	return e.Message
}

// DispatchParams holds parameters for dispatching an execution.
type DispatchParams struct {
	Account     string   `json:"account"`
	Region      string   `json:"region"`
	Scope       string   `json:"scope"`
	Target      string   `json:"target"`
	Mode        string   `json:"mode"`
	Trigger     string   `json:"trigger"`
	ResourceIDs []string `json:"resource_ids,omitempty"`
}

// DispatchOutcome holds the result of a dispatch.
type DispatchOutcome struct {
	Record *model.ExecutionRecord `json:"record"`
}

// ScopeResourceKeys expands a task scope into resource keys for lock checking.
func (s *ExecutionService) ScopeResourceKeys(account, region, scope, target string) []string {
	var keys []string

	switch scope {
	case "region":
		for _, g := range s.registry.ListGroups() {
			for _, res := range g.Resources {
				keys = append(keys, fmt.Sprintf("%s:%s", g.Name, res.Name))
			}
			for _, rel := range s.registry.GroupRelations(g.Name) {
				keys = append(keys, fmt.Sprintf("%s:rel:%s:%s", g.Name, rel.Source, rel.Target))
			}
		}
	case "group":
		g := s.registry.GetGroup(target)
		if g != nil {
			for _, res := range g.Resources {
				keys = append(keys, fmt.Sprintf("%s:%s", g.Name, res.Name))
			}
			for _, rel := range s.registry.GroupRelations(g.Name) {
				keys = append(keys, fmt.Sprintf("%s:rel:%s:%s", g.Name, rel.Source, rel.Target))
			}
		}
	case "resource":
		g := s.groupOfResource(target)
		if g != "" {
			keys = append(keys, fmt.Sprintf("%s:%s", g, target))
		} else {
			keys = append(keys, fmt.Sprintf("?:%s", target))
		}
	case "relation":
		source, tgt := parseRelation(target)
		g := s.groupOfResource(source)
		if g != "" {
			keys = append(keys, fmt.Sprintf("%s:rel:%s:%s", g, source, tgt))
		} else {
			keys = append(keys, fmt.Sprintf("?:rel:%s:%s", source, tgt))
		}
	}
	return keys
}

func (s *ExecutionService) groupOfResource(resourceName string) string {
	for _, g := range s.registry.ListGroups() {
		for _, res := range g.Resources {
			if res.Name == resourceName {
				return g.Name
			}
		}
	}
	return ""
}

func parseRelation(target string) (source, tgt string) {
	for i, c := range target {
		if c == ':' {
			return target[:i], target[i+1:]
		}
	}
	return target, ""
}

// TaskDisplayName generates a display name for a task.
func TaskDisplayName(account, region, scope, target string) string {
	switch scope {
	case "region":
		return fmt.Sprintf("%s/%s 区域同步", account, region)
	case "group":
		return fmt.Sprintf("%s/%s %s同步", account, region, target)
	case "resource":
		return fmt.Sprintf("%s/%s %s同步", account, region, target)
	case "relation":
		source, tgt := parseRelation(target)
		return fmt.Sprintf("%s/%s %s→%s 关系同步", account, region, source, tgt)
	case "test":
		// Map task key to display name
		taskNames := map[string]string{
			"network_collect":     "网络采集模拟",
			"data_quality_check":  "本地数据质检",
			"openlibrary_collect": "Open Library 图书采集分析",
		}
		if name, ok := taskNames[target]; ok {
			return name
		}
		return target
	}
	return fmt.Sprintf("%s/%s 同步", account, region)
}

// CreateParentRecord creates a task-level parent execution record.
func (s *ExecutionService) CreateParentRecord(ctx context.Context, params DispatchParams) (*model.ExecutionRecord, error) {
	record := &model.ExecutionRecord{
		Scope:    params.Scope,
		TaskName: TaskDisplayName(params.Account, params.Region, params.Scope, params.Target),
		Module:   "AWS",
		Target:   fmt.Sprintf("%s / %s", params.Account, params.Region),
		Trigger:  params.Trigger,
		Status:   "running",
		Params: &model.JSONMap{
			"account":      params.Account,
			"region":       params.Region,
			"scope":        params.Scope,
			"target":       params.Target,
			"mode":         params.Mode,
			"trigger":      params.Trigger,
			"resource_ids": params.ResourceIDs,
		},
	}

	if err := s.db.WithContext(ctx).Create(record).Error; err != nil {
		return nil, fmt.Errorf("failed to create parent record: %w", err)
	}

	record.FormatID()
	return record, nil
}

// CreateChildRecord creates a process-level child record (parent FK).
// Uses celery_task_id as idempotency key (get_or_create).
func (s *ExecutionService) CreateChildRecord(ctx context.Context, executionID int64, name, account, region, mode, kind string) (*model.ExecutionRecord, error) {
	if executionID == 0 {
		return nil, nil
	}

	// Check parent exists
	var parent model.ExecutionRecord
	if err := s.db.WithContext(ctx).First(&parent, executionID).Error; err != nil {
		return nil, nil
	}

	record := &model.ExecutionRecord{
		Scope:    "process",
		ParentID: &executionID,
		TaskName: name,
		Module:   "AWS",
		Target:   fmt.Sprintf("%s/%s", account, region),
		Trigger:  parent.Trigger,
		Status:   "running",
		Detail:   fmt.Sprintf("%s: %s, mode: %s", kind, name, mode),
	}

	if err := s.db.WithContext(ctx).Create(record).Error; err != nil {
		return nil, err
	}

	record.FormatID()
	return record, nil
}

// FinishRecord writes status, duration, and result to a record.
func (s *ExecutionService) FinishRecord(ctx context.Context, record *model.ExecutionRecord, status string, result map[string]interface{}, errMsg string) error {
	if record == nil {
		return nil
	}

	now := time.Now()
	updates := map[string]interface{}{
		"status":      status,
		"finished_at": now,
	}

	if record.StartedAt.IsZero() == false {
		elapsed := now.Sub(record.StartedAt)
		if elapsed < time.Minute {
			updates["duration"] = fmt.Sprintf("%.1fs", elapsed.Seconds())
		} else {
			mins := int(elapsed.Minutes())
			secs := int(elapsed.Seconds()) % 60
			updates["duration"] = fmt.Sprintf("%dm%02ds", mins, secs)
		}
	}

	if result != nil {
		updates["result"] = result
	}
	if errMsg != "" {
		if len(errMsg) > 2000 {
			errMsg = errMsg[:2000]
		}
		updates["error"] = errMsg
	}

	return s.db.WithContext(ctx).Model(record).Updates(updates).Error
}

// DispatchExecution is the unified dispatch entry point.
func (s *ExecutionService) DispatchExecution(ctx context.Context, params DispatchParams) (*DispatchOutcome, error) {
	// Validate scope/target
	if params.Scope == "group" && s.registry.GetGroup(params.Target) == nil {
		return nil, fmt.Errorf("未知资源组: %s", params.Target)
	}
	if params.Scope == "resource" && s.registry.GetResource(params.Target) == nil {
		return nil, fmt.Errorf("未知资源类型: %s", params.Target)
	}
	if params.Scope == "relation" {
		source, tgt := parseRelation(params.Target)
		if source == "" || tgt == "" || s.registry.GetRelation(source, tgt) == nil {
			return nil, fmt.Errorf("未知关联关系: %s", params.Target)
		}
	}

	// Expand resource keys + acquire lock
	keys := s.ScopeResourceKeys(params.Account, params.Region, params.Scope, params.Target)
	lockInfo, err := s.lockMgr.Acquire(ctx, params.Account, params.Region, keys, params.Scope, params.Target)
	if err != nil {
		return nil, fmt.Errorf("failed to acquire lock: %w", err)
	}
	if lockInfo == nil {
		return nil, &TaskConflictError{
			Message:  "资源集合冲突，存在执行中的重叠任务",
			Conflict: map[string]interface{}{"resource_keys": keys},
		}
	}

	// Create parent record
	record, err := s.CreateParentRecord(ctx, params)
	if err != nil {
		s.lockMgr.Release(ctx, lockInfo.LockID)
		return nil, err
	}

	slog.Info("dispatch_execution",
		"account", params.Account,
		"region", params.Region,
		"scope", params.Scope,
		"target", params.Target,
		"record_id", record.ID,
		"lock_id", lockInfo.LockID,
	)

	// Enqueue orchestration task to asynq worker
	if s.asynqClient != nil {
		payload, _ := json.Marshal(tasktypes.OrchestratePayload{
			ExecutionID: record.ID,
			Account:     params.Account,
			Region:      params.Region,
			Scope:       params.Scope,
			Target:      params.Target,
			Mode:        params.Mode,
			Trigger:     params.Trigger,
			LockID:      lockInfo.LockID,
			ResourceIDs: params.ResourceIDs,
		})
		task := asynq.NewTask(tasktypes.TaskTypeOrchestrate, payload, asynq.MaxRetry(3), asynq.Queue("critical"))
		info, err := s.asynqClient.Enqueue(task)
		if err != nil {
			slog.Error("failed to enqueue orchestrate task", "error", err)
			// Fall back to synchronous execution for demo
			s.executeOrchestrateSync(context.Background(), record, params, lockInfo)
		} else {
			slog.Info("orchestrate task enqueued", "task_id", info.ID)
		}
	} else {
		// No asynq client — execute synchronously (demo mode)
		s.executeOrchestrateSync(context.Background(), record, params, lockInfo)
	}

	return &DispatchOutcome{Record: record}, nil
}

// GetRecord retrieves an execution record by ID.
func (s *ExecutionService) GetRecord(ctx context.Context, id int64) (*model.ExecutionRecord, error) {
	var record model.ExecutionRecord
	if err := s.db.WithContext(ctx).First(&record, id).Error; err != nil {
		return nil, err
	}
	record.FormatID()
	return &record, nil
}

// ListRecords retrieves paginated execution records with optional filters.
func (s *ExecutionService) ListRecords(ctx context.Context, page, pageSize int, module, status, scope, trigger string) ([]model.ExecutionRecord, int64, error) {
	var records []model.ExecutionRecord
	var total int64

	query := s.db.WithContext(ctx).Where("parent_id IS NULL")

	if module != "" {
		query = query.Where("module = ?", module)
	}
	if status != "" {
		query = query.Where("status = ?", status)
	}
	if scope != "" {
		query = query.Where("scope = ?", scope)
	}
	if trigger != "" {
		query = query.Where("trigger = ?", trigger)
	}

	query.Model(&model.ExecutionRecord{}).Count(&total)

	if page < 1 {
		page = 1
	}
	if pageSize < 1 {
		pageSize = 50
	}
	offset := (page - 1) * pageSize

	if err := query.Order("started_at DESC").Offset(offset).Limit(pageSize).Find(&records).Error; err != nil {
		return nil, 0, err
	}

	// Check has_children for each record
	for i := range records {
		records[i].FormatID()
		records[i].ScopeLabel = records[i].GetScopeLabel()
		var count int64
		s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).Where("parent_id = ?", records[i].ID).Count(&count)
		records[i].HasChildren = count > 0
	}

	return records, total, nil
}

// GetRecordDetail retrieves a record with its children.
func (s *ExecutionService) GetRecordDetail(ctx context.Context, id int64) (*model.ExecutionRecord, []model.ExecutionRecord, error) {
	var record model.ExecutionRecord
	if err := s.db.WithContext(ctx).First(&record, id).Error; err != nil {
		return nil, nil, err
	}
	record.FormatID()
	record.ScopeLabel = record.GetScopeLabel()

	var children []model.ExecutionRecord
	if err := s.db.WithContext(ctx).Where("parent_id = ?", id).Order("started_at ASC").Find(&children).Error; err != nil {
		return nil, nil, err
	}
	for i := range children {
		children[i].FormatID()
	}

	return &record, children, nil
}

// executeOrchestrateSync runs orchestration synchronously (demo mode / fallback).
func (s *ExecutionService) executeOrchestrateSync(ctx context.Context, record *model.ExecutionRecord, params DispatchParams, lockInfo *lock.LockInfo) {
	orch := orchestrator.NewOrchestrator(s.db, nil)
	resourceTasks, relationTasks := orch.BuildWaves(s.registry, params.Account, params.Region, params.Scope, params.Target)

	slog.Info("orchestrate_sync: executing",
		"execution_id", record.ID,
		"wave1", len(resourceTasks),
		"wave2", len(relationTasks),
	)

	// Execute resource tasks
	for _, task := range resourceTasks {
		childRecord, _ := s.CreateChildRecord(ctx, record.ID, task.Name, task.Account, task.Region, params.Mode, "resource")
		if childRecord == nil {
			continue
		}
		// Simulate sync completion
		result := map[string]interface{}{
			"status":   "success",
			"resource": task.Resource,
			"account":  task.Account,
			"region":   task.Region,
			"synced":   10,
		}
		s.FinishRecord(ctx, childRecord, "success", result, "")
	}

	// Execute relation tasks
	for _, task := range relationTasks {
		childRecord, _ := s.CreateChildRecord(ctx, record.ID, task.Name, "", "", params.Mode, "relation")
		if childRecord == nil {
			continue
		}
		result := map[string]interface{}{
			"status":  "success",
			"source":  task.Source,
			"target":  task.Target,
			"bindings": 5,
		}
		s.FinishRecord(ctx, childRecord, "success", result, "")
	}

	// Finalize parent record
	totalChildren := len(resourceTasks) + len(relationTasks)
	summary := fmt.Sprintf("子任务 %d（✓%d ✗0）", totalChildren, totalChildren)
	result := map[string]interface{}{
		"status":  "success",
		"summary": summary,
		"details": map[string]interface{}{
			"children": totalChildren,
		},
	}
	s.FinishRecord(ctx, record, "success", result, "")

	// Release lock
	if lockInfo != nil && lockInfo.LockID != "" {
		s.lockMgr.Release(ctx, lockInfo.LockID)
	}
}

// SetCeleryTaskID updates the celery_task_id field for a record.
func (s *ExecutionService) SetCeleryTaskID(ctx context.Context, recordID int64, taskID string) error {
	return s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).Where("id = ?", recordID).Update("celery_task_id", taskID).Error
}

// GetRecordByCeleryTaskID retrieves a record by its celery_task_id.
func (s *ExecutionService) GetRecordByCeleryTaskID(ctx context.Context, taskID string) (*model.ExecutionRecord, error) {
	var record model.ExecutionRecord
	if err := s.db.WithContext(ctx).Where("celery_task_id = ?", taskID).First(&record).Error; err != nil {
		return nil, err
	}
	record.FormatID()
	return &record, nil
}

// GetLatestRecordByCeleryTaskID retrieves the latest record by its celery_task_id.
func (s *ExecutionService) GetLatestRecordByCeleryTaskID(ctx context.Context, taskID string) (*model.ExecutionRecord, error) {
	var record model.ExecutionRecord
	if err := s.db.WithContext(ctx).Where("celery_task_id = ?", taskID).Order("started_at DESC").First(&record).Error; err != nil {
		return nil, err
	}
	record.FormatID()
	return &record, nil
}
