package store

import (
	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

type SyncRepo struct{ db *gorm.DB }

func NewSyncRepo(db *gorm.DB) *SyncRepo { return &SyncRepo{db: db} }

func (r *SyncRepo) CreateJob(j *model.SyncJob) error { return r.db.Create(j).Error }
func (r *SyncRepo) FinishJob(id uint64, status int16, result map[string]any) error {
	return r.db.Model(&model.SyncJob{}).Where("id = ?", id).
		Updates(map[string]any{"status": status, "finished_at": gorm.Expr("now()"), "result": result}).Error
}
func (r *SyncRepo) Jobs(offset, limit int) ([]model.SyncJob, int64, error) {
	var total int64
	r.db.Model(&model.SyncJob{}).Count(&total)
	var js []model.SyncJob
	if err := r.db.Order("id desc").Offset(offset).Limit(limit).Find(&js).Error; err != nil {
		return nil, 0, err
	}
	return js, total, nil
}

// Bundle 相关
func (r *SyncRepo) LatestBundle(appID uint64) (*model.Bundle, error) {
	var b model.Bundle
	if err := r.db.Where("app_id = ?", appID).Order("revision desc").First(&b).Error; err != nil {
		return nil, err
	}
	return &b, nil
}

func (r *SyncRepo) CreateBundle(b *model.Bundle) error { return r.db.Create(b).Error }

// Bundles 应用的分发版本历史（revision 升序）
func (r *SyncRepo) Bundles(appID uint64) ([]model.Bundle, error) {
	var bs []model.Bundle
	if err := r.db.Where("app_id = ?", appID).Order("revision").Find(&bs).Error; err != nil {
		return nil, err
	}
	return bs, nil
}

// AgentStatus 相关
func (r *SyncRepo) UpsertAgentStatus(s *model.AgentStatus) error {
	var existing model.AgentStatus
	err := r.db.Where("agent_id = ?", s.AgentID).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		return r.db.Create(s).Error
	}
	if err != nil {
		return err
	}
	existing.AppID = s.AppID
	existing.CurrentRev = s.CurrentRev
	existing.LastSeenAt = s.LastSeenAt
	existing.DecisionCount = s.DecisionCount
	existing.HitRate = s.HitRate
	return r.db.Save(&existing).Error
}

func (r *SyncRepo) AgentStatuses() ([]model.AgentStatus, error) {
	var ss []model.AgentStatus
	if err := r.db.Order("last_seen_at desc").Find(&ss).Error; err != nil {
		return nil, err
	}
	return ss, nil
}

// Audit / Decision 日志
func (r *SyncRepo) CreateAudit(a *model.AuditLog) error   { return r.db.Create(a).Error }
func (r *SyncRepo) CreateDecision(d *model.DecisionLog) error { return r.db.Create(d).Error }

func (r *SyncRepo) AuditLogs(offset, limit int) ([]model.AuditLog, int64, error) {
	var total int64
	r.db.Model(&model.AuditLog{}).Count(&total)
	var ls []model.AuditLog
	if err := r.db.Order("id desc").Offset(offset).Limit(limit).Find(&ls).Error; err != nil {
		return nil, 0, err
	}
	return ls, total, nil
}

func (r *SyncRepo) DecisionLogs(offset, limit int) ([]model.DecisionLog, int64, error) {
	var total int64
	r.db.Model(&model.DecisionLog{}).Count(&total)
	var ls []model.DecisionLog
	if err := r.db.Order("id desc").Offset(offset).Limit(limit).Find(&ls).Error; err != nil {
		return nil, 0, err
	}
	return ls, total, nil
}

// DecisionLogsByTrace 按链路 ID 查询（一次请求的全部分步决策）
func (r *SyncRepo) DecisionLogsByTrace(traceID string) ([]model.DecisionLog, error) {
	var ls []model.DecisionLog
	if err := r.db.Where("trace_id = ?", traceID).Order("id").Find(&ls).Error; err != nil {
		return nil, err
	}
	return ls, nil
}

