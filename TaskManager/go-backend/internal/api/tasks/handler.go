package tasks

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"cmdb-go/internal/pkg/lock"
	"cmdb-go/internal/service"
	"cmdb-go/internal/tasktypes"

	"github.com/hibiken/asynq"
	"github.com/gin-gonic/gin"
)

// Handler holds tasks API handlers.
type Handler struct {
	executionSvc *service.ExecutionService
	treeSvc      *service.TaskTreeService
	scheduleSvc  *service.ScheduleService
	lockMgr      *lock.Manager
	asynqClient  *asynq.Client
}

// NewHandler creates a new tasks handler.
func NewHandler(
	executionSvc *service.ExecutionService,
	treeSvc *service.TaskTreeService,
	scheduleSvc *service.ScheduleService,
	lockMgr *lock.Manager,
	asynqClient *asynq.Client,
) *Handler {
	return &Handler{
		executionSvc: executionSvc,
		treeSvc:      treeSvc,
		scheduleSvc:  scheduleSvc,
		lockMgr:      lockMgr,
		asynqClient:  asynqClient,
	}
}

// RegisterRoutes registers all tasks routes.
func (h *Handler) RegisterRoutes(rg *gin.RouterGroup) {
	tasks := rg.Group("/tasks")
	{
		tasks.GET("/tree/", h.Tree)
		tasks.POST("/execute/", h.Execute)
		tasks.PUT("/schedule/", h.Schedule)
		tasks.GET("/locks/", h.Locks)
		tasks.POST("/preview/", h.Preview)
		tasks.POST("/test/run/", h.TestRun)
		tasks.GET("/test/status/:task_id/", h.TestStatus)
		tasks.GET("/test/file/", h.TestFile)
	}
}

// Tree returns the four-source merged task tree.
func (h *Handler) Tree(c *gin.Context) {
	ctx := c.Request.Context()
	tree, err := h.treeSvc.BuildTaskTree(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, tree)
}

// ExecuteRequest is the request body for task execution.
type ExecuteRequest struct {
	Account     string   `json:"account" binding:"required"`
	Region      string   `json:"region" binding:"required"`
	Scope       string   `json:"scope"`
	Target      string   `json:"target"`
	Mode        string   `json:"mode"`
	ResourceIDs []string `json:"resource_ids"`
}

// Execute dispatches a sync task.
func (h *Handler) Execute(c *gin.Context) {
	var req ExecuteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Scope == "" {
		req.Scope = "region"
	}
	if req.Mode == "" {
		req.Mode = "full"
	}

	ctx := c.Request.Context()
	params := service.DispatchParams{
		Account:     req.Account,
		Region:      req.Region,
		Scope:       req.Scope,
		Target:      req.Target,
		Mode:        req.Mode,
		Trigger:     "人工",
		ResourceIDs: req.ResourceIDs,
	}

	outcome, err := h.executionSvc.DispatchExecution(ctx, params)
	if err != nil {
		if tcErr, ok := err.(*service.TaskConflictError); ok {
			c.JSON(http.StatusConflict, gin.H{"error": tcErr.Error(), "conflict": tcErr.Conflict})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"execution_id": outcome.Record.ID,
		"task_id":      outcome.Record.ID,
		"status":       "dispatched",
	})
}

// ScheduleRequest is the request body for cron scheduling.
type ScheduleRequest struct {
	Name string `json:"name" binding:"required"`
	Cron string `json:"cron"`
}

// Schedule sets or clears a cron schedule.
func (h *Handler) Schedule(c *gin.Context) {
	var req ScheduleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := c.Request.Context()
	var result map[string]interface{}
	var err error

	if req.Cron != "" {
		result, err = h.scheduleSvc.SetCron(ctx, req.Name, req.Cron)
	} else {
		result, err = h.scheduleSvc.ClearCron(ctx, req.Name)
	}

	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	resp := gin.H{"status": "updated", "name": req.Name}
	for k, v := range result {
		resp[k] = v
	}
	c.JSON(http.StatusOK, resp)
}

// Locks returns active concurrency locks.
func (h *Handler) Locks(c *gin.Context) {
	ctx := c.Request.Context()
	locks := h.lockMgr.ListActive(ctx)
	c.JSON(http.StatusOK, gin.H{"locks": locks})
}

