package store

import (
	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type AppRepo struct{ db *gorm.DB }

func NewAppRepo(db *gorm.DB) *AppRepo { return &AppRepo{db: db} }

func (r *AppRepo) Create(a *model.App) error { return r.db.Create(a).Error }
func (r *AppRepo) Update(a *model.App) error { return r.db.Save(a).Error }

func (r *AppRepo) ByID(id uint64) (*model.App, error) {
	var a model.App
	if err := r.db.First(&a, id).Error; err != nil {
		return nil, err
	}
	return &a, nil
}

func (r *AppRepo) ByCode(code string) (*model.App, error) {
	var a model.App
	if err := r.db.Where("code = ?", code).First(&a).Error; err != nil {
		return nil, err
	}
	return &a, nil
}

func (r *AppRepo) List(offset, limit int) ([]model.App, int64, error) {
	var total int64
	r.db.Model(&model.App{}).Count(&total)
	var as []model.App
	if err := r.db.Order("id").Offset(offset).Limit(limit).Find(&as).Error; err != nil {
		return nil, 0, err
	}
	return as, total, nil
}

// Client 相关
func (r *AppRepo) CreateClient(c *model.Client) error { return r.db.Create(c).Error }
func (r *AppRepo) UpdateClient(c *model.Client) error { return r.db.Save(c).Error }

func (r *AppRepo) ClientByID(clientID string) (*model.Client, error) {
	var c model.Client
	if err := r.db.Where("client_id = ?", clientID).First(&c).Error; err != nil {
		return nil, err
	}
	return &c, nil
}

// ClientByRowID 按 clients.id 取（service subject 策略解析用）
func (r *AppRepo) ClientByRowID(id uint64) (*model.Client, error) {
	var c model.Client
	if err := r.db.First(&c, id).Error; err != nil {
		return nil, err
	}
	return &c, nil
}

func (r *AppRepo) Clients(appID uint64) ([]model.Client, error) {
	var cs []model.Client
	if err := r.db.Where("app_id = ?", appID).Find(&cs).Error; err != nil {
		return nil, err
	}
	return cs, nil
}

func (r *AppRepo) ClientsByIDs(ids []uint64) ([]model.Client, error) {
	var cs []model.Client
	if err := r.db.Where("id IN ?", ids).Find(&cs).Error; err != nil {
		return nil, err
	}
	return cs, nil
}

func (r *AppRepo) AllClients() ([]model.Client, error) {
	var cs []model.Client
	if err := r.db.Order("id").Find(&cs).Error; err != nil {
		return nil, err
	}
	return cs, nil
}

// AppOwner 相关
func (r *AppRepo) AddOwner(owner *model.AppOwner) error {
	// IsPrimary=false 是有效值：gorm 对零值字段默认不写入（配合 DB default:true 会兜底成 true），
	// 且 Create 后会把 DB 默认值回写到结构体（owner.IsPrimary 变回 true），
	// 故须在 Create 前捕获意图值，非主负责人再显式回写 false。
	// 否则注册/seed 的联合负责人会被误标成"主"。
	isPrimary := owner.IsPrimary
	if err := r.db.Create(owner).Error; err != nil {
		return err
	}
	if !isPrimary {
		return r.db.Model(&model.AppOwner{}).
			Where("app_id = ? AND user_id = ?", owner.AppID, owner.UserID).
			Update("is_primary", false).Error
	}
	return nil
}

func (r *AppRepo) Owners(appID uint64) ([]model.AppOwner, error) {
	var os []model.AppOwner
	if err := r.db.Where("app_id = ?", appID).Find(&os).Error; err != nil {
		return nil, err
	}
	return os, nil
}

func (r *AppRepo) IsOwner(appID, userID uint64) (bool, error) {
	var n int64
	if err := r.db.Model(&model.AppOwner{}).
		Where("app_id = ? AND user_id = ?", appID, userID).
		Count(&n).Error; err != nil {
		return false, err
	}
	return n > 0, nil
}

// ByOwnerID 返回用户拥有的所有应用
func (r *AppRepo) ByOwnerID(userID uint64) ([]model.App, error) {
	var as []model.App
	err := r.db.
		Joins("JOIN app_owners ao ON ao.app_id = apps.id").
		Where("ao.user_id = ?", userID).
		Find(&as).Error
	return as, err
}
