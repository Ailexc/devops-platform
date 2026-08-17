package model

import "time"

// Policy 统一策略表（API + 数据）
// effect: 1=allow 2=deny；subject_type: 1=user 2=group 3=service（原 role 已删除，组即角色）
// action_ids: 权限点 ID 数组（[]=全部）；resource_scope: 数据策略范围；conditions: ABAC 条件
// force_remote: 风险分级——强制回源中心（不进入本地 bundle）
type Policy struct {
	Base
	Name          string         `gorm:"size:128;not null" json:"name"`
	Version       int            `gorm:"not null;default:1" json:"version"`
	Effect        int16          `gorm:"not null" json:"effect"`
	SubjectType   int16          `gorm:"not null;index" json:"subject_type"`
	SubjectID     uint64         `gorm:"not null;index" json:"subject_id"`
	AppID         uint64         `gorm:"index;not null" json:"app_id"`
	ActionIDs     JSONArray      `gorm:"type:jsonb;not null" json:"action_ids"`
	ResourceScope JSONMap        `gorm:"type:jsonb" json:"resource_scope"`
	Conditions    JSONMap        `gorm:"type:jsonb;default:'{}'" json:"conditions"`
	ForceRemote   bool           `gorm:"default:false" json:"force_remote"`
	Status        int16          `gorm:"not null;default:1" json:"status"`
	CreatedBy     uint64         `json:"created_by"`
	Source        int16          `gorm:"not null;default:1" json:"source"` // 来源：1=owner_grant 2=via_request 3=app_request
	RequestID     *uint64        `gorm:"index" json:"request_id"`          // 关联申请单 ID
	CapabilityID  *uint64        `gorm:"index" json:"capability_id"`       // 关联能力声明（能力维度反查）
	DataScopeType string         `gorm:"size:16" json:"data_scope_type"`   // all/owner/dimension/instance/n-a
	ExpiresAt     *time.Time     `json:"expires_at"`                       // 策略级 TTL（临时授权承载）
}

// PolicyVersion 策略历史（支持回滚与审计）
type PolicyVersion struct {
	Base
	PolicyID  uint64  `gorm:"index;not null" json:"policy_id"`
	Version   int     `json:"version"`
	Content   JSONMap `gorm:"type:jsonb" json:"content"`
	ChangedBy uint64  `json:"changed_by"`
	Reason    string  `gorm:"size:512" json:"reason"`
}
