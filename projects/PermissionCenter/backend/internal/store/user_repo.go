package store

import (
	"errors"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type UserRepo struct{ db *gorm.DB }

func NewUserRepo(db *gorm.DB) *UserRepo { return &UserRepo{db: db} }

var ErrNotFound = errors.New("not found")

func (r *UserRepo) Create(u *model.User) error  { return r.db.Create(u).Error }
func (r *UserRepo) Update(u *model.User) error  { return r.db.Save(u).Error }
func (r *UserRepo) Delete(id uint64) error      { return r.db.Delete(&model.User{}, id).Error }

func (r *UserRepo) ByID(id uint64) (*model.User, error) {
	var u model.User
	if err := r.db.First(&u, id).Error; err != nil {
		return nil, err
	}
	return &u, nil
}

func (r *UserRepo) ByUsername(username string) (*model.User, error) {
	var u model.User
	if err := r.db.Where("username = ?", username).First(&u).Error; err != nil {
		return nil, err
	}
	return &u, nil
}

func (r *UserRepo) List(offset, limit int) ([]model.User, int64, error) {
	var total int64
	r.db.Model(&model.User{}).Count(&total)
	var us []model.User
	if err := r.db.Order("id").Offset(offset).Limit(limit).Find(&us).Error; err != nil {
		return nil, 0, err
	}
	return us, total, nil
}
