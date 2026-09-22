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
			var expired []model.Policy
			if err := deps.DB.Where("status = ? AND expires_at IS NOT NULL AND expires_at <= now()",
				model.PolicyActive).Find(&expired).Error; err != nil {
				log.Printf("[ttl] sweep query: %v", err)
				continue
			}
			for i := range expired {
				p := &expired[i]
				if err := deps.DataPlane.RevokePolicy(ctx, p); err != nil {
					log.Printf("[ttl] revoke tuples %s: %v", p.Name, err)
				}
				p.Status = 0
				if err := deps.DB.Save(p).Error; err != nil {
					log.Printf("[ttl] deactivate %s: %v", p.Name, err)
					continue
				}
				if _, err := deps.BundleMgr.Publish(ctx, p.AppID); err != nil {
					log.Printf("[ttl] rebundle app %d: %v", p.AppID, err)
				}
				log.Printf("[ttl] expired policy reclaimed: %s（tuples 已清、bundle 已重发布）", p.Name)
			}
		}
	}
}
