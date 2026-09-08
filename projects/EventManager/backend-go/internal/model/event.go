package model

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/datatypes"
)

// Event status constants — must match Python EventStatus.TextChoices exactly
const (
	StatusPending     = "pending"
	StatusProcessing  = "processing"
	StatusCompleted   = "completed"
	StatusFailed      = "failed"
	StatusDLQ         = "dlq"
)

// Event 核心事件模型
type Event struct {
	ID           uuid.UUID      `gorm:"type:uuid;primaryKey" json:"id"`
	EventType    string         `gorm:"size:128;index" json:"event_type"`
	Source       string         `gorm:"size:64;index" json:"source"`
	DetailType   string         `gorm:"size:64;default:''" json:"detail_type"`
	ResourceID   string         `gorm:"size:256;default:''" json:"resource_id"`
	RawPayload   datatypes.JSON `gorm:"type:jsonb;default:'{}'" json:"raw_payload"`
	Status       string         `gorm:"size:32;index;default:pending" json:"status"`
	TraceID      uuid.UUID      `gorm:"type:uuid;index" json:"trace_id"`
	RetryCount   int            `gorm:"default:0" json:"retry_count"`
	MaxRetries   int            `gorm:"default:5" json:"max_retries"`
	Handler      string         `gorm:"size:128;default:''" json:"handler"`
	WorkerID     string         `gorm:"size:64;default:''" json:"worker_id"`
	ErrorMessage string         `gorm:"type:text;default:''" json:"error_message"`
	ReceivedAt   time.Time      `gorm:"autoCreateTime;index" json:"received_at"`
	ProcessedAt  *time.Time     `json:"processed_at"`
	Logs         []EventLog     `gorm:"foreignKey:EventID" json:"-"`
}

func (Event) TableName() string {
	return "api_event"
}

// EventLog 事件处理日志
type EventLog struct {
	ID        int64          `gorm:"primaryKey;autoIncrement" json:"id"`
	EventID   uuid.UUID      `gorm:"type:uuid;index" json:"-"`
	Action    string         `gorm:"size:32" json:"action"`
	Detail    datatypes.JSON `gorm:"type:jsonb;default:'{}'" json:"detail"`
	CreatedAt time.Time      `gorm:"autoCreateTime" json:"created_at"`
}

func (EventLog) TableName() string {
	return "api_eventlog"
}

// EventHandlerConfig Handler 注册配置
type EventHandlerConfig struct {
	ID                int64      `gorm:"primaryKey;autoIncrement" json:"id"`
	Name              string     `gorm:"size:128;uniqueIndex" json:"name"`
	EventTypePattern  string     `gorm:"size:256" json:"event_type_pattern"`
	HandlerClass      string     `gorm:"size:256" json:"handler_class"`
	Timeout           int        `gorm:"default:60" json:"timeout"`
	MaxRetries        int        `gorm:"default:5" json:"max_retries"`
	IsActive          bool       `gorm:"default:true" json:"is_active"`
	Description       string     `gorm:"type:text;default:''" json:"description"`
	CreatedAt         time.Time  `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt         time.Time  `gorm:"autoUpdateTime" json:"updated_at"`
}

func (EventHandlerConfig) TableName() string {
	return "api_eventhandlerconfig"
}
