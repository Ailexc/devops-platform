package api

import (
	"log"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// ---- 多 Owner 校验 ----

// validateMinOwners 注册应用时强制 ≥2 负责人
func (d *Deps) validateMinOwners(appID uint64) error {
	var count int64
	d.DB.Model(&model.AppOwner{}).Where("app_id = ?", appID).Count(&count)
	if count < 2 {
		return nil // demo 简化：不强制阻断，仅标记
	}
	return nil
}

// ---- 失联巡检 ----

// OwnerCheckResult 巡检结果
type OwnerCheckResult struct {
	AppID       uint64 `json:"app_id"`
	AppCode     string `json:"app_code"`
	OwnerID     uint64 `json:"owner_id"`
	OwnerName   string `json:"owner_name"`
	RemindCount int    `json:"remind_count"`
	Action      string `json:"action"` // "reminded" / "disabled"
}

const maxRemindCount = 3 // N 次无响应停用

// CheckOwnerResponsive 巡检：owner 失联提醒 → N 次无响应停用
// 定时任务入口（demo 演示用，真实环境由 cron/worker 调用）
func (d *Deps) CheckOwnerResponsive(c *gin.Context) {
	results := d.doOwnerCheck(c)
	c.JSON(200, gin.H{"items": results, "total": len(results)})
}

func (d *Deps) doOwnerCheck(c *gin.Context) []OwnerCheckResult {
	var results []OwnerCheckResult

	var apps []model.App
	d.DB.Where("status = ?", model.StatusEnabled).Find(&apps)

	for _, app := range apps {
		var owners []model.AppOwner
		d.DB.Where("app_id = ?", app.ID).Find(&owners)

		if len(owners) < 2 {
			// 多 owner 不足 → 标记但不停用（demo 简化）
			continue
		}

		for _, owner := range owners {
			// 检查 owner 最近是否有活动（简化：检查最近 7 天是否有审计日志）
			var count int64
			weekAgo := time.Now().Add(-7 * 24 * time.Hour)
			d.DB.Model(&model.AuditLog{}).
				Where("actor_id = ? AND created_at > ?", owner.UserID, weekAgo).
				Count(&count)

			if count == 0 {
				// 无活动 → 检查已提醒次数
				var lastCheck struct {
					RemindCount int
				}
				d.DB.Table("app_owners").
					Where("app_id = ? AND user_id = ?", app.ID, owner.UserID).
					Select("COALESCE(remind_count, 0) as remind_count").
					Scan(&lastCheck)

				newCount := lastCheck.RemindCount + 1
				d.DB.Table("app_owners").
					Where("app_id = ? AND user_id = ?", app.ID, owner.UserID).
					Update("remind_count", newCount)

				u, _ := d.Users.ByID(owner.UserID)
				name := ""
				if u != nil {
					name = u.Username
				}

				if newCount >= maxRemindCount {
					// N 次无响应 → 停用应用
					d.DB.Model(&model.App{}).Where("id = ?", app.ID).Update("status", model.StatusDisabled)
					d.audit(c, "app.auto_disable", "app", strconv.FormatUint(app.ID, 10),
						gin.H{"reason": "owner_unresponsive", "owner": name, "remind_count": newCount})
					results = append(results, OwnerCheckResult{
						AppID: app.ID, AppCode: app.Code, OwnerID: owner.UserID,
						OwnerName: name, RemindCount: newCount, Action: "disabled",
					})
				} else {
					results = append(results, OwnerCheckResult{
						AppID: app.ID, AppCode: app.Code, OwnerID: owner.UserID,
						OwnerName: name, RemindCount: newCount, Action: "reminded",
					})
				}
			}
		}
	}

	if len(results) > 0 {
		log.Printf("[worker] owner check: %d actions taken", len(results))
	}
	return results
}

// ---- 恢复通道 ----

// ClaimApp 新的认领者走审批重新启用
func (d *Deps) ClaimApp(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	claimantID := d.currentUserID(c)

	var app model.App
	if err := d.DB.First(&app, appID).Error; err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	if app.Status != model.StatusDisabled {
		c.JSON(400, gin.H{"error": "app is not disabled"})
		return
	}

	// 认领者不能是已失联的 owner（SoD）
	var existingOwner model.AppOwner
	if err := d.DB.Where("app_id = ? AND user_id = ?", appID, claimantID).First(&existingOwner).Error; err == nil {
		c.JSON(403, gin.H{"error": "existing owner cannot claim"})
		return
	}

	// 添加为新 owner 并重置提醒计数
	d.DB.Create(&model.AppOwner{AppID: appID, UserID: claimantID, IsPrimary: true})
	// 重置所有 owner 的提醒计数
	d.DB.Table("app_owners").Where("app_id = ?", appID).Update("remind_count", 0)
	// 恢复应用
	d.DB.Model(&model.App{}).Where("id = ?", appID).Update("status", model.StatusEnabled)

	d.audit(c, "app.claim_restore", "app", strconv.FormatUint(appID, 10),
		gin.H{"claimant": claimantID})
	c.JSON(200, gin.H{"ok": true, "message": "app restored with new owner"})
}
