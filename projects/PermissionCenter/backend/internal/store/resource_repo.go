package store

import (
	"crypto/sha256"
	"encoding/hex"
	"log"
	"strings"
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
		// 指纹未变但上游时间戳推进（touch/首次回填）→ 只回填时间戳列。
		// 否则本地集合指纹 ts 侧永远对不上上游（A4 巡检会每轮失配→拉取→skip 死循环）
		if tsChanged(existing.UpstreamUpdatedAt, inst.UpstreamUpdatedAt) {
			existing.UpstreamUpdatedAt = inst.UpstreamUpdatedAt
			existing.SyncedAt = inst.SyncedAt
			return true, r.db.Model(&model.ResourceInstance{}).Where("id = ?", existing.ID).
				Updates(map[string]any{"upstream_updated_at": inst.UpstreamUpdatedAt, "synced_at": inst.SyncedAt}).Error
		}
		return false, nil // 判定字段与时间戳都未变，写库去重
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

// tsChanged 上游时间戳是否推进（nil→有值 / 值不同；方向安全已由单调守卫在前把关）
func tsChanged(oldTS, newTS *time.Time) bool {
	if newTS == nil {
		return false
	}
	if oldTS == nil {
		return true
	}
	return !newTS.Equal(*oldTS)
}

func sha256Hex(s string) string {
	sum := sha256.Sum256([]byte(s))
	return hex.EncodeToString(sum[:])
}

// SetFingerprint 域集合指纹——契约算法（清单 A3/A4，与 mock /sync/fingerprint 两侧逐字一致）：
//
//	external_id 按字典序 → hash_ids = sha256(join("\n"))
//	同序 upstream_updated_at（RFC3339Nano 规范化）→ hash_ts = sha256(join("\n"))
//
// 用途：巡检脏检（上游指纹 vs 本地指纹）与强一致档指纹快查。返回 (hashIDs, hashTS, count, err)
func (r *ResourceRepo) SetFingerprint(modelCode string) (string, string, int, error) {
	m, err := r.ModelByCode(modelCode)
	if err != nil {
		return "", "", 0, err
	}
	type row struct {
		ExternalID        string
		UpstreamUpdatedAt *time.Time
	}
	var rows []row
	if err := r.db.Model(&model.ResourceInstance{}).
		Where("model_id = ?", m.ID).
		Select("external_id, upstream_updated_at").
		Order("external_id").
		Scan(&rows).Error; err != nil {
		return "", "", 0, err
	}
	var idBuf, tsBuf strings.Builder
	for _, row := range rows {
		idBuf.WriteString(row.ExternalID)
		idBuf.WriteByte('\n')
		if row.UpstreamUpdatedAt != nil {
			tsBuf.WriteString(row.UpstreamUpdatedAt.Format(time.RFC3339Nano))
		}
		tsBuf.WriteByte('\n')
	}
	return sha256Hex(idBuf.String()), sha256Hex(tsBuf.String()), len(rows), nil
}

// InstancesByModelAll 域内全部投影记录（深对账差异比对用，清单 A5b）
func (r *ResourceRepo) InstancesByModelAll(modelID uint64) ([]model.ResourceInstance, error) {
	var is []model.ResourceInstance
	err := r.db.Where("model_id = ?", modelID).Order("external_id").Find(&is).Error
	return is, err
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
