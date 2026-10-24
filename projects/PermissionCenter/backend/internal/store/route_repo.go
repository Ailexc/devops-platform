package store

import (
	"fmt"
	"strings"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

// v1.5 T1 路由表配套：版本递增 / 待确认队列 / 引用计数 / 归档 / 动作码迁移（方案 §3.7-§3.9）

// --- 路由表版本 ---

// BumpRouteVersion 导入/迁移/归档即版本递增，返回新版本号
func (r *AccessRepo) BumpRouteVersion(appID uint64, source, note string, by uint64) (int, error) {
	var last model.RouteVersion
	v := 1
	if err := r.db.Where("app_id = ?", appID).Order("version DESC").First(&last).Error; err == nil {
		v = last.Version + 1
	}
	if err := r.db.Create(&model.RouteVersion{
		AppID: appID, Version: v, Source: source, Note: note, CreatedBy: by,
	}).Error; err != nil {
		return 0, err
	}
	return v, nil
}

// CurrentRouteVersion 当前版本（0 = 从未导入，判定审计快照用）
func (r *AccessRepo) CurrentRouteVersion(appID uint64) int {
	var last model.RouteVersion
	if err := r.db.Where("app_id = ?", appID).Order("version DESC").First(&last).Error; err != nil {
		return 0
	}
	return last.Version
}

// --- 待确认队列（推断预填永不直接生效，人工确认后落表）---

// AddPending 入队；同 (app, method, path) 已有 pending → 更新推断结果（去重）
func (r *AccessRepo) AddPending(p *model.RoutePending) error {
	var existing model.RoutePending
	err := r.db.Where("app_id = ? AND method = ? AND path = ? AND status = ?",
		p.AppID, p.Method, p.Path, model.PendPending).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		return r.db.Create(p).Error
	}
	if err != nil {
		return err
	}
	existing.InferredCode, existing.RW, existing.Reason = p.InferredCode, p.RW, p.Reason
	return r.db.Save(&existing).Error
}

// Pendings 待确认清单（status 空 = 仅 pending）
func (r *AccessRepo) Pendings(appID uint64, status string) ([]model.RoutePending, error) {
	q := r.db.Where("app_id = ?", appID)
	if status == "" {
		status = model.PendPending
	}
	if status != "all" {
		q = q.Where("status = ?", status)
	}
	var out []model.RoutePending
	if err := q.Order("id").Find(&out).Error; err != nil {
		return nil, err
	}
	return out, nil
}

func (r *AccessRepo) PendingByID(id uint64) (*model.RoutePending, error) {
	var p model.RoutePending
	if err := r.db.First(&p, id).Error; err != nil {
		return nil, err
	}
	return &p, nil
}

func (r *AccessRepo) SetPendingStatus(id uint64, status string) error {
	return r.db.Model(&model.RoutePending{}).Where("id = ?", id).Update("status", status).Error
}

// --- 引用计数（归档拒删 / 迁移影响面，§3.9 与 A9 策略影响面同一家族）---

// ActionRefs 动作被谁引用
type ActionRefs struct {
	Policies     []map[string]any `json:"policies"`
	Capabilities []map[string]any `json:"capabilities"`
}

func (a *ActionRefs) Empty() bool { return len(a.Policies) == 0 && len(a.Capabilities) == 0 }

