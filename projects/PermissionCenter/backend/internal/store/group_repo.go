package store

import (
	"time"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type GroupRepo struct{ db *gorm.DB }

func NewGroupRepo(db *gorm.DB) *GroupRepo { return &GroupRepo{db: db} }

func (r *GroupRepo) Create(g *model.Group) error { return r.db.Create(g).Error }
func (r *GroupRepo) Update(g *model.Group) error { return r.db.Save(g).Error }
func (r *GroupRepo) Delete(id uint64) error      { return r.db.Delete(&model.Group{}, id).Error }

func (r *GroupRepo) ByID(id uint64) (*model.Group, error) {
	var g model.Group
	if err := r.db.First(&g, id).Error; err != nil {
		return nil, err
	}
	return &g, nil
}

// Tree 返回全部组（应用层维护物化路径，子树查询用 path LIKE 'prefix%'）
func (r *GroupRepo) Tree() ([]model.Group, error) {
	var gs []model.Group
	if err := r.db.Order("path").Find(&gs).Error; err != nil {
		return nil, err
	}
	return gs, nil
}

// FindOrgByNameParent 幂等查找组织节点（name+parent；source<=0 表示不限来源）
func (r *GroupRepo) FindOrgByNameParent(name string, parentID *uint64, source int16) (*model.Group, error) {
	var g model.Group
	q := r.db.Where("name = ? AND type = ?", name, model.GroupTypeOrg)
	if source > 0 {
		q = q.Where("source = ?", source)
	}
	if parentID == nil {
		q = q.Where("parent_id IS NULL")
	} else {
		q = q.Where("parent_id = ?", *parentID)
	}
	if err := q.First(&g).Error; err != nil {
		return nil, err
	}
	return &g, nil
}

// SubtreeIDs 物化路径前缀查询子树（LIKE 前缀，不写裸 SQL）
func (r *GroupRepo) SubtreeIDs(prefix string) ([]uint64, error) {
	var ids []uint64
	if err := r.db.Model(&model.Group{}).Where("path LIKE ?", prefix+"%").Pluck("id", &ids).Error; err != nil {
		return nil, err
	}
	return ids, nil
}

func (r *GroupRepo) AddMember(ug *model.UserGroup) error {
	return r.db.Create(ug).Error
}

// AllMemberships 全部用户-组关系（策略构建用）
func (r *GroupRepo) AllMemberships(out *[]model.UserGroup) error {
	return r.db.Find(out).Error
}

func (r *GroupRepo) RemoveMember(userID, groupID uint64) error {
	return r.db.Where("user_id = ? AND group_id = ?", userID, groupID).Delete(&model.UserGroup{}).Error
}

// ExpireGroups 过期组状态更新（定时任务调用）
func (r *GroupRepo) ExpireGroups(now time.Time) (int64, error) {
	result := r.db.Model(&model.Group{}).
		Where("expires_at IS NOT NULL AND expires_at <= ? AND status = ?", now, model.StatusEnabled).
		Update("status", model.StatusDisabled)
	return result.RowsAffected, result.Error
}

// ActiveGroups 返回有效组
func (r *GroupRepo) ActiveGroups() ([]model.Group, error) {
	var gs []model.Group
	if err := r.db.Where("status = ?", model.StatusEnabled).Order("path").Find(&gs).Error; err != nil {
		return nil, err
	}
	return gs, nil
}

func (r *GroupRepo) Members(groupID uint64) ([]model.User, error) {
	var us []model.User
	err := r.db.
		Joins("JOIN user_groups ug ON ug.user_id = users.id").
		Where("ug.group_id = ?", groupID).
		Find(&us).Error
	return us, err
}

// ByUserID 返回用户所属的组列表
func (r *GroupRepo) ByUserID(userID uint64) ([]model.Group, error) {
	var gs []model.Group
	err := r.db.
		Joins("JOIN user_groups ug ON ug.group_id = groups.id").
		Where("ug.user_id = ?", userID).
		Find(&gs).Error
	return gs, err
}

// MemberGroupIDs 用户在哪些组（含组嵌套——应用层展开祖先链）
func (r *GroupRepo) MemberGroupIDs(userID uint64) ([]uint64, error) {
	var ids []uint64
	if err := r.db.Model(&model.UserGroup{}).Where("user_id = ?", userID).Pluck("group_id", &ids).Error; err != nil {
		return nil, err
	}
	// 展开祖先链：每个组沿 path 向上
	var groups []model.Group
	if len(ids) > 0 {
		r.db.Where("id IN ?", ids).Find(&groups)
	}
	seen := map[uint64]bool{}
	var all []uint64
	for _, g := range groups {
		anc := ancestorsFromPath(g.Path)
		for _, id := range anc {
			if !seen[id] {
				seen[id] = true
				all = append(all, id)
			}
		}
	}
	return all, nil
}

// ancestorsFromPath 从物化路径 /1/2/3/ 解析出全部祖先 id
func ancestorsFromPath(path string) []uint64 {
	var ids []uint64
	cur := uint64(0)
	for _, c := range path {
		if c >= '0' && c <= '9' {
			cur = cur*10 + uint64(c-'0')
		} else if c == '/' && cur > 0 {
			ids = append(ids, cur)
			cur = 0
		}
	}
	return ids
}
