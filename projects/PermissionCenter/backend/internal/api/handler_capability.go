package api

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/sync"
)

// capabilityReq 能力声明请求（创建/更新）
type capabilityReq struct {
	Name            string                `json:"name"`
	DataModel       *string               `json:"data_model"`
	Description     string                `json:"description"`
	Visibility      string                `json:"visibility"`       // public | org_visible | hidden（默认 public）
	GranteeTypes    []string              `json:"grantee_types"`    // 能力包级默认可申请主体
	EnforcementMode string                `json:"enforcement_mode"` // gateway | sdk | both
	Actions         []capabilityActionReq `json:"actions"`
	ModelFields     []map[string]any      `json:"model_fields"`
	Presets         []map[string]any      `json:"presets"`
	Tags            []string              `json:"tags"`
}

type capabilityActionReq struct {
	ActionID      uint64   `json:"action_id"`
	DataOperation string   `json:"data_operation"`
	AllowedScopes []string `json:"allowed_scopes"`
	DefaultScope  string   `json:"default_scope"`
	Description   string   `json:"description"`
}

// listCapabilities 应用的能力声明清单（含动作）
func (d *Deps) listCapabilities(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	ms, err := d.Caps.List(appID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	type out struct {
		model.CapabilityManifest
		Actions []model.CapabilityAction `json:"actions"`
	}
	items := make([]out, 0, len(ms))
	for _, m := range ms {
		acts, _ := d.Caps.Actions(m.ID)
		items = append(items, out{m, acts})
	}
	c.JSON(200, gin.H{"items": items})
}

// createCapability 创建能力声明（仅 owner）
func (d *Deps) createCapability(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req capabilityReq
	if err := c.ShouldBindJSON(&req); err != nil || req.Name == "" {
		c.JSON(400, gin.H{"error": "name required"})
		return
	}
	uid := d.currentUserID(c)
	m := &model.CapabilityManifest{
		AppID:           appID,
		Name:            req.Name,
		DataModel:       req.DataModel,
		Description:     req.Description,
		Version:         1,
		Status:          model.CapDraft,
		Visibility:      orDefault(req.Visibility, model.VisPublic),
		GranteeTypes:    model.StringArray(req.GranteeTypes),
		EnforcementMode: orDefault(req.EnforcementMode, "gateway"),
		CreatedBy:       uid,
		UpdatedBy:       uid,
		ModelFields:     toJSONAny(req.ModelFields),
		Presets:         toJSONAny(req.Presets),
		Tags:            req.Tags,
	}
	if err := validatePresets(m); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	if err := d.Caps.Create(m); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	if err := d.saveCapabilityActions(m.ID, req.Actions); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "capability.create", "capability", strconv.FormatUint(m.ID, 10), gin.H{"app_id": appID, "name": m.Name})
	c.JSON(201, m)
}

// updateCapability 更新能力声明（仅 owner；版本自增）
func (d *Deps) updateCapability(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	var req capabilityReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	if req.Name != "" {
		m.Name = req.Name
	}
	if req.DataModel != nil {
		m.DataModel = req.DataModel
	}
	if req.Description != "" {
		m.Description = req.Description
	}
	if req.Visibility != "" {
		m.Visibility = req.Visibility
	}
	if req.GranteeTypes != nil {
		m.GranteeTypes = req.GranteeTypes
	}
	if req.EnforcementMode != "" {
		m.EnforcementMode = req.EnforcementMode
	}
	if req.ModelFields != nil {
		m.ModelFields = toJSONAny(req.ModelFields)
	}
	if req.Presets != nil {
		m.Presets = toJSONAny(req.Presets)
	}
	if req.Tags != nil {
		m.Tags = req.Tags
	}
	if err := validatePresets(m); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	m.UpdatedBy = d.currentUserID(c)
	if req.Actions != nil {
		m.Version++
		if err := d.saveCapabilityActions(m.ID, req.Actions); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
	}
	if err := d.Caps.Update(m); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "capability.update", "capability", strconv.FormatUint(cid, 10), gin.H{"version": m.Version})
	c.JSON(200, m)
}

