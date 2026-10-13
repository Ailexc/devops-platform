package model

import (
	"fmt"
	"strings"
)

// v1.5 T1 动作码路由表配套（方案 §3.7/§3.8/§3.9）
// Action 本体即路由表行（Method/Path/Code），此处补版本、待确认队列、迁移记录三件。

// RouteVersion 路由表版本：每次导入/迁移/归档递增；
// 判定审计写 (action_code, route_version) 快照——"当时按哪版路由表判的"可复现（§3.9）
type RouteVersion struct {
	Base
	AppID     uint64 `gorm:"index;not null" json:"app_id"`
	Version   int    `gorm:"not null" json:"version"`
	Source    string `gorm:"size:32;not null" json:"source"` // openapi|dict|manual|migrate|archive|restore
	Note      string `gorm:"size:256" json:"note"`
	CreatedBy uint64 `json:"created_by"`
}

// RoutePending 待确认队列：推断预填永不直接生效，人工确认后才落表（§3.8 ⑤兜底）
type RoutePending struct {
	Base
	AppID        uint64 `gorm:"index;not null" json:"app_id"`
	Method       string `gorm:"size:16;not null" json:"method"`
	Path         string `gorm:"size:256;not null" json:"path"`
	InferredCode string `gorm:"size:128" json:"inferred_code"` // 推断出的动作码（app 段已补全）
	RW           string `gorm:"size:8" json:"rw"`              // read|write
	Reason       string `gorm:"size:256" json:"reason"`        // 推断依据 / 推不出原因
	Status       string `gorm:"size:16;default:pending" json:"status"`
}

// 待确认队列状态
const (
	PendPending   = "pending"
	PendConfirmed = "confirmed"
	PendDiscarded = "discarded"
)

// Action.Status 状态（归档=可查不可用，方案 §3.9）
const (
	StatusActive   = "active"
	StatusArchived = "archived"
)

// ValidateCodeFormat 词表规矩 1：全小写三段 app:resource:verb（§3.9，机器校验无审批流）
func ValidateCodeFormat(code string) error {
	parts := strings.Split(code, ":")
	if len(parts) != 3 {
		return fmt.Errorf("动作码须为三段 app:resource:verb")
	}
	for _, p := range parts {
		if p == "" {
			return fmt.Errorf("动作码段不能为空")
		}
		for _, ch := range p {
			ok := (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_' || ch == '-'
			if !ok {
				return fmt.Errorf("动作码须全小写（含 _ -），非法段 %q", p)
			}
		}
	}
	return nil
}

// RouteMigrateLog 动作码变更迁移记录：改名不存在→变更阻断+一键迁移（§3.9 词表规矩 3）
// 语义等价的改名才迁移；迁移只换词并留记录（旧码/新码/谁/何时/受影响清单）。
type RouteMigrateLog struct {
	Base
	AppID      uint64  `gorm:"index" json:"app_id"`
	ActionID   uint64  `gorm:"index" json:"action_id"`
	OldCode    string  `gorm:"size:128" json:"old_code"`
	NewCode    string  `gorm:"size:128" json:"new_code"`
	Affected   JSONMap `gorm:"type:jsonb" json:"affected"` // 迁移时受影响清单快照（策略/能力包）
	MigratedBy uint64  `json:"migrated_by"`
}
