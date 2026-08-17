package dto

import (
	"time"

	"github.com/google/uuid"
)

type EventCreate struct {
	EventType   string                 `json:"event_type" binding:"required"`
	Source      string                 `json:"source"`
	DetailType  string                 `json:"detail_type"`
	ResourceID  string                 `json:"resource_id"`
	RawPayload  map[string]interface{} `json:"raw_payload"`
	MaxRetries  int                    `json:"max_retries"`
}

type EventOut struct {
	ID           uuid.UUID              `json:"id"`
	EventType    string                 `json:"event_type"`
	Source       string                 `json:"source"`
	DetailType   string                 `json:"detail_type"`
	ResourceID   string                 `json:"resource_id"`
	RawPayload   map[string]interface{} `json:"raw_payload"`
	Status       string                 `json:"status"`
	TraceID      uuid.UUID              `json:"trace_id"`
	RetryCount   int                    `json:"retry_count"`
	MaxRetries   int                    `json:"max_retries"`
	Handler      string                 `json:"handler"`
	WorkerID     string                 `json:"worker_id"`
	ErrorMessage string                 `json:"error_message"`
	ReceivedAt   time.Time              `json:"received_at"`
	ProcessedAt  *time.Time             `json:"processed_at"`
}

type EventListOut struct {
	Items    []EventOut `json:"items"`
	Total    int64      `json:"total"`
	Page     int        `json:"page"`
	PageSize int        `json:"page_size"`
}

type EventLogOut struct {
	ID        int64                  `json:"id"`
	Action    string                 `json:"action"`
	Detail    map[string]interface{} `json:"detail"`
	CreatedAt time.Time              `json:"created_at"`
}

type RetryRequest struct {
	Force bool `json:"force"`
}

type DlqReplayRequest struct {
	EventIDs []uuid.UUID `json:"event_ids"`
}

type BatchCreateRequest []EventCreate



type StatsOut struct {
	Total        int64            `json:"total"`
	ByStatus     map[string]int64 `json:"by_status"`
	SuccessRate  float64          `json:"success_rate"`
	AvgDuration  *float64         `json:"avg_duration"`
	P99Duration  *float64         `json:"p99_duration"`
	QueueDepth   int64            `json:"queue_depth"`
}

type QueueStat struct {
	Name   string `json:"name"`
	Label  string `json:"label"`
	Depth  int64  `json:"depth"`
}

type WorkerInfo struct {
	ID          string `json:"id"`
	Status      string `json:"status"`
	Hostname    string `json:"hostname"`
	ActiveTasks int    `json:"active_tasks"`
	Pool        string `json:"pool"`
	Concurrency int    `json:"concurrency"`
}

type WorkerStatsOut struct {
	Total       int          `json:"total"`
	Online      int          `json:"online"`
	ActiveTasks int          `json:"active_tasks"`
	QueuedTasks int64        `json:"queued_tasks"`
	Workers     []WorkerInfo `json:"workers"`
}

type HourlyThroughputOut struct {
	Hour      string `json:"hour"`
	Total     int    `json:"total"`
	Completed int    `json:"completed"`
	Failed    int    `json:"failed"`
	Other     int    `json:"other"`
}

type RecentFailureOut struct {
	ID           string    `json:"id"`
	EventType    string    `json:"event_type"`
	Status       string    `json:"status"`
	ErrorMessage string    `json:"error_message"`
	RetryCount   int       `json:"retry_count"`
	MaxRetries   int       `json:"max_retries"`
	ReceivedAt   time.Time `json:"received_at"`
}

type HandlerConfigOut struct {
	ID               int64  `json:"id"`
	Name             string `json:"name"`
	EventTypePattern string `json:"event_type_pattern"`
	HandlerClass     string `json:"handler_class"`
	Timeout          int    `json:"timeout"`
	MaxRetries       int    `json:"max_retries"`
}

type EventTypeOut struct {
	Category    string                 `json:"category"`
	Icon        string                 `json:"icon"`
	Pattern     string                 `json:"pattern"`
	Description string                 `json:"description"`
	Handler     string                 `json:"handler"`
	Events      []map[string]interface{} `json:"events,omitempty"`
	Schema      map[string]interface{} `json:"schema,omitempty"`
	Example     interface{}            `json:"example,omitempty"`
}

type TriggerRequest struct {
	TaskID string `json:"task_id" binding:"required"`
	Count  int    `json:"count"`
}

type TriggerResponse struct {
	TaskID       string `json:"task_id"`
	AsynqTaskID  string `json:"celery_task_id"`
	Count        int    `json:"count"`
	BatchID      string `json:"batch_id"`
	Message      string `json:"message"`
}

type TaskStatusResponse struct {
	CeleryTaskID string                 `json:"celery_task_id"`
	State        string                 `json:"state"`
	Meta         map[string]interface{} `json:"meta,omitempty"`
	Result       map[string]interface{} `json:"result,omitempty"`
	EventIDs     []string               `json:"event_ids"`
}

type FilePreviewResponse struct {
	Filename string `json:"filename"`
	Size     int64  `json:"size"`
	Content  string `json:"content"`
}