// publishCapability 发布 / 下架（仅 owner；v12 支持预设级上架/下架）
// body:
//
//	{ "status": "published|disabled" }                    → 能力包整体（旧语义，兼容）
//	{ "action": "publish|offline", "preset_ids": [...], "all": bool } → 预设级上架/下架
func (d *Deps) publishCapability(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	var req struct {
		Status    string   `json:"status"` // published / disabled（整体）
		Action    string   `json:"action"` // publish | offline（预设级）
		PresetIDs []string `json:"preset_ids"`
		All       bool     `json:"all"` // 下架整个能力包全部预设
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}

	// 预设级上架 / 下架（v12）
	if req.Action != "" {
		presets := presetList(m.Presets)
		if len(presets) == 0 {
			c.JSON(400, gin.H{"error": "capability has no presets"})
			return
		}
		var targets []map[string]any
		if req.All {
			targets = presets
		} else {
			for _, id := range req.PresetIDs {
				p := findPresetInList(presets, id)
				if p == nil {
					c.JSON(400, gin.H{"error": "preset not found: " + id})
					return
				}
				targets = append(targets, p)
			}
		}
		if len(targets) == 0 {
			c.JSON(400, gin.H{"error": "preset_ids required (or all=true)"})
			return
		}
		if req.Action == "publish" {
			// A2 注册期门禁（发布时点）：数据级预设必须携带可算的数据契约 + 端点可达自检（失败二分）
			if cerr := d.ensureDataContracts(m, targets); cerr != nil {
				c.JSON(cerr.Status, gin.H{"error": cerr.Msg, "retryable": cerr.Retryable})
				return
			}
		}
		for _, p := range targets {
			switch req.Action {
			case "publish":
				p["status"] = model.PresetPublished
			case "offline":
				p["status"] = model.PresetDraft
			default:
				c.JSON(400, gin.H{"error": "action must be publish|offline"})
				return
			}
		}
		m.UpdatedBy = d.currentUserID(c)
		if err := d.Caps.Update(m); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
		// 上架/下架审批任务留痕（模拟：审批链通过 → 工单 → 生效）
		ticketNo := fmt.Sprintf("WO-%s-0%s", time.Now().Format("20060102"), map[string]string{"publish": "88", "offline": "99"}[req.Action])
		now := time.Now()
		d.DB.Create(&model.CapabilityPublishTask{
			CapabilityID: cid,
			Action:       req.Action,
			PresetIDs:    toJSONAnyStrings(req.PresetIDs),
			All:          req.All,
			RequesterID:  d.currentUserID(c),
			TicketNo:     ticketNo,
			Status:       2,
			DoneAt:       &now,
		})
		d.audit(c, "capability.preset."+req.Action, "capability", strconv.FormatUint(cid, 10),
			gin.H{"preset_ids": req.PresetIDs, "all": req.All, "ticket_no": ticketNo})
		c.JSON(200, gin.H{"ok": true, "action": req.Action, "preset_ids": req.PresetIDs, "all": req.All})
		return
	}

	// 首次发布校验：必须有动作（无动作的能力不可发布）
	if req.Status == model.CapPublished {
		acts, _ := d.Caps.Actions(cid)
		if len(acts) == 0 {
			c.JSON(400, gin.H{"error": "capability has no actions; cannot publish"})
			return
		}
		// A2 注册期门禁：全部数据级预设必须携带可算的数据契约 + 端点可达自检（失败二分）
		if cerr := d.ensureDataContracts(m, presetList(m.Presets)); cerr != nil {
			c.JSON(cerr.Status, gin.H{"error": cerr.Msg, "retryable": cerr.Retryable})
			return
		}
	}
	if req.Status == model.CapPublished {
		m.Status = model.CapPublished
	} else if req.Status == model.CapDisabled {
		m.Status = model.CapDisabled
	} else {
		c.JSON(400, gin.H{"error": "status must be published|disabled"})
		return
	}
	m.UpdatedBy = d.currentUserID(c)
	if err := d.Caps.Update(m); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "capability.publish", "capability", strconv.FormatUint(cid, 10), gin.H{"status": m.Status})
	c.JSON(200, m)
}

// deleteCapability 删除能力声明（仅 owner）
func (d *Deps) deleteCapability(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	if err := d.Caps.Delete(cid); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "capability.delete", "capability", strconv.FormatUint(cid, 10), nil)
	c.JSON(200, gin.H{"ok": true})
}

// presetScopeOptions 某预设×数据模型的范围选项（v12，数据源 = scope_option 独立表）
// 旧能力级 /capabilities/:cid/scope-options 已废弃
func (d *Deps) presetScopeOptions(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	pid := c.Param("pid")
	mc := c.Param("mc")
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	if d.findPreset(m.Presets, pid) == nil {
		c.JSON(400, gin.H{"error": "preset not found in capability"})
		return
	}
	opts, err := d.Caps.ScopeOptions(cid, pid, mc)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"model": mc, "options": opts})
}