// DecisionSummary 鉴权指标汇总：总量 / allow / deny / 来源分布（cache/remote/local）
func (r *SyncRepo) DecisionSummary() (map[string]any, error) {
	out := map[string]any{}
	var total int64
	r.db.Model(&model.DecisionLog{}).Count(&total)
	out["total"] = total
	var allow, deny int64
	r.db.Model(&model.DecisionLog{}).Where("decision = ?", model.DecisionAllow).Count(&allow)
	r.db.Model(&model.DecisionLog{}).Where("decision = ?", model.DecisionDeny).Count(&deny)
	out["allow"] = allow
	out["deny"] = deny
	// 来源分布：PEP jsonb 的 from 字段（cache / remote / local）
	type row struct {
		From  string `gorm:"column:from"`
		Count int64  `gorm:"column:cnt"`
	}
	var rows []row
	r.db.Model(&model.DecisionLog{}).
		Select("COALESCE(pep->>'from', '') as from, count(*) as cnt").
		Group("pep->>'from'").Scan(&rows)
	dist := map[string]int64{}
	for _, rw := range rows {
		if rw.From == "" {
			rw.From = "remote"
		}
		dist[rw.From] += rw.Count
	}
	out["source_dist"] = dist
	// 延迟百分位（P50/P90/P95）
	pcts := map[string]float64{"p50": 50, "p90": 90, "p95": 95}
	for name, p := range pcts {
		out[name] = r.decisionPercentile(p)
	}
	return out, nil
}

// decisionPercentile 延迟百分位（近似：ORDER BY + LIMIT 偏移）
func (r *SyncRepo) decisionPercentile(p float64) int64 {
	var total int64
	r.db.Model(&model.DecisionLog{}).Count(&total)
	if total == 0 {
		return 0
	}
	offset := int(float64(total) * p / 100)
	if offset >= int(total) {
		offset = int(total) - 1
	}
	var ms int64
	r.db.Model(&model.DecisionLog{}).Order("latency_ms").Offset(offset).Limit(1).Pluck("latency_ms", &ms)
	return ms
}

// DecisionTrend 最近 N 小时决策趋势（按小时分组：量 / allow / deny）
func (r *SyncRepo) DecisionTrend(hours int) []map[string]any {
	if hours <= 0 {
		hours = 24
	}
	type row struct {
		Hour  string `gorm:"column:hr"`
		Total int64  `gorm:"column:total"`
		Allow int64  `gorm:"column:allow"`
		Deny  int64  `gorm:"column:deny"`
	}
	var rows []row
	r.db.Raw(`
		SELECT to_char(date_trunc('hour', created_at), 'YYYY-MM-DD HH24') AS hr,
		       count(*) AS total,
		       count(*) FILTER (WHERE decision = 1) AS allow,
		       count(*) FILTER (WHERE decision = 2) AS deny
		FROM decision_logs
		WHERE created_at > now() - interval '1 hour' * ?
		GROUP BY 1 ORDER BY 1`, hours).Scan(&rows)
	out := make([]map[string]any, 0, len(rows))
	for _, rw := range rows {
		out = append(out, map[string]any{
			"hour": rw.Hour, "total": rw.Total, "allow": rw.Allow, "deny": rw.Deny,
		})
	}
	return out
}

// DecisionByAction 决策按权限点分布（Top N）
func (r *SyncRepo) DecisionByAction(limit int) []map[string]any {
	if limit <= 0 {
		limit = 10
	}
	type row struct {
		Action string `gorm:"column:action"`
		Total  int64  `gorm:"column:total"`
	}
	var rows []row
	r.db.Model(&model.DecisionLog{}).Select("action, count(*) as total").
		Group("action").Order("total desc").Limit(limit).Scan(&rows)
	out := make([]map[string]any, 0, len(rows))
	for _, rw := range rows {
		out = append(out, map[string]any{"action": rw.Action, "total": rw.Total})
	}
	return out
}
