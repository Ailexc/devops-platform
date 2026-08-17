package model

// AuditLog 管理操作审计（按月分区）
type AuditLog struct {
	Base
	ActorID      uint64  `gorm:"index" json:"actor_id"`
	Action       string  `gorm:"size:64;index" json:"action"`
	ResourceType string  `gorm:"size:64" json:"resource_type"`
	ResourceID   string  `gorm:"size:128" json:"resource_id"`
	Detail       JSONMap `gorm:"type:jsonb" json:"detail"`
	IP           string  `gorm:"size:64" json:"ip"`
}

// DecisionLog 鉴权决策日志（按月分区）
// TraceID: 一次请求的链路追踪 ID（网关 PEP → PDP → 数据级贯穿）
// PEP: 网关 PEP 解析信息（method/path/匹配方式 literal|template|header/解析出的资源/权限点）
type DecisionLog struct {
	Base
	TraceID   string  `gorm:"size:64;index" json:"trace_id"`
	UserID    uint64  `gorm:"index" json:"user_id"`
	AppID     uint64  `json:"app_id"`
	Action    string  `gorm:"size:128" json:"action"`
	Resource  string  `gorm:"size:128" json:"resource"`
	Decision  int16   `json:"decision"` // 1=allow 2=deny
	Reason    string  `gorm:"size:255" json:"reason"`
	Channel   int16   `json:"channel"` // 1=remote 2=local
	LatencyMS int64   `json:"latency_ms"`
	PEP       JSONMap `gorm:"type:jsonb" json:"pep"`
	Context   JSONMap `gorm:"type:jsonb" json:"context"`
}
