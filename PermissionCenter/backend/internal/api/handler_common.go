package api

import (
	"context"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

// audit 写管理操作审计日志（谁改了什么）
func (d *Deps) audit(c *gin.Context, action, resType, resID string, detail map[string]any) {
	actor := uint64(0)
	if claims, ok := auth.ClaimsFrom(c); ok {
		if u, err := d.Users.ByUsername(claims.Username); err == nil {
			actor = u.ID
		}
	}
	go func() {
		d.Syncs.CreateAudit(&model.AuditLog{
			ActorID:      actor,
			Action:       action,
			ResourceType: resType,
			ResourceID:   resID,
			Detail:       detail,
			IP:           c.ClientIP(),
		})
	}()
}

// bumpAllCaches 全量使策略缓存失效 + 清决策缓存（demo 简化：变更即失效）
// 决策缓存 TTL 内生效 → 策略发布/变更后立即清空，保证强一致演示
func (d *Deps) bumpAllCaches(c *gin.Context) {
	ctx := context.Background()
	apps, _, err := d.Apps.List(0, 1000)
	if err != nil {
		return
	}
	for _, a := range apps {
		d.Builder.Bump(ctx, a.ID)
	}
	d.Cache.DelPattern(ctx, "authz:dec:*")
	d.Cache.DelPattern(ctx, "authz:pset:*")
}

// currentUserID 当前登录用户 id
func (d *Deps) currentUserID(c *gin.Context) uint64 {
	claims, ok := auth.ClaimsFrom(c)
	if !ok {
		return 0
	}
	u, err := d.Users.ByUsername(claims.Username)
	if err != nil {
		return 0
	}
	return u.ID
}

func timeNow() time.Time { return time.Now() }