// ActionReferences 反查引用方：active 策略（ActionIDs 包含该 id）+ 能力包关联
func (r *AccessRepo) ActionReferences(actionID uint64) (*ActionRefs, error) {
	refs := &ActionRefs{Policies: []map[string]any{}, Capabilities: []map[string]any{}}
	var ps []model.Policy
	if err := r.db.Where("status = ? AND action_ids @> ?", int16(1), fmt.Sprintf("[%d]", actionID)).
		Find(&ps).Error; err != nil {
		return nil, err
	}
	for _, p := range ps {
		refs.Policies = append(refs.Policies, map[string]any{
			"id": p.ID, "name": p.Name, "effect": p.Effect,
		})
	}
	var cas []model.CapabilityAction
	if err := r.db.Where("action_id = ?", actionID).Find(&cas).Error; err != nil {
		return nil, err
	}
	if len(cas) > 0 {
		capIDs := make([]uint64, 0, len(cas))
		for _, ca := range cas {
			capIDs = append(capIDs, ca.CapabilityID)
		}
		var caps []model.CapabilityManifest
		r.db.Where("id IN ?", capIDs).Find(&caps)
		nameByID := map[uint64]string{}
		for _, c := range caps {
			nameByID[c.ID] = c.Name
		}
		for _, ca := range cas {
			refs.Capabilities = append(refs.Capabilities, map[string]any{
				"id": ca.CapabilityID, "name": nameByID[ca.CapabilityID],
			})
		}
	}
	return refs, nil
}

// --- 归档 / 恢复（归档不删、可查不可用）---

// SetActionStatus 只改状态列（active|archived）
func (r *AccessRepo) SetActionStatus(actionID uint64, status string) error {
	return r.db.Model(&model.Action{}).Where("id = ?", actionID).Update("status", status).Error
}

// --- 动作码迁移（改名不存在→变更阻断+一键迁移，§3.9 词表规矩 3）---

// ValidateActionCode 词表规矩 1：委托 model.ValidateCodeFormat（全小写三段）
func ValidateActionCode(code string) error {
	return model.ValidateCodeFormat(code)
}

// MigrateActionCode 批量替换引用留给 ID 引用结构天然免疫（策略按 ActionID 关联），
// 本方法执行：换码 + operation 跟随第三段 + 留迁移记录（旧码/新码/谁/受影响清单快照）。
// 语义等价的改名才迁移；语义变了=新增+归档（调用方把关）。
func (r *AccessRepo) MigrateActionCode(actionID uint64, newCode string, by uint64) (*model.Action, *model.RouteMigrateLog, error) {
	if err := ValidateActionCode(newCode); err != nil {
		return nil, nil, err
	}
	a, err := r.ActionByID(actionID)
	if err != nil {
		return nil, nil, err
	}
	// 同 app 内新码占用检查（同码挂多路由 = 体检阻断项，迁移入口先挡）
	var dup model.Action
	err = r.db.Where("app_id = ? AND code = ? AND id <> ?", a.AppID, newCode, actionID).First(&dup).Error
	if err == nil {
		return nil, nil, fmt.Errorf("动作码 %s 已存在（挂载 %s %s）", newCode, dup.Method, dup.Path)
	}
	if err != nil && err != gorm.ErrRecordNotFound {
		return nil, nil, err
	}
	refs, err := r.ActionReferences(actionID)
	if err != nil {
		return nil, nil, err
	}
	oldCode := a.Code
	parts := strings.Split(newCode, ":")
	logRow := &model.RouteMigrateLog{
		AppID: a.AppID, ActionID: actionID, OldCode: oldCode, NewCode: newCode,
		Affected: model.JSONMap{
			"policies": refs.Policies, "capabilities": refs.Capabilities,
		},
		MigratedBy: by,
	}
	txErr := r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Model(&model.Action{}).Where("id = ?", actionID).
			Updates(map[string]any{"code": newCode, "operation": parts[2]}).Error; err != nil {
			return err
		}
		return tx.Create(logRow).Error
	})
	if txErr != nil {
		return nil, nil, txErr
	}
	a.Code, a.Operation = newCode, parts[2]
	return a, logRow, nil
}

// MigrateLogs 迁移记录（审计可查）
func (r *AccessRepo) MigrateLogs(appID uint64) ([]model.RouteMigrateLog, error) {
	var out []model.RouteMigrateLog
	err := r.db.Where("app_id = ?", appID).Order("id DESC").Limit(50).Find(&out).Error
	return out, err
}
