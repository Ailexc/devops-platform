package model

import "time"

// 申请主体类型（FR-3 扩展：我 / 组织 / 自建组 / 下游应用）
const (
	ReqSubjectUser  = 1 // 我自己
	ReqSubjectGroup = 2 // 组织 / 自建组
	ReqSubjectOrg   = 3 // 组织
	ReqSubjectApp   = 4 // 下游应用（M2M）
)

// 申请单方向（授权即审批：任何授权变更都必须走申请单，无直授后门）
const (
	RequestApply = 1 // 自助申请（申请人为自己/组织/组/应用申请权限）
	RequestGrant = 2 // owner 授权（授权方主动授予，被授权方确认 + 其他 owner 复核）
	RequestOnboard = 3 // 接入申请（D4 定案：前置鉴权 + 网络开通，Phase 6.5）
	RequestRevoke  = 4 // 退还申请（用户主动退还已授权的能力包预设）（D4 定案：前置鉴权 + 网络开通，Phase 6.5）
)

// AccessRequest 权限申请（自助 / 业务系统对接）
// content: 角色/权限点/数据范围；risk_level: 1低 2中 3高
// status: 0草稿 1审批中 2通过 3拒绝 4已回收；expires_at 可空=JIT
// items: 申请项 [{capability_id, action_ids, data_scope, ttl}]
// prereq_actions: 联动申请的接口权限点（智能表单预检联动）
type AccessRequest struct {
	Base
	ApplicantID         uint64     `gorm:"index;not null" json:"applicant_id"`
	RequestType          int16      `gorm:"not null;default:1" json:"request_type"`             // 1=自助申请 2=owner 授权
	ApplicantSubjectType int16      `gorm:"not null;default:1" json:"applicant_subject_type"`   // 1=我 2=组 3=组织 4=下游应用
	ApplicantSubjectID   uint64     `gorm:"index" json:"applicant_subject_id"`                  // 申请/被授权主体 ID
	// v12 双主体（权限作用主体 grantee / 权限申请主体 applicant）：字段与 ApplicantSubject* 对齐，字符串化便于前端/表达式
	GranteeType      string   `gorm:"size:16" json:"grantee_type"`   // user | org | group | app
	GranteeName      string   `gorm:"size:256" json:"grantee_name"`  // client:xxx / 用户名 / 组织路径 / 组名
	GranteeID        uint64   `json:"grantee_id"`                    // 作用主体 ID（程序=App.ID）
	ScopeSelections  JSONAny  `gorm:"type:jsonb" json:"scope_selections"` // v12：每模型 {model,type,selectedValue,selectedValues[]}，落库留痕
	AppID                uint64     `gorm:"index;not null" json:"app_id"`
	Content              JSONMap    `gorm:"type:jsonb;not null" json:"content"`
	Items                JSONMap    `gorm:"type:jsonb" json:"items"`
	PrereqActions        JSONArray  `gorm:"type:jsonb" json:"prereq_actions"`
	Reason               string     `gorm:"size:512" json:"reason"` // 授权理由/申请说明（"为什么给我授权"）
	RiskLevel            int16      `gorm:"not null;default:1" json:"risk_level"`
	Status               int16      `gorm:"not null;default:1;index" json:"status"`
	ExpiresAt            *time.Time `json:"expires_at"`
}

// ApprovalTask 多级审批节点
type ApprovalTask struct {
	Base
	RequestID  uint64 `gorm:"index;not null" json:"request_id"`
	Step       int    `json:"step"`
	ApproverID uint64 `json:"approver_id"`
	Action     int16  `json:"action"` // 1=通过 2=驳回
	Comment    string `gorm:"size:512" json:"comment"`
}

// 回收申请状态
const (
	RevokePending  = 1 // 待审批
	RevokeApproved = 2 // 已通过（已执行回收）
	RevokeRejected = 3 // 已驳回
)

// RevokeRequest 授权回收申请（阶段 6：回收走审批，新增状态机）
// 流程：owner/管理员发起 → 应用其他 owner 审批 → 通过后停用策略 + 撤销 OpenFGA 关系
type RevokeRequest struct {
	Base
	PolicyID    uint64     `gorm:"index;not null" json:"policy_id"`
	AppID       uint64     `gorm:"index;not null" json:"app_id"`
	RequesterID uint64     `gorm:"index;not null" json:"requester_id"`
	Reason      string     `gorm:"size:512" json:"reason"`
	Status      int16      `gorm:"not null;default:1;index" json:"status"`
	ApproverID  uint64     `json:"approver_id"`
	Comment     string     `gorm:"size:512" json:"comment"`
	ApprovedAt  *time.Time `json:"approved_at"`
}

// CapabilityPublishTask 预设级上架/下架审批任务（Phase 6：审批 → 工单 → 生效，留痕）
// status: 1=已发起 2=已完成；demo 模拟审批链通过后直接 done
type CapabilityPublishTask struct {
	Base
	CapabilityID uint64   `gorm:"index;not null" json:"capability_id"`
	Action       string   `gorm:"size:16" json:"action"` // publish | offline
	PresetIDs    JSONAny  `gorm:"type:jsonb" json:"preset_ids"`
	All          bool     `json:"all"`
	RequesterID  uint64   `json:"requester_id"`
	TicketNo     string   `gorm:"size:64" json:"ticket_no"` // 模拟工单号（真实对接工单系统 webhook）
	Status       int16    `gorm:"not null;default:1" json:"status"`
	DoneAt       *time.Time `json:"done_at"`
}
