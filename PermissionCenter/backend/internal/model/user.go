package model

import "time"

// User 用户
// attributes: ABAC 属性（部门/级别等）；source: 1=identity 同步(只读) 2=manual 手工
// token_version: 停用/改密时 +1，旧 token 即时失效
type User struct {
	Base
	Username     string         `gorm:"size:64;uniqueIndex;not null" json:"username"`
	DisplayName  string         `gorm:"size:128" json:"display_name"`
	Email        string         `gorm:"size:128;uniqueIndex" json:"email"`
	PasswordHash string         `gorm:"size:255;not null" json:"-"`
	Status       int16          `gorm:"not null;default:1" json:"status"`
	Attributes   JSONMap        `gorm:"type:jsonb;default:'{}'" json:"attributes"`
	Source       int16          `gorm:"not null;default:2" json:"source"`
	TokenVersion int            `gorm:"not null;default:1" json:"token_version"`
}

// Group 组织架构树 + 自建组（组即角色）
// type: 1=org 组织架构 2=custom 自建组；path: 物化路径（应用层维护，如 /1/2/3/）
// expires_at: 组级有效期（TTL 组）；status: 1=active 0=expired
type Group struct {
	Base
	Name      string     `gorm:"size:128;not null" json:"name"`
	ParentID  *uint64    `gorm:"index" json:"parent_id"`
	Type      int16      `gorm:"not null;default:2" json:"type"`
	Path      string     `gorm:"size:255;index" json:"path"`
	Source    int16      `gorm:"not null;default:2" json:"source"`
	ExpiresAt *time.Time `json:"expires_at"` // 组级有效期（可空=永久）
	Status    int16      `gorm:"not null;default:1" json:"status"` // 1=active 0=expired
}

// UserGroup 用户-组 成员关系
type UserGroup struct {
	Base
	UserID  uint64 `gorm:"uniqueIndex:idx_ug;not null" json:"user_id"`
	GroupID uint64 `gorm:"uniqueIndex:idx_ug;not null" json:"group_id"`
	Role      int16      `gorm:"not null;default:1" json:"role"`       // 1=member 2=admin
	ExpiresAt *time.Time `json:"expires_at"`                              // 成员级 TTL（临时授权）
}
