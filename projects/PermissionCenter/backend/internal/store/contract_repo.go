package store

import (
	"time"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

// ContractRepo 数据契约 + 巡检日志读写面（清单 A2/A4：确认制时钟与失败历史）
type ContractRepo struct{ db *gorm.DB }

func NewContractRepo(db *gorm.DB) *ContractRepo { return &ContractRepo{db: db} }

// ListEnabled 全部启用契约（巡检循环按数据域遍历）
func (r *ContractRepo) ListEnabled() ([]model.DataContract, error) {
	var cs []model.DataContract
	err := r.db.Where("enabled = ?", true).Order("id").Find(&cs).Error
	return cs, err
}

// ByModelCode 数据域 → 最近更新的启用契约（判定侧新鲜度门槛读参，清单 A6）
func (r *ContractRepo) ByModelCode(code string) (*model.DataContract, error) {
	var c model.DataContract
	err := r.db.Where("model_code = ? AND enabled = ?", code, true).
		Order("updated_at desc").First(&c).Error
	if err != nil {
		return nil, err
	}
	return &c, nil
}

// UpsertContract 按 (app_id, model_code) 幂等落契约：字段/算法/承诺随声明更新；
// 已有契约保留确认制时钟与增量水位（改契约不等于数据变旧），新建以 now 起钟
func (r *ContractRepo) UpsertContract(in *model.DataContract) (*model.DataContract, error) {
	var existing model.DataContract
	err := r.db.Where("app_id = ? AND model_code = ?", in.AppID, in.ModelCode).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		now := time.Now()
		in.LastConfirmedFreshAt = &now
		in.Enabled = true
		return in, r.db.Create(in).Error
	}
	if err != nil {
		return nil, err
	}
	existing.Fields = in.Fields
	existing.Algorithm = in.Algorithm
	existing.StalenessSlaSec = in.StalenessSlaSec
	existing.DegradeMaxAgeSec = in.DegradeMaxAgeSec
	existing.Enabled = true
	// S5③：Updates(map) 显式列字段——Save 会把 37 行读入的旧时钟/旧水位整行回写，
	// 双副本/并发下绕过 TouchFresh/UpdateWatermark 的单调守卫（对抗审查 L-2 绕行路径）
	return &existing, r.db.Model(&existing).Updates(map[string]any{
		"fields":              existing.Fields,
		"algorithm":           existing.Algorithm,
		"staleness_sla_sec":   existing.StalenessSlaSec,
		"degrade_max_age_sec": existing.DegradeMaxAgeSec,
		"enabled":             true,
	}).Error
}

// TouchFresh 确认制时钟刷新（同步成功落地 或 指纹比对一致——清单 2.3.1 裁定①）
// S5② 单调守卫：只进不退——双副本竞态下旧值不允许覆写新时钟
func (r *ContractRepo) TouchFresh(id uint64, at time.Time) error {
	return r.db.Model(&model.DataContract{}).
		Where("id = ? AND (last_confirmed_fresh_at IS NULL OR last_confirmed_fresh_at < ?)", id, at).
		Update("last_confirmed_fresh_at", at).Error
}

// UpdateWatermark 增量水位推进——调用方保证批末语义：本批全部写成功后才调用（清单 A4 三句）
// S5① CAS：条件更新只允许单调前进，双副本竞态下旧水位写入自动失效（影响行数 0）
func (r *ContractRepo) UpdateWatermark(id uint64, at time.Time) error {
	return r.db.Model(&model.DataContract{}).
		Where("id = ? AND (sync_watermark_at IS NULL OR sync_watermark_at < ?)", id, at).
		Update("sync_watermark_at", at).Error
}

// CreatePatrolLog 写巡检失败历史（观测与告警分级进；判定只读状态机、不读本表）
func (r *ContractRepo) CreatePatrolLog(l *model.PatrolLog) error { return r.db.Create(l).Error }

// ListPatrolLogs 观测查询（验收/演示：reachable/match/sync_ok/fresh_age）
func (r *ContractRepo) ListPatrolLogs(limit int) ([]model.PatrolLog, error) {
	if limit <= 0 {
		limit = 20
	}
	var ls []model.PatrolLog
	err := r.db.Order("id desc").Limit(limit).Find(&ls).Error
	return ls, err
}