// presetScopeMeta 预设范围元数据：可用数据模型 + 字段 + 类型/操作符白名单（编辑器下拉与前端校验）
func (d *Deps) presetScopeMeta(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	pid := c.Param("pid")
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	p := d.findPreset(m.Presets, pid)
	if p == nil {
		c.JSON(400, gin.H{"error": "preset not found in capability"})
		return
	}
	var models []string
	if v, ok := p["data_models"].([]any); ok {
		for _, x := range v {
			if s, ok := x.(string); ok {
				models = append(models, s)
			}
		}
	}
	types := gin.H{}
	for _, t := range []string{model.ScopeOptSelect, model.ScopeOptMultiSelect, model.ScopeOptVariable, model.ScopeOptInput} {
		types[t] = gin.H{"ops": model.ScopeOptOps(t), "field_required": true}
	}
	types[model.ScopeOptAll] = gin.H{"ops": []string{}, "field_required": false}
	types[model.ScopeOptInstance] = gin.H{"ops": []string{}, "field_required": false}
	c.JSON(200, gin.H{
		"models":       models,
		"model_fields": m.ModelFields,
		"types":        types,
	})
}

// validateScopeOptions 校验 owner 配置的范围选项（保存前）：结构 + op 白名单 + field 引用 + choices 非空
func (d *Deps) validateScopeOptions(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	pid := c.Param("pid")
	var req struct {
		ModelCode string              `json:"model_code"`
		Options   []model.ScopeOption `json:"options"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.ModelCode == "" {
		c.JSON(400, gin.H{"error": "model_code required"})
		return
	}
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	if d.findPreset(m.Presets, pid) == nil {
		c.JSON(400, gin.H{"error": "preset not found in capability"})
		return
	}
	// 可用字段集合（ModelFields 平铺列表）
	fieldSet := map[string]bool{}
	for _, f := range m.ModelFields {
		if fm, ok := f.(map[string]any); ok {
			if name, ok := fm["name"].(string); ok {
				fieldSet[name] = true
			}
		}
	}
	var errs []string
	for i := range req.Options {
		o := req.Options[i]
		if err := model.ValidateScopeOption(&o); err != nil {
			errs = append(errs, fmt.Sprintf("option[%d]: %v", i, err))
			continue
		}
		if o.Field != "" && !fieldSet[o.Field] {
			errs = append(errs, fmt.Sprintf("option[%d]: field %q not in model fields", i, o.Field))
		}
	}
	if len(errs) > 0 {
		c.JSON(400, gin.H{"ok": false, "errors": errs})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}

// savePresetScopeOptions 保存某预设×数据模型的范围选项（编辑保存，D1 独立表覆盖写）
func (d *Deps) savePresetScopeOptions(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	pid := c.Param("pid")
	mc := c.Param("mc")
	var req struct {
		Options []model.ScopeOption `json:"options"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.Options == nil {
		c.JSON(400, gin.H{"error": "options required"})
		return
	}
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	if d.findPreset(m.Presets, pid) == nil {
		c.JSON(400, gin.H{"error": "preset not found in capability"})
		return
	}
	fieldSet := map[string]bool{}
	for _, f := range m.ModelFields {
		if fm, ok := f.(map[string]any); ok {
			if name, ok := fm["name"].(string); ok {
				fieldSet[name] = true
			}
		}
	}
	for i := range req.Options {
		o := req.Options[i]
		if err := model.ValidateScopeOption(&o); err != nil {
			c.JSON(400, gin.H{"error": fmt.Sprintf("option[%d]: %v", i, err)})
			return
		}
		if o.Field != "" && !fieldSet[o.Field] {
			c.JSON(400, gin.H{"error": fmt.Sprintf("option[%d]: field %q not in model fields", i, o.Field)})
			return
		}
	}
	ptrOpts := make([]*model.ScopeOption, 0, len(req.Options))
	for i := range req.Options {
		ptrOpts = append(ptrOpts, &req.Options[i])
	}
	if err := d.Caps.ReplaceScopeOptions(cid, pid, mc, ptrOpts); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "capability.scope_options.save", "capability", strconv.FormatUint(cid, 10),
		gin.H{"preset_id": pid, "model_code": mc, "count": len(req.Options)})
	c.JSON(200, gin.H{"ok": true, "count": len(req.Options)})
}

