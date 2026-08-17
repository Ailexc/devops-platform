package api

import (
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

type groupReq struct {
	Name     string  `json:"name"`
	ParentID *uint64 `json:"parent_id"`
	Type     int16   `json:"type"` // 1=org 2=custom
}

// createGroup 创建组，应用层维护物化路径 path（/父/子/）
func (d *Deps) createGroup(c *gin.Context) {
	var req groupReq
	if err := c.ShouldBindJSON(&req); err != nil || req.Name == "" {
		c.JSON(400, gin.H{"error": "name required"})
		return
	}
	gtype := req.Type
	if gtype == 0 {
		gtype = model.GroupTypeCustom
	}
	g := &model.Group{Name: req.Name, ParentID: req.ParentID, Type: gtype, Source: model.SourceLocal}
	if err := d.Groups.Create(g); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	// 物化路径依赖自身 id，创建后回填
	path := "/" + strconv.FormatUint(g.ID, 10) + "/"
	if req.ParentID != nil {
		if parent, err := d.Groups.ByID(*req.ParentID); err == nil {
			path = parent.Path + strconv.FormatUint(g.ID, 10) + "/"
		}
	}
	g.Path = path
	d.Groups.Update(g)
	d.audit(c, "group.create", "group", strconv.FormatUint(g.ID, 10), gin.H{"name": g.Name})
	c.JSON(201, g)
}

// listGroups 返回组树（含物化路径，子树查询用 path LIKE 前缀）
func (d *Deps) listGroups(c *gin.Context) {
	gs, err := d.Groups.Tree()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": gs})
}

func (d *Deps) updateGroup(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req groupReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	g, err := d.Groups.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "group not found"})
		return
	}
	if req.Name != "" {
		g.Name = req.Name
	}
	if err := d.Groups.Update(g); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.bumpAllCaches(c)
	d.audit(c, "group.update", "group", strconv.FormatUint(g.ID, 10), nil)
	c.JSON(200, g)
}

func (d *Deps) addMember(c *gin.Context) {
	groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		UserID uint64 `json:"user_id"`
		Role   int16  `json:"role"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.UserID == 0 {
		c.JSON(400, gin.H{"error": "user_id required"})
		return
	}
	role := req.Role
	if role == 0 {
		role = model.GroupRoleMember
	}
	if err := d.Groups.AddMember(&model.UserGroup{UserID: req.UserID, GroupID: groupID, Role: role}); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.bumpAllCaches(c)
	d.audit(c, "group.add_member", "group", strconv.FormatUint(groupID, 10), gin.H{"user_id": req.UserID})
	c.JSON(200, gin.H{"ok": true})
}

func (d *Deps) removeMember(c *gin.Context) {
	groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	userID, _ := strconv.ParseUint(c.Param("uid"), 10, 64)
	if err := d.Groups.RemoveMember(userID, groupID); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.bumpAllCaches(c)
	c.JSON(200, gin.H{"ok": true})
}

// setGroupPermissions 组挂权限点（组即角色）—— 授权即审批：
// 组长为组申请权限同样生成授权申请单（grant 方向），
// 审批链：组长若是应用负责人则跳过本人确认（SoD），由另一应用负责人复核；
// 组长非负责人时被授权方（组长）确认 + 其他 owner 复核。
// 全部通过后由 grantFromRequest 落 GroupPermission 并关联申请单留痕。
func (d *Deps) setGroupPermissions(c *gin.Context) {
	groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		ActionIDs []uint64 `json:"action_ids"`
		Reason    string   `json:"reason"` // 申请理由（留痕）
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	applicantID := d.currentUserID(c)

	// 确定申请单所属应用：取第一个 action 所属应用（组权限通常单应用）
	appID := uint64(0)
	if len(req.ActionIDs) > 0 {
		acts, _ := d.Access.ActionsByIDs(req.ActionIDs)
		for _, a := range acts {
			if a.AppID > 0 {
				appID = a.AppID
				break
			}
		}
	}
	if appID == 0 {
		c.JSON(400, gin.H{"error": "no application found for these actions"})
		return
	}
	app, err := d.Apps.ByID(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}

	r := &model.AccessRequest{
		ApplicantID:          applicantID,
		RequestType:          model.RequestGrant,
		ApplicantSubjectType: model.ReqSubjectGroup,
		ApplicantSubjectID:   groupID,
		AppID:                appID,
		Content: model.JSONMap{
			"group_permission": true,
			"group_id":         groupID,
			"action_ids":       req.ActionIDs,
		},
		Reason:    req.Reason,
		RiskLevel: model.RiskMedium,
		Status:    model.ReqPending,
	}
	if err := d.DB.Create(r).Error; err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	chain := d.buildApprovalChain(r, app, applicantID)
	d.audit(c, "group.permissions.request", "request", strconv.FormatUint(r.ID, 10),
		gin.H{"group_id": groupID, "action_ids": req.ActionIDs, "chain": chain})
	c.JSON(201, gin.H{"id": r.ID, "status": "pending", "request_type": "grant", "approval_chain": chain})
}

// getGroupPermissions 获取组的权限点列表
func (d *Deps) getGroupPermissions(c *gin.Context) {
	groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	ids, err := d.Access.GroupPermissionIDs(groupID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	actions, _ := d.Access.ActionsByIDs(ids)
	c.JSON(200, gin.H{"items": actions, "action_ids": ids})
}

// getGroupCapabilityPermissions 获取组的能力包授权列表（通过 policies 表 subject_type=group 查询）
// 返回字段与 meCapabilityPermissions 对齐，前端可复用 MyPermissions 风格的卡片+抽屉
func (d *Deps) getGroupCapabilityPermissions(c *gin.Context) {
	groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var reqs []model.AccessRequest
	d.DB.Where("status = ? AND request_type != ? AND grantee_type = ? AND grantee_id = ?",
		model.ReqApproved, model.RequestOnboard, model.GranteeGroup, groupID).
		Order("id desc").Limit(100).Find(&reqs)
	items := []gin.H{}
	for _, r := range reqs {
		cid, _ := r.Content["capability_id"].(float64)
		if cid == 0 {
			continue
		}
		cap, err := d.Caps.ByID(uint64(cid))
		if err != nil {
			continue
		}
		pid, _ := r.Content["preset_id"].(string)
		presetName := pid
		var interfaces []string
		if p := d.findPreset(cap.Presets, pid); p != nil {
			if n, ok := p["name"].(string); ok {
				presetName = n
			}
			if v, ok := p["action_codes"].([]any); ok {
				for _, x := range v {
					if code, ok := x.(string); ok {
						interfaces = append(interfaces, code)
					}
				}
			}
		}
		appName := ""
		if a, err := d.Apps.ByID(cap.AppID); err == nil {
			appName = a.Name
		}
		scopeText := selectionsText(scopeSelectionsOf(r.Content))
		items = append(items, gin.H{
			"request_id":      r.ID,
			"capability_id":   cap.ID,
			"capability_name": cap.Name,
			"description":     cap.Description,
			"app_name":        appName,
			"preset_name":     presetName,
			"interfaces":     interfaces,
			"scope_text":     scopeText,
			"grantee_type":   "group",
			"created_at":      r.CreatedAt.Format("2006-01-02 15:04"),
			"reason":          r.Reason,
			"risk_level":     r.RiskLevel,
		})
	}
	c.JSON(200, gin.H{"items": items})
}
