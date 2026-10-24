// Package api 观测端点：把后台黑盒（PEP 解析 / PIP 身份 / Agent / 分发 / 同步）显性化
package api

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/model"
)

// debugResolve PEP 解析工作台（B）：交互式展示 请求→action 的完整解析步骤 + 模拟决策
// POST /api/v1/debug/resolve {method, path, app, user, x_resource_type}
func (d *Deps) debugResolve(c *gin.Context) {
	var req struct {
		Method        string `json:"method"`
		Path          string `json:"path"`
		App           string `json:"app"`
		User          string `json:"user"`
		XResourceType string `json:"x_resource_type"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.Method == "" || req.Path == "" {
		c.JSON(400, gin.H{"error": "method/path required"})
		return
	}
	appCode := req.App
	if appCode == "" {
		appCode = "cmdb"
	}
	app, err := d.Apps.ByCode(appCode)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	trace := d.Access.ResolveActionSteps(app.ID, req.Method, req.Path, req.XResourceType)
	out := gin.H{
		"app":   gin.H{"code": app.Code, "name": app.Name},
		"trace": trace,
	}
	// 模拟决策（若解析出权限点且有主体）
	if trace.Action != nil && req.User != "" {
		dec, _, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
			User: req.User, App: appCode, Action: trace.Action.Code,
			Context: map[string]any{"ip": c.ClientIP()},
		})
		if err == nil {
			out["decision"] = dec
		}
	}
	c.JSON(200, out)
}

// debugPIP 身份解析图谱（C）：主体 → 组织/组/祖先链 → 组权限 → 个人策略
// GET /api/v1/debug/pip/:user
func (d *Deps) debugPIP(c *gin.Context) {
	user := c.Param("user")

	// 服务主体（M2M）
	if len(user) > 7 && user[:7] == "client:" {
		cid := user[7:]
		cli, err := d.Apps.ClientByID(cid)
		if err != nil {
			c.JSON(404, gin.H{"error": "client not found"})
			return
		}
		c.JSON(200, gin.H{
			"subject":      user,
			"subject_type": "service",
			"subject_key":  "s:" + cid,
			"client":       cli,
		})
		return
	}

	u, err := d.Users.ByUsername(user)
	if err != nil {
		c.JSON(404, gin.H{"error": "user not found"})
		return
	}
	// 直接隶属组 + 角色
	directGroups, _ := d.Groups.ByUserID(u.ID)
	var memberships []model.UserGroup
	d.DB.Where("user_id = ?", u.ID).Find(&memberships)
	roleByGroup := map[uint64]int16{}
	for _, m := range memberships {
		roleByGroup[m.GroupID] = m.Role
	}
	// 祖先链 closure（组层级传递）
	closureIDs, _ := d.Groups.MemberGroupIDs(u.ID)
	var closureGroups []model.Group
	if len(closureIDs) > 0 {
		d.DB.Where("id IN ?", closureIDs).Find(&closureGroups)
	}
	// 组权限点（org + custom）
	var gps []model.GroupPermission
	if len(closureIDs) > 0 {
		d.DB.Where("group_id IN ?", closureIDs).Find(&gps)
	}
	actionIDs := make([]uint64, 0, len(gps))
	for _, gp := range gps {
		actionIDs = append(actionIDs, gp.ActionID)
	}
	actions, _ := d.Access.ActionsByIDs(actionIDs)
	// 个人策略
	var ps []model.Policy
	d.DB.Where("subject_type = ? AND subject_id = ? AND status = ?",
		model.SubjectUser, u.ID, model.PolicyActive).Find(&ps)
	// （1.5 T3）OpenFGA 关系面板已随投影机制退役——数据级判定=点查权威行

	// 组装视图
	directView := make([]gin.H, 0, len(directGroups))
	for _, g := range directGroups {
		role := roleByGroup[g.ID]
		directView = append(directView, gin.H{
			"id": g.ID, "name": g.Name, "type": g.Type, "path": g.Path,
			"role": role, "role_name": map[int16]string{1: "成员", 2: "组长"}[role],
		})
	}
	closureView := make([]gin.H, 0, len(closureGroups))
	for _, g := range closureGroups {
		closureView = append(closureView, gin.H{"id": g.ID, "name": g.Name, "type": g.Type, "path": g.Path})
	}
	groupActionView := make([]gin.H, 0)
	groupActionByID := map[uint64][]uint64{}
	for _, gp := range gps {
		groupActionByID[gp.GroupID] = append(groupActionByID[gp.GroupID], gp.ActionID)
	}
	actionByID := map[uint64]model.Action{}
	for _, a := range actions {
		actionByID[a.ID] = a
	}
	for gid, aids := range groupActionByID {
		var g model.Group
		if err := d.DB.First(&g, gid).Error; err != nil {
			continue
		}
		var acts []model.Action
		for _, aid := range aids {
			if a, ok := actionByID[aid]; ok {
				acts = append(acts, a)
			}
		}
		groupActionView = append(groupActionView, gin.H{"group_id": gid, "group_name": g.Name, "actions": acts})
	}

	c.JSON(200, gin.H{
		"subject":          u.Username,
		"subject_type":     "user",
		"subject_key":      "u:" + strconv.FormatUint(u.ID, 10),
		"user":             u,
		"direct_groups":    directView,
		"ancestor_chain":   closureView,
		"group_actions":    groupActionView,
		"personal_policies": d.decoratePolicies(ps),

	})
}

// listAgents Agent 下发工作台（D）：在线状态 + 本地/中心 bundle 版本对比 + 决策量
// GET /api/v1/agents
func (d *Deps) listAgents(c *gin.Context) {
	ss, err := d.Syncs.AgentStatuses()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	latestByApp := map[uint64]*model.Bundle{}
	appNameByID := map[uint64]string{}
	items := make([]gin.H, 0, len(ss))
	now := time.Now()
	for _, s := range ss {
		latest, ok := latestByApp[s.AppID]
		if !ok {
			latest, _ = d.Syncs.LatestBundle(s.AppID)
			if latest != nil {
				latestByApp[s.AppID] = latest
			}
		}
		name, ok := appNameByID[s.AppID]
		if !ok {
			if app, err := d.Apps.ByID(s.AppID); err == nil {
				name = app.Name
			}
			appNameByID[s.AppID] = name
		}
		online := s.LastSeenAt != nil && now.Sub(*s.LastSeenAt) < 30*time.Second
		behind := latest != nil && s.CurrentRev < latest.Revision
		items = append(items, gin.H{
			"agent_id":       s.AgentID,
			"app_id":         s.AppID,
			"app_name":       name,
			"online":         online,
			"current_rev":    s.CurrentRev,
			"latest_rev":     func() *int64 { if latest != nil { v := latest.Revision; return &v }; return nil }(),
			"behind":         behind,
			"last_seen_at":   s.LastSeenAt,
			"decision_count": s.DecisionCount,
			"hit_rate":       s.HitRate,
		})
	}
	c.JSON(200, gin.H{"items": items, "now": now})
}

// listBundles 策略分发版本记录（E）+ 内容概要（G4：bundle 内容展开）
// GET /api/v1/apps/:id/bundles
func (d *Deps) listBundles(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	bs, err := d.Syncs.Bundles(appID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	items := make([]gin.H, 0, len(bs))
	for _, b := range bs {
		policyCount := 0
		groupingCount := 0
		preview := []gin.H{}
		forceRemote := []string{}
		if content, ok := b.Content["policies"].([]any); ok {
			policyCount = len(content)
			// 内容概要（前 20 条：subject/app/actions/effect）
			for i, raw := range content {
				if i >= 20 {
					break
				}
				if p, ok := raw.(map[string]any); ok {
					preview = append(preview, gin.H{
						"subject_key": p["subject_key"],
						"app_code":    p["app_code"],
						"actions":     p["actions"],
						"effect":      p["effect"],
					})
				}
			}
		}
		if content, ok := b.Content["groupings"].([]any); ok {
			groupingCount = len(content)
		}
		if fr, ok := b.Content["force_remote"].([]any); ok {
			for _, x := range fr {
				if s, ok := x.(string); ok {
					forceRemote = append(forceRemote, s)
				}
			}
		}
		items = append(items, gin.H{
			"id": b.ID, "revision": b.Revision, "checksum": b.Checksum,
			"published_by": b.PublishedBy, "created_at": b.CreatedAt,
			"policy_count": policyCount, "grouping_count": groupingCount,
			"policy_preview": preview, "force_remote": forceRemote,
		})
	}
	c.JSON(200, gin.H{"items": items})
}

// debugCache 决策缓存工作台（G1）：authz:dec:* / authz:pset:* 键 + 命中率 + 手动失效
// GET /api/v1/debug/cache
func (d *Deps) debugCache(c *gin.Context) {
	ctx := c.Request.Context()
	decEntries, _ := d.Cache.ScanPattern(ctx, "authz:dec:*", 200)
	psetCount, _ := d.Cache.CountPattern(ctx, "authz:pset:*")
	summary, _ := d.Syncs.DecisionSummary()
	sourceDist := map[string]int64{}
	if s, ok := summary["source_dist"].(map[string]int64); ok {
		sourceDist = s
	}
	total, _ := summary["total"].(int64)
	hit := sourceDist["cache"]
	hitRate := 0.0
	if total > 0 {
		hitRate = float64(hit) / float64(total) * 100
	}
	c.JSON(200, gin.H{
		"dec_count":       len(decEntries),
		"pset_count":      psetCount,
		"decision_total":  total,
		"cache_hits":      hit,
		"hit_rate_pct":    hitRate,
		"entries":         decEntries,
	})
}

// debugCacheClear 清空决策缓存（运维排障：策略变更不生效时一键失效）
// POST /api/v1/debug/cache/clear
func (d *Deps) debugCacheClear(c *gin.Context) {
	ctx := c.Request.Context()
	n, _ := d.Cache.CountPattern(ctx, "authz:dec:*")
	if err := d.Cache.DelPattern(ctx, "authz:dec:*"); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"cleared": n, "ok": true})
}

// debugMetrics 鉴权指标面板（G2）：决策量/allow/deny/来源分布/延迟百分位/趋势/Top 动作
// GET /api/v1/debug/metrics
func (d *Deps) debugMetrics(c *gin.Context) {
	summary, _ := d.Syncs.DecisionSummary()
	trend := d.Syncs.DecisionTrend(24)
	topActions := d.Syncs.DecisionByAction(10)
	c.JSON(200, gin.H{"summary": summary, "trend": trend, "top_actions": topActions})
}

// debugOwners owner 巡检视图（G4，只读）：失联提醒中的 owner + 已停用应用
// GET /api/v1/debug/owners
func (d *Deps) debugOwners(c *gin.Context) {
	var owners []model.AppOwner
	d.DB.Where("remind_count > 0").Find(&owners)
	items := []gin.H{}
	for _, o := range owners {
		app, err := d.Apps.ByID(o.AppID)
		if err != nil {
			continue
		}
		un, dn := "", ""
		if u, err := d.Users.ByID(o.UserID); err == nil {
			un, dn = u.Username, u.DisplayName
		}
		items = append(items, gin.H{
			"app_id": o.AppID, "app_code": app.Code, "app_name": app.Name,
			"app_status": app.Status, "disabled": app.Status == model.StatusDisabled,
			"owner_id": o.UserID, "owner_name": dn, "owner_username": un,
			"remind_count": o.RemindCount, "is_primary": o.IsPrimary,
		})
	}
	c.JSON(200, gin.H{"items": items, "total": len(items)})
}

// listSyncJobs 同步任务工作台（F）
// GET /api/v1/sync-jobs
func (d *Deps) listSyncJobs(c *gin.Context) {
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	js, total, err := d.Syncs.Jobs(offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	typeNames := map[int16]string{
		model.SyncOpenAPI: "OpenAPI 同步", model.SyncCMDBModel: "CMDB 模型同步",
		model.SyncCMDBInst: "CMDB 实例同步", model.SyncIdentity: "身份源同步",
	}
	statusNames := map[int16]string{0: "失败", 1: "运行中", 2: "成功"}
	items := make([]gin.H, 0, len(js))
	for _, j := range js {
		dur := ""
		if j.StartedAt != nil && j.FinishedAt != nil {
			dur = j.FinishedAt.Sub(*j.StartedAt).Round(time.Millisecond).String()
		}
		items = append(items, gin.H{
			"id": j.ID, "type": j.Type, "type_name": typeNames[j.Type],
			"status": j.Status, "status_name": statusNames[j.Status],
			"started_at": j.StartedAt, "finished_at": j.FinishedAt,
			"duration": dur, "result": j.Result,
		})
	}
	c.JSON(200, gin.H{"items": items, "total": total})
}
