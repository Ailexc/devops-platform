package store

import (
	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type PolicyRepo struct{ db *gorm.DB }

func NewPolicyRepo(db *gorm.DB) *PolicyRepo { return &PolicyRepo{db: db} }

func (r *PolicyRepo) Create(p *model.Policy) error { return r.db.Create(p).Error }
func (r *PolicyRepo) Update(p *model.Policy) error { return r.db.Save(p).Error }

func (r *PolicyRepo) ByID(id uint64) (*model.Policy, error) {
	var p model.Policy
	if err := r.db.First(&p, id).Error; err != nil {
		return nil, err
	}
	return &p, nil
}

func (r *PolicyRepo) List(appID *uint64, offset, limit int) ([]model.Policy, int64, error) {
	var total int64
	q := r.db.Model(&model.Policy{})
	if appID != nil {
		q = q.Where("app_id = ?", *appID)
	}
	q.Count(&total)

	var ps []model.Policy
	q2 := r.db.Order("id")
	if appID != nil {
		q2 = q2.Where("app_id = ?", *appID)
	}
	if err := q2.Offset(offset).Limit(limit).Find(&ps).Error; err != nil {
		return nil, 0, err
	}
	return ps, total, nil
}

// ActiveByApp 该应用下全部有效策略（构建 Casbin / bundle）
func (r *PolicyRepo) ActiveByApp(appID uint64) ([]model.Policy, error) {
	var ps []model.Policy
	if err := r.db.Where("app_id = ? AND status = ?", appID, model.PolicyActive).Find(&ps).Error; err != nil {
		return nil, err
	}
	return ps, nil
}

func (r *PolicyRepo) CreateVersion(v *model.PolicyVersion) error { return r.db.Create(v).Error }

func (r *PolicyRepo) Versions(policyID uint64) ([]model.PolicyVersion, error) {
	var vs []model.PolicyVersion
	if err := r.db.Where("policy_id = ?", policyID).Order("version desc").Find(&vs).Error; err != nil {
		return nil, err
	}
	return vs, nil
}