// capabilityAuthz 授权管理聚合（v12）：预设列表（状态/配置）+ 授权四维概况（用户/组织/自建组/程序）
func (d *Deps) capabilityAuthz(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	// 预设列表
	presets := make([]gin.H, 0, 8)
	for i, raw := range m.Presets {
		p, _ := raw.(map[string]any)
		if p == nil {
			continue
		}
		presets = append(presets, gin.H{
			"id":            p["id"],
			"name":          p["name"],
			"status":        presetStatusOf(p),
			"grantee_types": p["grantee_types"],
			"apply_scope":   p["apply_scope"],
			"data_control":  p["data_control"],
			"data_models":   p["data_models"],
			"interfaces":    interfacesOf(p),
			"idx":           i,
		})
	}
	// 授权概况 + 预设级授权钻取：已生效策略（subject_type: 1=user 2=group 3=service）
	dim := gin.H{"user": 0, "org": 0, "group": 0, "app": 0}
	presetStats := map[string]gin.H{}
	presetGrants := map[string][]gin.H{}
	var ps []model.Policy
	d.DB.Where("capability_id = ? AND status = ?", cid, model.PolicyActive).Find(&ps)
	for _, p := range ps {
		gDim := "user"
		switch p.SubjectType {
		case model.SubjectUser:
			dim["user"] = dim["user"].(int) + 1
		case model.SubjectGroup:
			// org vs 自建组：按组类型拆分
			g, err := d.Groups.ByID(p.SubjectID)
			if err == nil && g.Type == model.GroupTypeOrg {
				dim["org"] = dim["org"].(int) + 1
				gDim = "org"
			} else {
				dim["group"] = dim["group"].(int) + 1
				gDim = "group"
			}
		case model.SubjectService:
			dim["app"] = dim["app"].(int) + 1
			gDim = "app"
		}
		// 预设归属：从关联申请单 content.preset_id 解析
		presetID := ""
		if p.RequestID != nil {
			var req model.AccessRequest
			if err := d.DB.First(&req, *p.RequestID).Error; err == nil {
				if v, ok := req.Content["preset_id"].(string); ok {
					presetID = v
				}
			}
		}
		if presetID != "" {
			st := presetStats[presetID]
			if st == nil {
				st = gin.H{"user": 0, "org": 0, "group": 0, "app": 0, "total": 0}
				presetStats[presetID] = st
			}
			st[gDim] = st[gDim].(int) + 1
			st["total"] = st["total"].(int) + 1
			presetGrants[presetID] = append(presetGrants[presetID], gin.H{
				"dim":  gDim,
				"name": d.subjectDisplayName(p.SubjectType, p.SubjectID),
				"sub":  d.subjectCode(p.SubjectType, p.SubjectID),
				"req_id": func() uint64 {
					if p.RequestID != nil {
						return *p.RequestID
					}
					return 0
				}(),
				"time": p.CreatedAt.Format("2006-01-02 15:04"),
			})
		}
	}
	c.JSON(200, gin.H{
		"capability":    m,
		"presets":       presets,
		"grants":        gin.H{"total": len(ps), "by_dim": dim},
		"preset_stats":  presetStats,
		"preset_grants": presetGrants,
	})
}

// interfacesOf 预设接口列表：优先 interfaces（demo 字段），兼容 action_codes
func interfacesOf(p map[string]any) []any {
	if v, ok := p["interfaces"].([]any); ok {
		return v
	}
	if v, ok := p["action_codes"].([]any); ok {
		return v
	}
	return nil
}

// subjectDisplayName 主体可读名（授权钻取）
func (d *Deps) subjectDisplayName(subjectType int16, subjectID uint64) string {
	switch subjectType {
	case model.SubjectUser:
		if u, err := d.Users.ByID(subjectID); err == nil {
			return u.DisplayName
		}
	case model.SubjectGroup:
		if g, err := d.Groups.ByID(subjectID); err == nil {
			return g.Name
		}
	case model.SubjectService:
		if a, err := d.Apps.ByID(subjectID); err == nil {
			return a.Name
		}
	}
	return ""
}

