package model

import "time"

// ResourceModel 数据模型（= CMDB 表概念，同步索引投影）
type ResourceModel struct {
	Base
	SourceID         uint64     `gorm:"uniqueIndex;not null" json:"source_id"`
	AppID            uint64     `gorm:"index" json:"app_id"` // 归属应用（0=未关联，用于"我接入了谁"展示对方数据模型）
	Name             string     `gorm:"size:128;not null" json:"name"`
	Code             string     `gorm:"size:128;uniqueIndex;not null" json:"code"`
	AttributesSchema JSONMap    `gorm:"type:jsonb" json:"attributes_schema"`
	SyncedAt         *time.Time `json:"synced_at"`
}

// ResourceInstance 资源实例（只存权限判断所需字段——投影裁剪，防数据膨胀）
type ResourceInstance struct {
	Base
	ModelID    uint64     `gorm:"uniqueIndex:idx_model_ext;not null" json:"model_id"`
	ExternalID string     `gorm:"size:128;uniqueIndex:idx_model_ext;not null" json:"external_id"`
	Name       string     `gorm:"size:128" json:"name"`
	Attributes JSONMap    `gorm:"type:jsonb" json:"attributes"`
	OwnerID    *uint64    `gorm:"index" json:"owner_id"` // 关系锚点
	SyncedAt   *time.Time `json:"synced_at"`
}
