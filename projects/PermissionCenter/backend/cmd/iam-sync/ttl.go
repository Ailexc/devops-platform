package main

import (
	"context"
	"log"
	"time"

	"github.com/xcy/permission-center/internal/api"
	"github.com/xcy/permission-center/internal/model"
)

// ttlSweepLoop 策略级 TTL 到期回收（清单 A8 生效链——原实现只有 expires_at 字段，
// 既无判定过滤也无回收，"直授必须带 TTL"是空话；本循环补"回收语义"半段）：
//
//   - 判定侧过滤由 ActiveByApp 查询承担（expires_at IS NULL OR > now → builder/enforcer/matchedPids/bundle 全链源头排除）
//   - 本循环：置状态失效（status=0，权限列表不再展示）+ 清 OpenFGA 关系元组（复用 RevokePolicy，幂等）
//   - agent bundle 重发布（旧快照含过期策略 → Publish 重建）
//   - 周期 60s；配合 builder 缓存（PolicyCacheTTL=30s）→ 过期后判定最长 ~90s 内完全消失
func ttlSweepLoop(ctx context.Context, deps *api.Deps) {
	t := time.NewTicker(60 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			// S4 第四执行点：ttl 单活锁（周期 60s → 锁 TTL 30s）；逐轮 recover 与 defer 释放在 runLocked 内
			runLocked(ctx, deps, lockTTL, 30*time.Second, "ttl sweep", func() {
				var expired []model.Policy
				if err := deps.DB.Where("status = ? AND expires_at IS NOT NULL AND expires_at <= now()",
					model.PolicyActive).Find(&expired).Error; err != nil {
					log.Printf("[ttl] sweep query: %v", err)
					return // 原 continue——闭包内跳过本轮
				}
				for i := range expired {
					p := &expired[i]
					if err := deps.DataPlane.RevokePolicy(ctx, p); err != nil {
						// S6②：出错不置 status=0——否则 OFGA 瞬断窗口下元组残留 + status 已死
						// → 查询条件 status=active 永远捞不到它 = 永不再扫；保持 active 下轮重扫
						log.Printf("[ttl] revoke %s: %v（OFGA 失败——保持 active 下轮重扫）", p.Name, err)
						continue
					}
					// S6③：status 守卫（防并发双副本重复回收）——已回收的影响行数=0 直接跳过
					res := deps.DB.Model(&model.Policy{}).
						Where("id = ? AND status = ?", p.ID, model.PolicyActive).
						Update("status", 0)
					if res.Error != nil {
						log.Printf("[ttl] deactivate %s: %v", p.Name, res.Error)
						continue
					}
					if res.RowsAffected == 0 {
						continue // 并发副本已回收
					}
					p.Status = 0
					if _, err := deps.BundleMgr.Publish(ctx, p.AppID); err != nil {
						log.Printf("[ttl] rebundle app %d: %v", p.AppID, err)
					}
					log.Printf("[ttl] expired policy reclaimed: %s（tuples 已清、bundle 已重发布）", p.Name)
				}
			})
		}
	}
}