// subjectCode 主体标识（mono，授权钻取）
func (d *Deps) subjectCode(subjectType int16, subjectID uint64) string {
	switch subjectType {
	case model.SubjectUser:
		if u, err := d.Users.ByID(subjectID); err == nil {
			return u.Username
		}
	case model.SubjectGroup:
		if g, err := d.Groups.ByID(subjectID); err == nil {
			return g.Name
		}
	case model.SubjectService:
		if a, err := d.Apps.ByID(subjectID); err == nil {
			return "client:" + a.Code
		}
	}
	return ""
}

// toJSONAny []map[string]any → model.JSONAny（nil 保持 nil 以支持部分更新）
func toJSONAny(in []map[string]any) model.JSONAny {
	if in == nil {
		return nil
	}
	out := make(model.JSONAny, 0, len(in))
	for _, m := range in {
		out = append(out, m)
	}
	return out
}

func toJSONAnyStrings(in []string) model.JSONAny {
	if in == nil {
		return nil
	}
	out := make(model.JSONAny, 0, len(in))
	for _, s := range in {
		out = append(out, s)
	}
	return out
}

// saveCapabilityActions 校验并保存能力动作映射
func (d *Deps) saveCapabilityActions(capabilityID uint64, reqs []capabilityActionReq) error {
	acts := make([]*model.CapabilityAction, 0, len(reqs))
	for _, r := range reqs {
		if r.ActionID == 0 {
			return fmt.Errorf("action_id required")
		}
		op := r.DataOperation
		if op == "" {
			return fmt.Errorf("data_operation required for action %d", r.ActionID)
		}
		scopes := r.AllowedScopes
		if len(scopes) == 0 {
			// 推断初值（§5.3）
			def, inferred := inferScopeForOperation(op)
			scopes = inferred
			r.DefaultScope = def
		}
		ds := r.DefaultScope
		if ds == "" && len(scopes) > 0 {
			ds = scopes[0]
		}
		acts = append(acts, &model.CapabilityAction{
			CapabilityID:  capabilityID,
			ActionID:      r.ActionID,
			DataOperation: op,
			AllowedScopes: scopes,
			DefaultScope:  ds,
			Description:   r.Description,
		})
	}
	return d.Caps.SetActions(capabilityID, acts)
}

// syncCapabilities OpenAPI 推断：paths→action（已有）+ schemas→data_model（新增）
// 推断仅作初值，发布前 owner 必须逐项确认（§5.3/§5.4）
func (d *Deps) syncCapabilities(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	if app.OpenAPIURL == "" {
		c.JSON(400, gin.H{"error": "openapi_url not configured"})
		return
	}

	// 1. 先同步权限点（复用现有链路）
	if _, err := d.OpenAPISyncer.Sync(c.Request.Context(), app); err != nil {
		c.JSON(502, gin.H{"error": "openapi sync: " + err.Error()})
		return
	}

	// 2. 拉取原始文档提取 data_model
	raw, err := d.OpenAPISyncer.FetchRaw(c.Request.Context(), app.OpenAPIURL)
	if err != nil {
		c.JSON(502, gin.H{"error": "fetch openapi: " + err.Error()})
		return
	}
	models, _ := sync.ExtractDataModels(raw)

	// 3. 按资源分组推断能力
	actions, _ := d.Access.Actions(appID)
	byRes := map[string][]model.Action{}
	for _, a := range actions {
		byRes[a.Resource] = append(byRes[a.Resource], a)
	}
	uid := d.currentUserID(c)
	created := 0
	for resource, acts := range byRes {
		// 幂等：按 app+data_model 查已有能力
		var dm *string
		if _, ok := findModel(models, resource); ok {
			r := resource
			dm = &r
		}
		existing, _ := d.findCapabilityByDataModel(appID, dm)
		var m *model.CapabilityManifest
		if existing != nil {
			m = existing
		} else {
			m = &model.CapabilityManifest{
				AppID: appID, Name: resource + " 管理", DataModel: dm,
				Description: "由 OpenAPI 自动推断（初值，待 owner 确认）",
				Version:     1, Status: model.CapDraft,
				CreatedBy: uid, UpdatedBy: uid,
			}
			if err := d.Caps.Create(m); err != nil {
				continue
			}
			created++
		}
		// 组装动作
		var reqs []capabilityActionReq
		for _, a := range acts {
			def, scopes := inferScopeForOperation(a.Operation)
			reqs = append(reqs, capabilityActionReq{
				ActionID: a.ID, DataOperation: a.Operation,
				AllowedScopes: scopes, DefaultScope: def,
				Description: a.Name,
			})
		}
		if len(reqs) > 0 {
			d.saveCapabilityActions(m.ID, reqs)
		}
	}

	d.audit(c, "capability.sync", "app", strconv.FormatUint(appID, 10),
		gin.H{"data_models": len(models), "capabilities_created": created})
	c.JSON(200, gin.H{"ok": true, "data_models": models, "capabilities_created": created})
}