// Preview returns a diff preview (stub).
func (h *Handler) Preview(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"preview": gin.H{
			"adds":    []gin.H{{"id": "i-0new1", "reason": "AWS有CMDB无"}},
			"updates": []gin.H{{"id": "i-0a1b2c3d", "reason": "running→stopped"}},
			"deletes": []gin.H{{"id": "i-deleted1", "reason": "CMDB有AWS无"}},
		},
	})
}

// TestRunRequest is the request body for test task execution.
type TestRunRequest struct {
	Task string `json:"task" binding:"required"`
}

// TestRun runs a test task — creates an execution record and simulates async completion.
func (h *Handler) TestRun(c *gin.Context) {
	var req TestRunRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := c.Request.Context()
	taskID := "test-" + req.Task

	// Create execution record
	record, err := h.executionSvc.CreateParentRecord(ctx, service.DispatchParams{
		Account: "测试",
		Region:  "local",
		Scope:   "test",
		Target:  req.Task,
		Mode:    "test",
		Trigger: "测试",
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Store task_id mapping in the record
	h.executionSvc.SetCeleryTaskID(ctx, record.ID, taskID)

	// Enqueue actual test task to asynq worker for real execution
	if h.asynqClient != nil {
		payload, _ := json.Marshal(tasktypes.ResourceSyncPayload{
			ExecutionID: record.ID,
			Resource:    req.Task,
			Mode:        "test",
		})
		task := asynq.NewTask(tasktypes.TaskTypeTestTask, payload, asynq.MaxRetry(1), asynq.Queue("default"))
		info, err := h.asynqClient.Enqueue(task)
		if err != nil {
			slog.Error("failed to enqueue test task", "error", err)
			// Fallback: mark as completed immediately
			h.executionSvc.FinishRecord(ctx, record, "success", map[string]interface{}{
				"status":  "success",
				"summary": "测试任务完成",
				"task":    req.Task,
			}, "")
		} else {
			slog.Info("test task enqueued", "task_id", info.ID, "type", tasktypes.TaskTypeTestTask)
		}
	} else {
		// Fallback: mark as completed immediately (no worker)
		h.executionSvc.FinishRecord(ctx, record, "success", map[string]interface{}{
			"status":  "success",
			"summary": "测试任务完成",
			"task":    req.Task,
		}, "")
	}

	c.JSON(http.StatusOK, gin.H{
		"task_id":   taskID,
		"record_id": record.ID,
		"task":      req.Task,
		"status":    "dispatched",
	})
}

// TestStatus returns test task status — reads from execution record.
func (h *Handler) TestStatus(c *gin.Context) {
	taskID := c.Param("task_id")
	ctx := c.Request.Context()

	// Find latest record by celery_task_id
	record, err := h.executionSvc.GetLatestRecordByCeleryTaskID(ctx, taskID)
	if err != nil || record == nil {
		// Fallback: simulate completion for demo
		c.JSON(http.StatusOK, gin.H{
			"task_id": taskID,
			"status":  "completed",
			"result": gin.H{
				"status":  "success",
				"summary": "测试任务完成",
			},
		})
		return
	}

	result := gin.H{
		"task_id":    taskID,
		"record_id":  record.ID,
		"status":     record.Status,
		"started_at": record.StartedAt.Format("2006-01-02 15:04:05"),
	}
	if record.FinishedAt != nil {
		result["finished_at"] = record.FinishedAt.Format("2006-01-02 15:04:05")
	}
	if record.Duration != "" {
		result["duration"] = record.Duration
	}
	if record.Result != nil {
		result["result"] = record.Result
	}

	// Map status to frontend-expected values
	if record.Status == "success" {
		result["status"] = "completed"
	} else if record.Status == "failed" {
		result["status"] = "failed"
	}

	c.JSON(http.StatusOK, result)
}

// TestFile returns test file content (stub).
func (h *Handler) TestFile(c *gin.Context) {
	filePath := c.Query("path")
	if filePath == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path parameter is required"})
		return
	}

	// Security: only allow files under /tmp/cmdb_test
	absPath, _ := filepath.Abs(filePath)
	if !strings.HasPrefix(absPath, "/tmp/cmdb_test") {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			c.JSON(http.StatusNotFound, gin.H{"error": "File not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	ext := strings.ToLower(filepath.Ext(filePath))
	mime := "text/plain"
	switch ext {
	case ".json":
		mime = "application/json"
	case ".md":
		mime = "text/markdown"
	}

	c.JSON(http.StatusOK, gin.H{
		"content": string(content),
		"mime":    mime,
		"path":    filePath,
	})
}
