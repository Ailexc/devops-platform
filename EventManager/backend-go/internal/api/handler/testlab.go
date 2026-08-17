package handler

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/hibiken/asynq"
	"gorm.io/datatypes"
	"gorm.io/gorm"

	"event-flow/internal/model"
	"event-flow/internal/repository"
	"event-flow/internal/tasklab"
)

// TestLabHandler holds dependencies for the test-lab endpoints.
type TestLabHandler struct {
	Client      *asynq.Client
	Inspector   *asynq.Inspector
	EventRepo   *repository.EventRepo
	DB          *gorm.DB
	OutputDir   string
	StatusStore *tasklab.StatusStore
}

// NewTestLabHandler creates a new TestLabHandler.
func NewTestLabHandler(client *asynq.Client, inspector *asynq.Inspector, eventRepo *repository.EventRepo, db *gorm.DB, outputDir string, statusStore *tasklab.StatusStore) *TestLabHandler {
	return &TestLabHandler{
		Client:      client,
		Inspector:   inspector,
		EventRepo:   eventRepo,
		DB:          db,
		OutputDir:   outputDir,
		StatusStore: statusStore,
	}
}

// TaskDef defines a test-lab task template.
type TaskDef struct {
	ID             string `json:"id"`
	Name           string `json:"name"`
	Description    string `json:"description"`
	Duration       string `json:"duration"`
	MaxCount       int    `json:"max_count"`
	DefaultCount   int    `json:"default_count"`
}

// taskRegistry is the list of demo tasks (mirrors Python TASK_REGISTRY).
var taskRegistry = []TaskDef{
	{
		ID:           "fast",
		Name:         "⚡ 快任务 — API 数据爬取",
		Description:  "调用 JSONPlaceholder 公开 API 爬取帖子数据，提取关键字段并统计词频，结果写入 JSON 文件",
		Duration:     "~2-5 秒/批",
		MaxCount:     50,
		DefaultCount: 1,
	},
	{
		ID:           "slow",
		Name:         "🐢 慢任务 — 报告生成",
		Description:  "模拟数据分析流程：读取数据源 → 数据清洗 → 统计计算 → 生成报告，支持实时进度上报",
		Duration:     "~3-8 秒/条",
		MaxCount:     20,
		DefaultCount: 1,
	},
}

// ListTasks handles GET /api/v1/test-lab/tasks
func (h *TestLabHandler) ListTasks(c *gin.Context) {
	c.JSON(http.StatusOK, taskRegistry)
}

// TriggerRequest is the request body for triggering a task.
type TriggerRequest struct {
	TaskID string `json:"task_id" binding:"required"`
	Count  int    `json:"count"`
}

// TriggerTask handles POST /api/v1/test-lab/trigger
func (h *TestLabHandler) TriggerTask(c *gin.Context) {
	var req TriggerRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request", "detail": err.Error()})
		return
	}

	// Validate task_id
	found := false
	for _, t := range taskRegistry {
		if t.ID == req.TaskID {
			found = true
			if req.Count <= 0 {
				req.Count = t.DefaultCount
			}
			if req.Count > t.MaxCount {
				req.Count = t.MaxCount
			}
			break
		}
	}
	if !found {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": fmt.Sprintf("未知任务: %s，可用: fast, slow", req.TaskID),
		})
		return
	}

	batchID := uuid.New().String()
	celeryTaskIDs := make([]string, 0, req.Count)

	// Enqueue N asynq tasks on the "tasklab" queue
	for i := 0; i < req.Count; i++ {
		taskUUID := uuid.New().String()
		payload, _ := json.Marshal(map[string]interface{}{
			"task_id":       req.TaskID,
			"batch_id":      batchID,
			"index":         i,
			"asynq_task_id": taskUUID,
		})
		task := asynq.NewTask("demo_task", payload)
		info, err := h.Client.EnqueueContext(c.Request.Context(), task,
			asynq.Queue("tasklab"),
			asynq.MaxRetry(1),
			asynq.TaskID(taskUUID),
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "enqueue failed", "detail": err.Error()})
			return
		}
		celeryTaskIDs = append(celeryTaskIDs, info.ID)

		// Store initial PENDING state in Redis keyed by task ID
		if h.StatusStore != nil {
			_ = h.StatusStore.SetState(c.Request.Context(), info.ID, "PENDING", nil, nil)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"task_id":          req.TaskID,
		"celery_task_id":   celeryTaskIDs[0], // primary task ID for status tracking
		"celery_task_ids":  celeryTaskIDs,
		"count":            req.Count,
		"batch_id":         batchID,
		"message":          fmt.Sprintf("已触发 %d 个 %s 任务", req.Count, req.TaskID),
	})
}

