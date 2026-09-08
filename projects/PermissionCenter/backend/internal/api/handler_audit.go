package api

import (
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

func (d *Deps) listAuditLogs(c *gin.Context) {
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	ls, total, err := d.Syncs.AuditLogs(offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": ls, "total": total})
}

func (d *Deps) listDecisionLogs(c *gin.Context) {
	// 链路视图：按 trace_id 展开一次请求的全部决策
	if traceID := c.Query("trace_id"); traceID != "" {
		ls, err := d.Syncs.DecisionLogsByTrace(traceID)
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		c.JSON(200, gin.H{"items": ls, "total": len(ls)})
		return
	}
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	ls, total, err := d.Syncs.DecisionLogs(offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": ls, "total": total})
}

// auditMyRequests 我的申请（FR-8）：我发起的全部申请 + 审批链
func (d *Deps) auditMyRequests(c *gin.Context) {
	uid := d.currentUserID(c)
	var rs []model.AccessRequest
	d.DB.Where("applicant_id = ?", uid).Order("id desc").Find(&rs)
	out := make([]gin.H, 0, len(rs))
	for _, r := range rs {
		out = append(out, d.requestView(&r))
	}
	c.JSON(200, gin.H{"items": out})
}

// auditMyApprovals 我的审批（FR-8）：待我审批 + 我审批过的
func (d *Deps) auditMyApprovals(c *gin.Context) {
	uid := d.currentUserID(c)
	var rs []model.AccessRequest
	d.DB.Where("status = ?", model.ReqPending).Order("id desc").Find(&rs)
	pending := make([]gin.H, 0)
	for _, r := range rs {
		app, err := d.Apps.ByID(r.AppID)
		if err != nil {
			continue
		}
		chain := d.buildApprovalChain(&r, app, r.ApplicantID)
		if d.inChain(uid, chain) {
			pending = append(pending, d.requestView(&r))
		}
	}
	// 我审批过的（ApprovalTask 有记录）
	var taskIDs []uint64
	d.DB.Model(&model.ApprovalTask{}).Where("approver_id = ?", uid).Distinct("request_id").Pluck("request_id", &taskIDs)
	var done []gin.H
	if len(taskIDs) > 0 {
		var rs2 []model.AccessRequest
		d.DB.Where("id IN ?", taskIDs).Order("id desc").Find(&rs2)
		for _, r := range rs2 {
			done = append(done, d.requestView(&r))
		}
	}
	c.JSON(200, gin.H{"pending": pending, "done": done})
}

// auditMyPublishes 我的发布（FR-8）：我发布的策略 / 模板 / 授权记录
func (d *Deps) auditMyPublishes(c *gin.Context) {
	uid := d.currentUserID(c)
	// 策略（含授权记录）
	var ps []model.Policy
	d.DB.Where("created_by = ?", uid).Order("id desc").Limit(100).Find(&ps)
	var pols []gin.H
	for _, p := range ps {
		pols = append(pols, gin.H{
			"id": p.ID, "type": "policy", "name": p.Name,
			"app_id": p.AppID, "source": p.Source,
			"created_at": p.CreatedAt, "status": p.Status,
		})
	}
	// 策略模板
	var ts []model.PolicyTemplate
	d.DB.Where("published_by = ?", uid).Order("id desc").Find(&ts)
	var tpls []gin.H
	for _, t := range ts {
		tpls = append(tpls, gin.H{
			"id": t.ID, "type": "template", "name": t.Name,
			"app_id": t.AppID, "created_at": t.CreatedAt,
			"status": t.Status, "apply_count": t.ApplyCount,
		})
	}
	// 能力声明
	var caps []model.CapabilityManifest
	d.DB.Where("created_by = ? OR updated_by = ?", uid, uid).Order("id desc").Find(&caps)
	var capViews []gin.H
	for _, m := range caps {
		capViews = append(capViews, gin.H{
			"id": m.ID, "type": "capability", "name": m.Name,
			"app_id": m.AppID, "created_at": m.CreatedAt,
			"status": m.Status, "version": m.Version,
		})
	}
	c.JSON(200, gin.H{"policies": pols, "templates": tpls, "capabilities": capViews})
}

// requestView 申请单展示视图（含审批链）
func (d *Deps) requestView(r *model.AccessRequest) gin.H {
	v := gin.H{
		"id": r.ID, "app_id": r.AppID, "applicant_id": r.ApplicantID,
		"request_type":           r.RequestType, // 1=自助申请 2=owner 授权
		"applicant_subject_type": r.ApplicantSubjectType,
		"applicant_subject_id":   r.ApplicantSubjectID,
		"content":                r.Content,
		"items":                  r.Items,
		"reason":                 r.Reason, // 授权理由 / 申请说明
		"risk_level":             r.RiskLevel,
		"status":                 r.Status,
		"expires_at":             r.ExpiresAt,
		"created_at":             r.CreatedAt,
	}
	appName, appCode := "", ""
	if app, err := d.Apps.ByID(r.AppID); err == nil {
		appName, appCode = app.Name, app.Code
	}
	v["app_name"] = appName
	v["app_code"] = appCode
	applicantName := ""
	if u, err := d.Users.ByID(r.ApplicantID); err == nil {
		applicantName = u.DisplayName
	}
	v["applicant_name"] = applicantName
	// 审批链
	app, _ := d.Apps.ByID(r.AppID)
	chain := d.buildApprovalChain(r, app, r.ApplicantID)
	var chainView []gin.H
	for _, id := range chain {
		name := ""
		if u, err := d.Users.ByID(id); err == nil {
			name = u.DisplayName
		}
		chainView = append(chainView, gin.H{"id": id, "name": name})
	}
	v["approval_chain"] = chainView
	// 审批记录
	var tasks []model.ApprovalTask
	d.DB.Where("request_id = ?", r.ID).Order("step").Find(&tasks)
	v["approvals"] = tasks
	return v
}

// handleBundle agent 拉取策略包（带当前版本，无更新返回 304）
func (d *Deps) handleBundle(c *gin.Context) {
	appCode := c.Param("app")
	currentRev, _ := strconv.ParseInt(c.DefaultQuery("rev", "0"), 10, 64)
	b, updated, err := d.BundleMgr.Fetch(c.Request.Context(), appCode, currentRev)
	if err != nil {
		c.JSON(404, gin.H{"error": err.Error()})
		return
	}
	if !updated || b == nil {
		c.Status(304)
		return
	}
	c.JSON(200, gin.H{
		"revision": b.Revision,
		"checksum": b.Checksum,
		"content":  b.Content,
	})
}

// handleAgentStatus agent 状态上报（升级率/存活监控）
func (d *Deps) handleAgentStatus(c *gin.Context) {
	var req struct {
		AgentID        string  `json:"agent_id"`
		AppID          uint64  `json:"app_id"`
		CurrentRev     int64   `json:"current_rev"`
		DecisionCount  int64   `json:"decision_count"`
		HitRate        float64 `json:"hit_rate"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	now := timeNow()
	if err := d.Syncs.UpsertAgentStatus(&model.AgentStatus{
		AgentID:       req.AgentID,
		AppID:         req.AppID,
		CurrentRev:    req.CurrentRev,
		LastSeenAt:    &now,
		DecisionCount: req.DecisionCount,
		HitRate:       req.HitRate,
	}); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}
