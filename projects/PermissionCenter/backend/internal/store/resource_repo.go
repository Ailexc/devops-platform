package store

import (
	"log"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type ResourceRepo struct{ db *gorm.DB }

func NewResourceRepo(db *gorm.DB) *ResourceRepo { return &ResourceRepo{db: db} }

// UpsertModel upsert 模型投影；返回 written=false 表示指纹未变跳过写库（清单 A1 去重）
func (r *ResourceRepo) UpsertModel(m *model.ResourceModel) (bool, error) {
	var existing model.ResourceModel
	err := r.db.Where("source_id = ?", m.SourceID).First(&existing).Error
	fpIn := model.ComputeModelFP(m)
	m.FP = fpIn
	if err == gorm.ErrRecordNotFound {
		return true, r.db.Create(m).Error
	}
	if err != nil {
		return false, err
	}
	if existing.FP == fpIn {
		return false, nil // 定义未变，不写库
	}
	existing.Name, existing.Code = m.Name, m.Code
	existing.AttributesSchema = m.AttributesSchema
	existing.SyncedAt = m.SyncedAt
	existing.FP = fpIn
	if m.AppID != 0 {
		existing.AppID = m.AppID
	}
	return true, r.db.Save(&existing).Error
}

func (r *ResourceRepo) ModelByCode(code string) (*model.ResourceModel, error) {
	var m model.ResourceModel
	if err := r.db.Where("code = ?", code).First(&m).Error; err != nil {
		return nil, err
	}
	return &m, nil
}

func (r *ResourceRepo) Models() ([]model.ResourceModel, error) {
	var ms []model.ResourceModel
	if err := r.db.Order("id").Find(&ms).Error; err != nil {
		return nil, err
	}
	return ms, nil
}

// UpsertInstance upsert 实例投影，三道门（清单 A1）：
//  1. 单调守卫：上游时间戳倒退（事件乱序/迟到旧版本）→ 跳过，防旧覆新（regression_skip 日志）
//  2. 记录级指纹去重：判定字段未变 → 不写库（skip，由调用方计入 skip 计数）
//  3. 均通过才落库；返回 written=false 表示跳过
func (r *ResourceRepo) UpsertInstance(inst *model.ResourceInstance) (bool, error) {
	fpIn := model.ComputeInstanceFP(inst)
	var existing model.ResourceInstance
	err := r.db.Where("model_id = ? AND external_id = ?", inst.ModelID, inst.ExternalID).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		inst.FP = fpIn
		return true, r.db.Create(inst).Error
	}
	if err != nil {
		return false, err
	}
	if inst.UpstreamUpdatedAt != nil && existing.UpstreamUpdatedAt != nil &&
		inst.UpstreamUpdatedAt.Before(*existing.UpstreamUpdatedAt) {
		log.Printf("[sync] regression_skip instance %s: upstream ts %s < stored %s",
			inst.ExternalID, inst.UpstreamUpdatedAt.Format(time.RFC3339Nano), existing.UpstreamUpdatedAt.Format(time.RFC3339Nano))
		return false, nil
	}
	if existing.FP == fpIn {
		return false, nil // 判定字段未变，写库去重
	}
	existing.Name = inst.Name
	existing.Attributes = inst.Attributes
	existing.OwnerID = inst.OwnerID
	existing.SyncedAt = inst.SyncedAt
	existing.UpstreamUpdatedAt = inst.UpstreamUpdatedAt
	existing.FP = fpIn
	return true, r.db.Save(&existing).Error
}

func (r *ResourceRepo) DeleteInstanceByExternal(modelID uint64, externalID string) error {
	return r.db.Where("model_id = ? AND external_id = ?", modelID, externalID).Delete(&model.ResourceInstance{}).Error
}

func (r *ResourceRepo) Instances(modelID uint64, offset, limit int) ([]model.ResourceInstance, int64, error) {
	var total int64
	r.db.Model(&model.ResourceInstance{}).Where("model_id = ?", modelID).Count(&total)
	var is []model.ResourceInstance
	if err := r.db.Where("model_id = ?", modelID).Order("id").Offset(offset).Limit(limit).Find(&is).Error; err != nil {
		return nil, 0, err
	}
	return is, total, nil
}

func (r *ResourceRepo) InstanceByExternal(modelID uint64, externalID string) (*model.ResourceInstance, error) {
	var inst model.ResourceInstance
	if err := r.db.Where("model_id = ? AND external_id = ?", modelID, externalID).First(&inst).Error; err != nil {
		return nil, err
	}
	return &inst, nil
}

// InstancesByIDs 按内部 ID 批量取（filter 列表兜底）
func (r *ResourceRepo) InstancesByIDs(ids []uint64) ([]model.ResourceInstance, error) {
	var is []model.ResourceInstance
	if err := r.db.Where("id IN ?", ids).Find(&is).Error; err != nil {
		return nil, err
	}
	return is, nil
}

func (r *ResourceRepo) SetSyncedAt(modelID uint64, t any) error {
	return r.db.Model(&model.ResourceModel{}).Where("id = ?", modelID).Update("synced_at", t).Error
}