// GetTaskStatus handles GET /api/v1/test-lab/status/:celery_task_id
func (h *TestLabHandler) GetTaskStatus(c *gin.Context) {
	taskID := c.Param("celery_task_id")

	// Check Redis first (worker stores progress/result here)
	if h.StatusStore != nil {
		progress, err := h.StatusStore.GetProgress(c.Request.Context(), taskID)
		if err == nil && progress != nil {
			state, _ := progress["state"].(string)
			if state == "" {
				state = "PROGRESS"
			}
			c.JSON(http.StatusOK, gin.H{
				"celery_task_id": taskID,
				"state":          state,
				"meta":           progress["meta"],
				"result":         progress["result"],
			})
			return
		}
	}

	// Fallback: check asynq queues
	if h.Inspector == nil {
		c.JSON(http.StatusOK, gin.H{"celery_task_id": taskID, "state": "UNKNOWN"})
		return
	}

	queues := []string{"tasklab", "default", "events"}
	var info *asynq.TaskInfo
	var err error
	for _, q := range queues {
		info, err = h.Inspector.GetTaskInfo(q, taskID)
		if err == nil {
			break
		}
	}
	if err != nil {
		c.JSON(http.StatusOK, gin.H{
			"celery_task_id": taskID,
			"state":          "UNKNOWN",
			"error":          "task not found",
		})
		return
	}

	state := info.State.String()
	c.JSON(http.StatusOK, gin.H{
		"celery_task_id": taskID,
		"state":          state,
		"queue":          info.Queue,
		"retry":          info.Retried,
		"max_retry":      info.MaxRetry,
	})
}

// PreviewFile handles GET /api/v1/test-lab/preview?filename=
func (h *TestLabHandler) PreviewFile(c *gin.Context) {
	filename := c.Query("filename")
	if filename == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "filename parameter required"})
		return
	}

	// Security: prevent path traversal
	if filepath.Base(filename) != filename || filepath.Dir(filename) != "." {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid filename"})
		return
	}

	filePath := filepath.Join(h.OutputDir, filename)
	f, err := os.Open(filePath)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "file not found"})
		return
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "stat file failed"})
		return
	}

	content, err := io.ReadAll(f)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "read file failed"})
		return
	}

	// Limit preview to 500KB
	contentStr := string(content)
	if len(content) > 500*1024 {
		contentStr = contentStr[:500*1024] + "\n... (文件过大，已截断)"
	}

	// Return in the format the frontend expects: {filename, size, content}
	c.JSON(http.StatusOK, gin.H{
		"filename": filename,
		"size":     info.Size(),
		"content":  contentStr,
	})
}

// Helper to create EventLog with JSON detail
func createEventLog(db *gorm.DB, eventID uuid.UUID, action string, detail map[string]interface{}) {
	b, _ := json.Marshal(detail)
	entry := model.EventLog{
		EventID:   eventID,
		Action:    action,
		Detail:    datatypes.JSON(b),
		CreatedAt: time.Now(),
	}
	_ = db.Create(&entry).Error
}
