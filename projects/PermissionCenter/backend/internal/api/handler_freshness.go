package api

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// listDataContracts 数据契约与确认制时钟观测（清单 A2/A4 验收与演示入口：
// 字段/算法/新鲜度承诺/last_confirmed_fresh_at/sync_watermark_at 一目了然）
func (d *Deps) listDataContracts(c *gin.Context) {
	cs, err := d.Contracts.ListEnabled()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": cs})
}

// listPatrolLogs 巡检失败历史（观测与告警分级进；判定只读状态机、不读本表——清单 2.3.1 分工）
func (d *Deps) listPatrolLogs(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))
	ls, err := d.Contracts.ListPatrolLogs(limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": ls})
}

// reconcileNow 手动触发深对账（清单 A5b：演示与验收入口——
// 全量三类差异：常规更新 upsert / 孤儿双侧清理（PG+OpenFGA）/ 静默漂移告警）
func (d *Deps) reconcileNow(c *gin.Context) {
	summary := d.Patrol.ReconcileOnce(c.Request.Context())
	d.audit(c, "sync.reconcile", "reconcile", "manual", gin.H{"summary": summary})
	c.JSON(200, gin.H{"ok": true, "summary": summary})
}

// freshnessGate 数据新鲜度门槛（清单 2.3.1 判定侧读参）：
// 无契约 / 数据域无投影 → fresh（未接契约的域不做门槛，与巡检跳过同款理由）；
// 有契约 → 确认制状态机三态（fresh / degraded / expired）
func (d *Deps) freshnessGate(domain string) string {
	if d.Contracts == nil {
		return model.FreshStateFresh
	}
	if _, err := d.Res.ModelByCode(domain); err != nil {
		return model.FreshStateFresh
	}
	dc, err := d.Contracts.ByModelCode(domain)
	if err != nil || dc == nil {
		return model.FreshStateFresh
	}
	_, st := dc.Freshness(time.Now())
	return st
}

// matchedForceRemote 命中策略中是否存在 force-remote 标记
// （与 §5.7 策略分发同一标记合流——数据级挂接=本轮新增行为，清单 2.3 强一致档）
func (d *Deps) matchedForceRemote(matchedPids []string) bool {
	for _, pid := range matchedPids {
		id, err := strconv.ParseUint(pid, 10, 64)
		if err != nil {
			continue
		}
		if p, err := d.Pol.ByID(id); err == nil && p.ForceRemote {
			return true
		}
	}
	return false
}