// validateApp 注册契约测试：OpenAPI 可拉取 + 权限点可解析 + 能力声明格式合法
// （数据接口按需查询的可调用性校验，非强制）
func (d *Deps) validateApp(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	var checks []gin.H
	if app.OpenAPIURL == "" {
		checks = append(checks, gin.H{"name": "openapi", "ok": false, "detail": "openapi_url 未配置"})
	} else if raw, err := d.OpenAPISyncer.FetchRaw(c.Request.Context(), app.OpenAPIURL); err != nil {
		checks = append(checks, gin.H{"name": "openapi", "ok": false, "detail": err.Error()})
	} else {
		acts, err := sync.ParseOpenAPI(raw, app.Code)
		if err != nil {
			checks = append(checks, gin.H{"name": "openapi", "ok": false, "detail": err.Error()})
		} else {
			checks = append(checks, gin.H{"name": "openapi", "ok": true, "detail": fmt.Sprintf("解析出 %d 个权限点", len(acts))})
		}
		models, _ := sync.ExtractDataModels(raw)
		checks = append(checks, gin.H{"name": "data_model", "ok": true, "detail": fmt.Sprintf("提取 %d 个数据模型", len(models))})
	}
	// 能力声明合法性
	caps, _ := d.Caps.List(appID)
	capOK := true
	for _, m := range caps {
		acts, _ := d.Caps.Actions(m.ID)
		if len(acts) == 0 {
			capOK = false
		}
		for _, a := range acts {
			if !validScopeEnum(a.AllowedScopes) {
				capOK = false
			}
		}
	}
	checks = append(checks, gin.H{"name": "capabilities", "ok": capOK, "detail": fmt.Sprintf("%d 个能力声明", len(caps))})
	allOK := true
	for _, ck := range checks {
		if ok, _ := ck["ok"].(bool); !ok {
			allOK = false
		}
	}
	d.audit(c, "app.validate", "app", strconv.FormatUint(appID, 10), gin.H{"ok": allOK})
	c.JSON(200, gin.H{"ok": allOK, "checks": checks})
}

// ---- 内部辅助 ----

// inferScopeForOperation §5.3 推断初值表
func inferScopeForOperation(operation string) (string, []string) {
	switch operation {
	case model.OpList:
		return model.ScopeAll, []string{model.ScopeAll}
	case model.OpRead:
		return model.ScopeAll, []string{model.ScopeAll, model.ScopeOwner, model.ScopeDimension, model.ScopeInstance}
	case model.OpCreate:
		return model.ScopeNA, []string{model.ScopeNA}
	case model.OpUpdate:
		return model.ScopeInstance, []string{model.ScopeOwner, model.ScopeInstance}
	case model.OpDelete:
		return model.ScopeInstance, []string{model.ScopeInstance}
	}
	return model.ScopeAll, []string{model.ScopeAll}
}

func validScopeEnum(scopes []string) bool {
	valid := map[string]bool{
		model.ScopeAll: true, model.ScopeOwner: true,
		model.ScopeDimension: true, model.ScopeInstance: true, model.ScopeNA: true,
	}
	for _, s := range scopes {
		if !valid[s] {
			return false
		}
	}
	return true
}

// orDefault 字符串默认值
func orDefault(v, def string) string {
	if v == "" {
		return def
	}
	return v
}

