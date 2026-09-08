package store

import (
	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type ResourceRepo struct{ db *gorm.DB }

func NewResourceRepo(db *gorm.DB) *ResourceRepo { return &ResourceRepo{db: db} }

func (r *ResourceRepo) UpsertModel(m *model.ResourceModel) error {
	var existing model.ResourceModel
	err := r.db.Where("source_id = ?", m.SourceID).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		return r.db.Create(m).Error
	}
	if err != nil {
		return err
	}
	existing.Name, existing.Code = m.Name, m.Code
	existing.AttributesSchema = m.AttributesSchema
	existing.SyncedAt = m.SyncedAt
	if m.AppID != 0 {
		existing.AppID = m.AppID
	}
	return r.db.Save(&existing).Error
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

func (r *ResourceRepo) UpsertInstance(inst *model.ResourceInstance) error {
	var existing model.ResourceInstance
	err := r.db.Where("model_id = ? AND external_id = ?", inst.ModelID, inst.ExternalID).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		return r.db.Create(inst).Error
	}
	if err != nil {
		return err
	}
	existing.Name = inst.Name
	existing.Attributes = inst.Attributes
	existing.OwnerID = inst.OwnerID
	existing.SyncedAt = inst.SyncedAt
	return r.db.Save(&existing).Error
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
