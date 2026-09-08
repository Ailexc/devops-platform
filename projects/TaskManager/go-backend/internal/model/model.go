package model

import (
	"database/sql"
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"

	"gorm.io/gorm"
)

// ExecutionRecord maps to the execution_records table.
// Two-level entity model (parent + child in same table):
//   - ParentID == nil → task-level record (region/group/resource/relation)
//   - ParentID != nil → process-level child record
type ExecutionRecord struct {
	ID              int64          `gorm:"primaryKey;autoIncrement" json:"-"`
	RecordID        string         `gorm:"-" json:"id"` // formatted as "#00001"
	Scope           string         `gorm:"column:scope;size:20;default:region" json:"scope"`
	ParentID        *int64         `gorm:"column:parent_id" json:"-"`
	Parent          *ExecutionRecord `gorm:"foreignKey:ParentID" json:"-"`
	TaskName        string         `gorm:"column:task_name;size:200" json:"task"`
	Module          string         `gorm:"column:module;size:50" json:"module"`
	Target          string         `gorm:"column:target;size:300" json:"target"`
	Trigger         string         `gorm:"column:trigger;size:50" json:"trigger"`
	Status          string         `gorm:"column:status;size:20;default:pending" json:"status"`
	CeleryTaskID    string         `gorm:"column:celery_task_id;size:200;index" json:"celery_task_id"`
	Error           string         `gorm:"column:error;type:text" json:"error"`
	Detail          string         `gorm:"column:detail;type:text" json:"detail"`
	Duration        string         `gorm:"column:duration;size:30" json:"duration"`
	Result          *JSONMap       `gorm:"column:result;type:jsonb" json:"result,omitempty"`
	LifecycleEvents JSONArray     `gorm:"column:lifecycle_events;type:jsonb;default:'[]'" json:"lifecycle_events,omitempty"`
	Params          *JSONMap       `gorm:"column:params;type:jsonb" json:"params,omitempty"`
	StartedAt       time.Time      `gorm:"column:started_at;autoCreateTime" json:"started_at"`
	FinishedAt      *time.Time     `gorm:"column:finished_at" json:"finished_at"`
	HasChildren     bool           `gorm:"-" json:"has_children,omitempty"`
	ScopeLabel      string         `gorm:"-" json:"scope_label,omitempty"`
}

func (ExecutionRecord) TableName() string {
	return "execution_records"
}

// BeforeCreate formats the RecordID for JSON output.
func (r *ExecutionRecord) BeforeCreate(tx *gorm.DB) error {
	return nil
}

// FormatID sets the formatted ID field.
func (r *ExecutionRecord) FormatID() {
	r.RecordID = fmt.Sprintf("#%05d", r.ID)
}

// GetScopeLabel returns the Chinese label for scope.
func (r *ExecutionRecord) GetScopeLabel() string {
	labels := map[string]string{
		"region":   "区域级",
		"group":    "资源组级",
		"resource": "资源级",
		"relation": "关系级",
		"test":     "测试",
		"process":  "进程级",
	}
	if l, ok := labels[r.Scope]; ok {
		return l
	}
	return r.Scope
}

// DailyTaskStat maps to the daily_task_stats table.
type DailyTaskStat struct {
	ID            int64     `gorm:"primaryKey;autoIncrement" json:"-"`
	StatDate      time.Time `gorm:"column:stat_date;type:date" json:"stat_date"`
	Module        string    `gorm:"column:module;size:50;default:AWS" json:"module"`
	Total         int       `gorm:"column:total;default:0" json:"total"`
	Success       int       `gorm:"column:success;default:0" json:"success"`
	Failed        int       `gorm:"column:failed;default:0" json:"failed"`
	TotalDuration float64   `gorm:"column:total_duration;default:0" json:"total_duration"`
	SyncedCount   int       `gorm:"column:synced_count;default:0" json:"synced_count"`
}

func (DailyTaskStat) TableName() string {
	return "daily_task_stats"
}

// AccountRegion maps to the account_regions table.
type AccountRegion struct {
	ID          int64  `gorm:"primaryKey;autoIncrement" json:"-"`
	Account     string `gorm:"column:account;size:100" json:"account"`
	AccountID   string `gorm:"column:account_id;size:50" json:"account_id"`
	Region      string `gorm:"column:region;size:50" json:"region"`
	Endpoint    string `gorm:"column:endpoint;size:300" json:"endpoint"`
	Cron        string `gorm:"column:cron;size:50;default:0 2 * * *" json:"cron"`
	Concurrency int    `gorm:"column:concurrency;default:50" json:"concurrency"`
	Source      string `gorm:"column:source;size:20;default:seed" json:"source"`
	Enabled     bool   `gorm:"column:enabled;default:true" json:"enabled"`
}

func (AccountRegion) TableName() string {
	return "account_regions"
}

// PeriodicTask maps to the periodic_tasks table.
type PeriodicTask struct {
	ID            int64      `gorm:"primaryKey;autoIncrement" json:"-"`
	Name          string     `gorm:"column:name;size:200;uniqueIndex" json:"name"`
	Task          string     `gorm:"column:task;size:200" json:"task"`
	Enabled       bool       `gorm:"column:enabled;default:false" json:"enabled"`
	Crontab       string     `gorm:"column:crontab;size:100" json:"crontab"`
	Args          string     `gorm:"column:args;type:text" json:"args"`
	Kwargs        string     `gorm:"column:kwargs;type:text" json:"kwargs"`
	LastRunAt     *time.Time `gorm:"column:last_run_at" json:"last_run_at"`
	TotalRunCount int        `gorm:"column:total_run_count;default:0" json:"total_run_count"`
}

func (PeriodicTask) TableName() string {
	return "periodic_tasks"
}

// JSONMap is a helper type for JSONB columns stored as map[string]interface{}.
type JSONMap map[string]interface{}

// JSONArray is a helper type for JSONB columns stored as []interface{}.
type JSONArray []interface{}

// Scan implements the sql.Scanner interface for JSONMap.
func (j *JSONMap) Scan(value interface{}) error {
	if value == nil {
		*j = make(JSONMap)
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return nil
	}
	return json.Unmarshal(bytes, j)
}

// Value implements the driver.Valuer interface for JSONMap.
func (j JSONMap) Value() (driver.Value, error) {
	if j == nil {
		return "{}", nil
	}
	bytes, err := json.Marshal(j)
	return string(bytes), err
}

// Scan implements the sql.Scanner interface for JSONArray.
func (j *JSONArray) Scan(value interface{}) error {
	if value == nil {
		*j = make(JSONArray, 0)
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return nil
	}
	return json.Unmarshal(bytes, j)
}

// Value implements the driver.Valuer interface for JSONArray.
func (j JSONArray) Value() (driver.Value, error) {
	if j == nil {
		return "[]", nil
	}
	bytes, err := json.Marshal(j)
	return string(bytes), err
}

// NullTime is an alias for sql.NullTime to handle nullable time fields.
type NullTime = sql.NullTime