// validatePresets 校验预设结构（v12）：status 枚举 / grantee_types 合法 / apply_scope 形状 / data_control+data_models
func validatePresets(m *model.CapabilityManifest) error {
	if m.Visibility == "" {
		m.Visibility = model.VisPublic
	}
	switch m.Visibility {
	case model.VisPublic, model.VisOrgVisible, model.VisHidden:
	default:
		return fmt.Errorf("visibility must be public|org_visible|hidden")
	}
	switch m.EnforcementMode {
	case "gateway", "sdk", "both":
	default:
		return fmt.Errorf("enforcement_mode must be gateway|sdk|both")
	}
	validGrantees := map[string]bool{
		model.GranteeUser: true, model.GranteeOrg: true,
		model.GranteeGroup: true, model.GranteeApp: true,
	}
	for _, g := range m.GranteeTypes {
		if !validGrantees[g] {
			return fmt.Errorf("invalid grantee_type %q", g)
		}
	}
	for i, raw := range m.Presets {
		p, ok := raw.(map[string]any)
		if !ok {
			return fmt.Errorf("preset[%d] must be an object", i)
		}
		if id, _ := p["id"].(string); id == "" {
			return fmt.Errorf("preset[%d] requires id", i)
		}
		if st, _ := p["status"].(string); st == "" {
			p["status"] = model.PresetDraft
		} else if st != model.PresetPublished && st != model.PresetDraft {
			return fmt.Errorf("preset[%d] status must be published|draft", i)
		}
		if gts, ok := p["grantee_types"].([]any); ok {
			for _, g := range gts {
				if s, ok := g.(string); ok && !validGrantees[s] {
					return fmt.Errorf("preset[%d] invalid grantee_type %q", i, s)
				}
			}
		}
		if dc, ok := p["data_control"].(bool); ok && dc {
			dms, ok := p["data_models"].([]any)
			if !ok || len(dms) == 0 {
				return fmt.Errorf("preset[%d] data_control=true requires data_models", i)
			}
			// 数据契约结构校验（清单 A2：创建/更新时若携带 data_contract 则立即校验；
			//   "发布必填 + 端点可达自检"在发布链路 ensureDataContracts 二分执行）
			if raw, has := p["data_contract"]; has {
				spec, ok := raw.(map[string]any)
				if !ok {
					return fmt.Errorf("preset[%d] data_contract must be an object", i)
				}
				pid, _ := p["id"].(string)
				if err := validateDataContractSpec(pid, spec, m); err != nil {
					return err
				}
			}
		}
	}
	return nil
}

// presetList presets JSONAny → []map[string]any
func presetList(presets model.JSONAny) []map[string]any {
	out := make([]map[string]any, 0, len(presets))
	for _, raw := range presets {
		if p, ok := raw.(map[string]any); ok {
			out = append(out, p)
		}
	}
	return out
}

func findPresetInList(presets []map[string]any, id string) map[string]any {
	for _, p := range presets {
		if pid, _ := p["id"].(string); pid == id {
			return p
		}
	}
	return nil
}

func presetStatusOf(p map[string]any) string {
	if st, ok := p["status"].(string); ok && st != "" {
		return st
	}
	return model.PresetDraft
}

// validateDataContractSpec 数据契约结构校验（清单 A2 注册期"字段算不出 → 拒绝 + 算法建议 + 出路"）：
// 字段白名单 = 能力包资源模型字段（m.ModelFields）∪ 基础判定字段；算法档位 L1/L2/L3；新鲜度承诺 > 0
func validateDataContractSpec(presetID string, spec map[string]any, m *model.CapabilityManifest) error {
	fields, _ := spec["fields"].([]any)
	if len(fields) == 0 {
		return fmt.Errorf("preset[%s] data_contract.fields required（字段算不出三元素=不可授权；出路：不勾数据级、只发接口级能力包）", presetID)
	}
	algo, _ := spec["algorithm"].(string)
	switch algo {
	case "L1", "L2", "L3":
	default:
		return fmt.Errorf("preset[%s] data_contract.algorithm must be L1|L2|L3（算法菜单：L1 count+max(ts) / L2 集合哈希 / L3 判定字段全量哈希）", presetID)
	}
	sla := 0
	switch v := spec["staleness_sla_sec"].(type) {
	case float64:
		sla = int(v)
	case int:
		sla = v
	}
	if sla <= 0 {
		return fmt.Errorf("preset[%s] data_contract.staleness_sla_sec must be > 0（新鲜度承诺是 A6 超龄判定的读参）", presetID)
	}
	allowed := map[string]bool{"name": true, "owner_id": true, "external_id": true, "updated_at": true}
	for _, raw := range m.ModelFields {
		if mf, ok := raw.(map[string]any); ok {
			if n, ok := mf["name"].(string); ok && n != "" {
				allowed[n] = true
			}
		}
	}
	for _, f := range fields {
		s, ok := f.(string)
		if !ok || !allowed[s] {
			return fmt.Errorf("preset[%s] data_contract field %v 不可算（须为模型字段或 name/owner_id/external_id/updated_at）——换可算字段，或只发接口级能力包", presetID, f)
		}
	}
	return nil
}

