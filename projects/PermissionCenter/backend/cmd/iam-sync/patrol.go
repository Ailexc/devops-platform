package main

import (
	"context"
	"log"
	"time"

	"github.com/xcy/permission-center/internal/api"
)

// patrolLoop 数据契约巡检 + 深对账双定时循环（清单 A4/A5b）
//
// 配置：PATROL_INTERVAL（默认 5m；demo 10s → 分钟级演示新鲜度三态）
//
//	RECONCILE_INTERVAL（默认 24h；demo 另有手动 POST /api/v1/sync/reconcile 触发口）
//
// 语义细节全部在 PatrolService 内：确认制时钟（同步落地/指纹一致才刷新）、
// 水位批末推进、失败历史 patrol_log、recovery 跃迁、孤儿双侧清理与静默漂移告警。
func patrolLoop(ctx context.Context, deps *api.Deps) {
	interval := deps.Cfg.PatrolInterval
	if interval <= 0 {
		interval = 5 * time.Minute
	}
	recon := deps.Cfg.ReconcileInterval
	if recon <= 0 {
		recon = 24 * time.Hour
	}
	patrolT := time.NewTicker(interval)
	reconT := time.NewTicker(recon)
	defer patrolT.Stop()
	defer reconT.Stop()
	// 启动即巡检一轮（S4 四执行点之一）：契约时钟立刻起跑（避免 seed 后到首轮 tick 之间的年龄被误读）；
	// 抢不到锁直接跳过（另一副本刚跑过），不阻塞启动
	runLocked(ctx, deps, lockPatrol, interval/2, "startup", func() {
		deps.Patrol.PatrolOnce(ctx)
	})
	for {
		select {
		case <-ctx.Done():
			return
		case <-patrolT.C:
			runLocked(ctx, deps, lockPatrol, interval/2, "patrol tick", func() {
				deps.Patrol.PatrolOnce(ctx)
			})
		case <-reconT.C:
			runLocked(ctx, deps, lockReconcile, deps.Cfg.ReconcileLockTTL, "reconcile tick", func() {
				summary := deps.Patrol.ReconcileOnce(ctx)
				log.Printf("[patrol] scheduled reconcile done: %d domains", len(summary))
			})
		}
	}
}
