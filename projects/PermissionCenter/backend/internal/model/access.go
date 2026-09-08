package model

// Action 权限点：规范化权限标识 {app}:{resource}:{operation}，如 cmdb:host:create
// IsGeneric: 通用接口路由（如 /api/v1/{model}），PEP 请求时解析资源槽位 → 真实权限点
// ResourceSlot: 资源槽位名（如 model）；"header" 表示经 X-Resource-Type 请求头解析（统一查询入口）
type Action struct {
	Base
	AppID        uint64 `gorm:"index;not null" json:"app_id"`
	Code         string `gorm:"size:128;uniqueIndex:idx_app_code,priority:1;not null" json:"code"`
	Name         string `gorm:"size:128" json:"name"`
	Resource     string `gorm:"size:128" json:"resource"`
	Operation    string `gorm:"size:32" json:"operation"`
	Method       string `gorm:"size:16" json:"method"`
	Path         string `gorm:"size:256" json:"path"`
	IsGeneric    bool   `gorm:"default:false" json:"is_generic"`
	ResourceSlot string `gorm:"size:64" json:"resource_slot"`
	// v12 前端改造：接口树展示 请求/响应示例（D5：后端补字段）
	ReqExample  string `gorm:"type:text" json:"req_example,omitempty"`
	RespExample string `gorm:"type:text" json:"resp_example,omitempty"`
}

// PermissionTemplate 权限板块（如"主机管理"）
type PermissionTemplate struct {
	Base
	AppID uint64 `gorm:"index;not null" json:"app_id"`
	Name  string `gorm:"size:128;not null" json:"name"`
	Sort  int    `json:"sort"`
}

// TemplateAction 板块 → 权限点
type TemplateAction struct {
	TemplateID uint64 `gorm:"primaryKey" json:"template_id"`
	ActionID   uint64 `gorm:"primaryKey" json:"action_id"`
}

// GroupPermission 组 → 权限点（组即角色：自建组 = 人的集合 + 权限集合）
// RequestID: 关联授权申请单（组长申请组权限同样走审批单，留痕）
type GroupPermission struct {
	GroupID   uint64  `gorm:"primaryKey" json:"group_id"`
	ActionID  uint64  `gorm:"primaryKey" json:"action_id"`
	RequestID *uint64 `gorm:"index" json:"request_id"`
}
