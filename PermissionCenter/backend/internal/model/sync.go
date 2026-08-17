package model

import "time"

// SyncJob 同步任务记录
// type: 1=openapi 2=cmdb-model 3=cmdb-instance 4=identity
type SyncJob struct {
	Base
	Type       int16      `gorm:"index;not null" json:"type"`
	Status     int16      `json:"status"` // 0=失败 1=运行中 2=成功
	StartedAt  *time.Time `json:"started_at"`
	FinishedAt *time.Time `json:"finished_at"`
	Result     JSONMap    `gorm:"type:jsonb" json:"result"`
}

// Bundle 策略分发版本（全量策略快照 + 版本 + checksum）
type Bundle struct {
	Base
	AppID       uint64  `gorm:"uniqueIndex:idx_app_rev;not null" json:"app_id"`
	Revision    int64   `gorm:"uniqueIndex:idx_app_rev;not null" json:"revision"`
	Content     JSONMap `gorm:"type:jsonb;not null" json:"content"`
	Checksum    string  `gorm:"size:64" json:"checksum"`
	PublishedBy uint64  `json:"published_by"`
}

// AgentStatus agent 上报（升级率/存活监控）
type AgentStatus struct {
	Base
	AgentID        string     `gorm:"uniqueIndex;not null" json:"agent_id"`
	AppID          uint64     `json:"app_id"`
	CurrentRev     int64      `json:"current_rev"`
	LastSeenAt     *time.Time `json:"last_seen_at"`
	DecisionCount  int64      `json:"decision_count"`
	HitRate        float64    `json:"hit_rate"`
}