// capContractError 发布期契约门禁错误（失败二分，清单 A2：
// 400=字段/契约不可算 → 拒绝发布；502 retryable=端点不可达 → 可重试提示、**不计契约拒绝**）
type capContractError struct {
	Status    int
	Msg       string
	Retryable bool
}

// ensureDataContracts 数据级预设发布门禁 + 契约落库（清单 A2 发布链路钩子）：
//   - 必填：data_contract{fields,algorithm,staleness_sla_sec}（结构校验复用 validateDataContractSpec）
//   - 自检①字段可算：结构校验内给出"算法建议 + 出路（只发接口级）"
//   - 自检②端点可达：数据源为 cmdb 时调发布方指纹端点（2s 超时）——
//     不可达 → 502 retryable。注册是控制面操作、调外部符合 Sync 既有设计，**不违反数据面解耦红线**
//   - 通过 → UpsertContract 落 data_contracts（已有契约保留确认制时钟与增量水位）
func (d *Deps) ensureDataContracts(m *model.CapabilityManifest, presets []map[string]any) *capContractError {
	appCode := ""
	if app, err := d.Apps.ByID(m.AppID); err == nil {
		appCode = app.Code
	}
	toInt := func(v any) int {
		switch t := v.(type) {
		case float64:
			return int(t)
		case int:
			return t
		}
		return 0
	}
	for _, p := range presets {
		dc, _ := p["data_control"].(bool)
		if !dc {
			continue
		}
		pid, _ := p["id"].(string)
		raw, has := p["data_contract"]
		if !has {
			return &capContractError{Status: 400, Msg: fmt.Sprintf(
				"preset %q data_control=true requires data_contract{fields,algorithm,staleness_sla_sec}（数据契约发布必填）——不填则不勾数据级、只发接口级", pid)}
		}
		spec, ok := raw.(map[string]any)
		if !ok {
			return &capContractError{Status: 400, Msg: fmt.Sprintf("preset %q data_contract must be an object", pid)}
		}
		if err := validateDataContractSpec(pid, spec, m); err != nil {
			return &capContractError{Status: 400, Msg: err.Error()}
		}
		dms, _ := p["data_models"].([]any)
		// 端点可达自检（仅 cmdb 数据源有指纹端点；其他接入系统 = 演进方向，跳过）
		if appCode == "cmdb" && len(dms) > 0 {
			if mc, ok := dms[0].(string); ok && mc != "" {
				ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
				_, ferr := d.CMDBConnector.FetchFingerprint(ctx, mc)
				cancel()
				if ferr != nil {
					return &capContractError{Status: 502, Retryable: true,
						Msg: fmt.Sprintf("fingerprint endpoint unreachable (%v)——稍后重试；这是可重试提示，不是契约拒绝", ferr)}
				}
			}
		}
		fields := []string{}
		for _, f := range spec["fields"].([]any) {
			if s, ok := f.(string); ok {
				fields = append(fields, s)
			}
		}
		for _, dm := range dms {
			mc, ok := dm.(string)
			if !ok || mc == "" {
				continue
			}
			if _, err := d.Contracts.UpsertContract(&model.DataContract{
				AppID: m.AppID, ModelCode: mc, Fields: fields,
				Algorithm:        spec["algorithm"].(string),
				StalenessSlaSec:  toInt(spec["staleness_sla_sec"]),
				DegradeMaxAgeSec: toInt(spec["degrade_max_age_sec"]),
			}); err != nil {
				return &capContractError{Status: 500, Msg: "persist contract: " + err.Error()}
			}
		}
	}
	return nil
}
func (d *Deps) findCapabilityByDataModel(appID uint64, dm *string) (*model.CapabilityManifest, error) {
	ms, err := d.Caps.List(appID)
	if err != nil {
		return nil, err
	}
	for i := range ms {
		if dm == nil {
			if ms[i].DataModel == nil {
				return &ms[i], nil
			}
			continue
		}
		if ms[i].DataModel != nil && *ms[i].DataModel == *dm {
			return &ms[i], nil
		}
	}
	return nil, nil
}

func findModel(models []sync.DataModelCandidate, code string) (sync.DataModelCandidate, bool) {
	for _, m := range models {
		if m.Code == code {
			return m, true
		}
	}
	return sync.DataModelCandidate{}, false
}
