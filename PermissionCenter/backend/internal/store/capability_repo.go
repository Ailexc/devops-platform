package store

import (
	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

// CapabilityRepo L1 能力声明
type CapabilityRepo struct{ db *gorm.DB }

func NewCapabilityRepo(db *gorm.DB) *CapabilityRepo { return &CapabilityRepo{db: db} }

func (r *CapabilityRepo) Create(m *model.CapabilityManifest) error { return r.db.Create(m).Error }
func (r *CapabilityRepo) Update(m *model.CapabilityManifest) error { return r.db.Save(m).Error }
func (r *CapabilityRepo) ByID(id uint64) (*model.CapabilityManifest, error) {
	var m model.CapabilityManifest
	if err := r.db.First(&m, id).Error; err != nil {
		return nil, err
	}
	return &m, nil
}
func (r *CapabilityRepo) Delete(id uint64) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Where("capability_id = ?", id).Delete(&model.CapabilityAction{}).Error; err != nil {
			return err
		}
		if err := tx.Where("capability_id = ?", id).Delete(&model.ScopeOption{}).Error; err != nil {
			return err
		}
		return tx.Delete(&model.CapabilityManifest{}, id).Error
	})
}

func (r *CapabilityRepo) List(appID uint64) ([]model.CapabilityManifest, error) {
	var ms []model.CapabilityManifest
	if err := r.db.Where("app_id = ?", appID).Order("id").Find(&ms).Error; err != nil {
		return nil, err
	}
	return ms, nil
}

// Published 权限市场可见：全部应用已发布能力
func (r *CapabilityRepo) Published() ([]model.CapabilityManifest, error) {
	var ms []model.CapabilityManifest
	if err := r.db.Where("status = ?", model.CapPublished).Order("id").Find(&ms).Error; err != nil {
		return nil, err
	}
	return ms, nil
}

// SetActions 覆盖写能力 → 动作映射
func (r *CapabilityRepo) SetActions(capabilityID uint64, acts []*model.CapabilityAction) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Where("capability_id = ?", capabilityID).Delete(&model.CapabilityAction{}).Error; err != nil {
			return err
		}
		if len(acts) > 0 {
			if err := tx.CreateInBatches(acts, 100).Error; err != nil {
				return err
			}
		}
		return nil
	})
}

// Actions 能力 → 动作列表（含权限点信息）
func (r *CapabilityRepo) Actions(capabilityID uint64) ([]model.CapabilityAction, error) {
	var acts []model.CapabilityAction
	if err := r.db.Where("capability_id = ?", capabilityID).Find(&acts).Error; err != nil {
		return nil, err
	}
	return acts, nil
}

// ActionByOperation 能力下某数据操作对应的动作
func (r *CapabilityRepo) ActionByOperation(capabilityID uint64, operation string) (*model.CapabilityAction, error) {
	var a model.CapabilityAction
	if err := r.db.Where("capability_id = ? AND data_operation = ?", capabilityID, operation).First(&a).Error; err != nil {
		return nil, err
	}
	return &a, nil
}

// ---- ScopeOption（v12 范围选项独立表，D1）----

// ReplaceScopeOptions 覆盖写某预设×数据模型的范围选项（编辑保存）
func (r *CapabilityRepo) ReplaceScopeOptions(capabilityID uint64, presetID, modelCode string, opts []*model.ScopeOption) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Where("capability_id = ? AND preset_id = ? AND model_code = ?",
			capabilityID, presetID, modelCode).Delete(&model.ScopeOption{}).Error; err != nil {
			return err
		}
		for i, o := range opts {
			o.CapabilityID = capabilityID
			o.PresetID = presetID
			o.ModelCode = modelCode
			o.Seq = i
		}
		if len(opts) > 0 {
			if err := tx.CreateInBatches(opts, 100).Error; err != nil {
				return err
			}
		}
		return nil
	})
}

// ScopeOptions 查询某预设×数据模型的范围选项（按 seq 排序）
func (r *CapabilityRepo) ScopeOptions(capabilityID uint64, presetID, modelCode string) ([]model.ScopeOption, error) {
	var opts []model.ScopeOption
	if err := r.db.Where("capability_id = ? AND preset_id = ? AND model_code = ?",
		capabilityID, presetID, modelCode).Order("seq").Find(&opts).Error; err != nil {
		return nil, err
	}
	return opts, nil
}

// AllScopeOptions 某能力包全部范围选项（预加载/快照用）
func (r *CapabilityRepo) AllScopeOptions(capabilityID uint64) ([]model.ScopeOption, error) {
	var opts []model.ScopeOption
	if err := r.db.Where("capability_id = ?", capabilityID).Order("preset_id, model_code, seq").Find(&opts).Error; err != nil {
		return nil, err
	}
	return opts, nil
}

// DeleteScopeOptions 删除某预设全部范围选项（预设删除时）
func (r *CapabilityRepo) DeleteScopeOptions(capabilityID uint64, presetID string) error {
	return r.db.Where("capability_id = ? AND preset_id = ?", capabilityID, presetID).Delete(&model.ScopeOption{}).Error
}

// ---- PolicyTemplate L3 ----

type PolicyTemplateRepo struct{ db *gorm.DB }

func NewPolicyTemplateRepo(db *gorm.DB) *PolicyTemplateRepo { return &PolicyTemplateRepo{db: db} }

func (r *PolicyTemplateRepo) Create(t *model.PolicyTemplate) error { return r.db.Create(t).Error }
func (r *PolicyTemplateRepo) Update(t *model.PolicyTemplate) error { return r.db.Save(t).Error }
func (r *PolicyTemplateRepo) ByID(id uint64) (*model.PolicyTemplate, error) {
	var t model.PolicyTemplate
	if err := r.db.First(&t, id).Error; err != nil {
		return nil, err
	}
	return &t, nil
}
func (r *PolicyTemplateRepo) Delete(id uint64) error { return r.db.Delete(&model.PolicyTemplate{}, id).Error }

func (r *PolicyTemplateRepo) List(appID uint64) ([]model.PolicyTemplate, error) {
	var ts []model.PolicyTemplate
	if err := r.db.Where("app_id = ?", appID).Order("id").Find(&ts).Error; err != nil {
		return nil, err
	}
	return ts, nil
}

// Published 市场可见模板（发布态）
func (r *PolicyTemplateRepo) Published() ([]model.PolicyTemplate, error) {
	var ts []model.PolicyTemplate
	if err := r.db.Where("status = ?", "published").Order("id").Find(&ts).Error; err != nil {
		return nil, err
	}
	return ts, nil
}

// IncApply 被申请次数 +1
func (r *PolicyTemplateRepo) IncApply(id uint64) error {
	return r.db.Model(&model.PolicyTemplate{}).Where("id = ?", id).
		UpdateColumn("apply_count", gorm.Expr("apply_count + 1")).Error
}
