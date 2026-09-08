// Package model 定义领域模型与枚举（GORM AutoMigrate 建表，零手写 SQL）
package model

import "time"

// 主键统一 BIGSERIAL；时间统一 TIMESTAMPTZ；软删除统一 deleted_at（可空）
type Base struct {
	ID        uint64     `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time  `json:"created_at"`
	UpdatedAt time.Time  `json:"updated_at"`
	DeletedAt *time.Time `gorm:"index" json:"deleted_at,omitempty"`
}

// 通用枚举
const (
	StatusDisabled = 0
	StatusEnabled  = 1
)

// 数据来源：1=外部源同步(只读) 2=手工(可编辑)
const (
	SourceSync  = 1
	SourceLocal = 2
)

// 主体类型（策略）
const (
	SubjectUser    = 1
	SubjectGroup   = 2
	SubjectService = 3 // 注意：原 SubjectRole=3 已删除，组即角色
)

// 策略效果
const (
	EffectAllow = 1
	EffectDeny  = 2
)

// 策略状态
const (
	PolicyDisabled = 0
	PolicyActive   = 1
)

// 策略来源（双向账本）
const (
	SourceOwnerGrant = 1 // 应用 owner 主动发布（预授权）
	SourceViaRequest = 2 // 用户/应用申请 → 审批生成
	SourceAppRequest = 3 // 应用间申请（service-to-service）
)

// 应用类型
const (
	AppTypeAPI  = 1
	AppTypeData = 2
)

// 组类型
const (
	GroupTypeOrg    = 1
	GroupTypeCustom = 2
)

// 组内角色
const (
	GroupRoleMember = 1
	GroupRoleAdmin  = 2
)

// 风险等级（申请/审批）
const (
	RiskLow    = 1
	RiskMedium = 2
	RiskHigh   = 3
)

// 申请状态
const (
	ReqDraft     = 0
	ReqPending   = 1
	ReqApproved  = 2
	ReqRejected  = 3
	ReqRevoked   = 4
)

// 审批动作
const (
	ApproveYes = 1
	ApproveNo  = 2
)

// 同步任务类型
const (
	SyncOpenAPI    = 1
	SyncCMDBModel  = 2
	SyncCMDBInst   = 3
	SyncIdentity   = 4
)

// 决策渠道
const (
	ChannelRemote = 1
	ChannelLocal  = 2
)

// 决策结果
const (
	DecisionAllow = 1
	DecisionDeny  = 2
)
