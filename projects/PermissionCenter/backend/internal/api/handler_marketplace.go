package api

import (
	"sort"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// marketplaceCapabilities 权限市场能力目录（仅已发布）
// 搜索/筛选：q=全文（名称/描述/应用名/数据模型/标签）、app=应用 code、model=数据模型、tag=标签
// presets 由后端解析 action_codes → action_ids + ops（method/path/name），前端直接渲染组合卡片
func (d *Deps) marketplaceCapabilities(c *gin.Context) {
	q := c.Query("q")
	appCode := c.Query("app")
	modelCode := c.Query("model")
	tag := c.Query("tag")

	ms, err := d.Caps.Published()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	type out struct {
		model.CapabilityManifest
		AppName string                   `json:"app_name"`
		AppCode string                   `json:"app_code"`
		Actions []model.CapabilityAction `json:"actions"`
		Presets []map[string]any         `json:"presets"`
	}
	items := make([]out, 0, len(ms))
	for _, m := range ms {
		appName, appCodeOf := "", ""
		if app, err := d.Apps.ByID(m.AppID); err == nil {
			appName, appCodeOf = app.Name, app.Code
		}
		// 筛选：应用
		if appCode != "" && appCodeOf != appCode {
			continue
		}
		// 筛选：数据模型
		if modelCode != "" && (m.DataModel == nil || *m.DataModel != modelCode) {
			continue
		}
		// 筛选：标签
		if tag != "" && !containsStr(m.Tags, tag) {
			continue
		}
		// 筛选：全文搜索
		if q != "" && !capabilityMatches(m, q, appName, appCodeOf) {
			continue
		}
		acts, _ := d.Caps.Actions(m.ID)
		presets := d.enrichPresets(m.AppID, m.Presets)
		items = append(items, out{m, appName, appCodeOf, acts, presets})
	}
	c.JSON(200, gin.H{"items": items})
}

// enrichPresets 解析预设的 action_codes → action_ids + ops（method/path/name），并校验 allowed_scopes
func (d *Deps) enrichPresets(appID uint64, presets model.JSONAny) []map[string]any {
	out := make([]map[string]any, 0, len(presets))
	for _, raw := range presets {
		p, _ := raw.(map[string]any)
		if p == nil {
			continue
		}
		// v12：市场只显示已上架预设（草稿预设不可申请，但已授权者仍生效）
		if st, _ := p["status"].(string); st != model.PresetPublished {
			continue
		}
		out = append(out, d.enrichOnePreset(appID, p))
	}
	return out
}

// enrichOnePreset 单个预设：action_codes → action_ids + ops（供市场卡片 / 申请预览复用）
func (d *Deps) enrichOnePreset(appID uint64, p map[string]any) map[string]any {
	resolved := map[string]any{}
	for k, v := range p {
		resolved[k] = v
	}
	var codes []any
	if v, ok := p["action_codes"].([]any); ok {
		codes = v
	}
	var actionIDs []uint64
	ops := make([]map[string]any, 0, len(codes))
	for _, codeRaw := range codes {
		code, _ := codeRaw.(string)
		if code == "" {
			continue
		}
		act, err := d.Access.ActionByCode(appID, code)
		if err != nil {
			continue
		}
		actionIDs = append(actionIDs, act.ID)
		ops = append(ops, map[string]any{
			"action": act.Code, "method": act.Method, "path": act.Path,
			"name": act.Name, "operation": act.Operation,
			// 接口契约（v12）：请求/响应示例
			"req_example":  act.ReqExample,
			"resp_example": act.RespExample,
		})
	}
	resolved["action_ids"] = actionIDs
	resolved["ops"] = ops
	return resolved
}

func capabilityMatches(m model.CapabilityManifest, q, appName, appCode string) bool {
	needle := q
	hay := m.Name + " " + m.Description + " " + appName + " " + appCode
	if m.DataModel != nil {
		hay += " " + *m.DataModel
	}
	for _, t := range m.Tags {
		hay += " " + t
	}
	return strings.Contains(strings.ToLower(hay), strings.ToLower(needle))
}

func containsStr(arr []string, s string) bool {
	for _, v := range arr {
		if v == s {
			return true
		}
	}
	return false
}

// marketplaceTemplates 权限市场策略模板（已发布模板化资产）
func (d *Deps) marketplaceTemplates(c *gin.Context) {
	ts, err := d.Tpls.Published()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	type out struct {
		model.PolicyTemplate
		AppName string `json:"app_name"`
		AppCode string `json:"app_code"`
	}
	items := make([]out, 0, len(ts))
	for _, t := range ts {
		appName, appCode := "", ""
		if app, err := d.Apps.ByID(t.AppID); err == nil {
			appName, appCode = app.Name, app.Code
		}
		items = append(items, out{t, appName, appCode})
	}
	c.JSON(200, gin.H{"items": items})
}

// marketplacePrereqs 前置接口权限预检（智能表单：缺失的接口权限自动联动勾选）
func (d *Deps) marketplacePrereqs(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
	m, err := d.Caps.ByID(cid)
	if err != nil {
		c.JSON(404, gin.H{"error": "capability not found"})
		return
	}
	acts, _ := d.Caps.Actions(cid)

	// 当前用户已有接口权限
	uid := d.currentUserID(c)
	have := d.userActionIDs(uid, m.AppID)

	type actionView struct {
		model.CapabilityAction
		Action model.Action `json:"action"`
		Have   bool         `json:"have"`
		Prereq bool         `json:"prereq"`
	}
	items := make([]actionView, 0, len(acts))
	for _, ca := range acts {
		act, err := d.Access.ActionByID(ca.ActionID)
		if err != nil {
			continue
		}
		haveFlag := false
		for _, id := range have {
			if id == ca.ActionID {
				haveFlag = true
				break
			}
		}
		// 除 read/list 外均视为前置接口权限
		items = append(items, actionView{ca, *act, haveFlag, ca.DataOperation != model.OpRead && ca.DataOperation != model.OpList})
	}

	c.JSON(200, gin.H{
		"capability":      m,
		"actions":         items,
		"missing_prereqs": len(items) > 0, // 前端根据 have/prereq 计算
	})
}

// userActionIDs 用户在某个应用下拥有的全部权限点 ID（个人 + 组继承）
func (d *Deps) userActionIDs(uid, appID uint64) []uint64 {
	set := map[uint64]bool{}
	// 个人策略
	var ps []model.Policy
	d.DB.Where("app_id = ? AND subject_type = ? AND subject_id = ? AND status = ?",
		appID, model.SubjectUser, uid, model.PolicyActive).Find(&ps)
	for _, p := range ps {
		for _, id := range p.ActionIDs {
			set[id] = true
		}
	}
	// 组继承（org + custom + 祖先）
	groups, _ := d.Groups.ByUserID(uid)
	groupIDs := d.allGroupIDsForUser(uid, groups)
	if len(groupIDs) > 0 {
		var gps []model.GroupPermission
		d.DB.Where("group_id IN ?", groupIDs).Find(&gps)
		for _, gp := range gps {
			set[gp.ActionID] = true
		}
	}
	out := make([]uint64, 0, len(set))
	for id := range set {
		out = append(out, id)
	}
	return out
}

// ---- T7 关联推荐（#4）：基于共现推荐，非依赖 ----
//
// 同一申请单（含多包单与历史 items）中共同出现过的包 = 强关联信号——
// "常一起申请"；无共现数据时返回空（不猜、不做热门兜底，推荐是提效不是导购）。
// GET /api/v1/marketplace/recommend?capability_id=N → top3
func (d *Deps) marketplaceRecommend(c *gin.Context) {
	cid, _ := strconv.ParseUint(c.Query("capability_id"), 10, 64)
	if cid == 0 {
		c.JSON(400, gin.H{"error": "capability_id required"})
		return
	}
	var reqs []model.AccessRequest
	d.DB.Where("request_type = ? AND status IN ?",
		model.RequestApply, []int16{model.ReqApproved, model.ReqPending}).
		Order("id desc").Limit(500).Find(&reqs)
	co := map[uint64]int{}
	for _, r := range reqs {
		items, _ := r.Items["items"].([]any)
		ids := make([]uint64, 0, len(items))
		for _, it := range items {
			item, _ := it.(map[string]any)
			if item == nil {
				continue
			}
			switch v := item["capability_id"].(type) {
			case float64:
				ids = append(ids, uint64(v))
			case uint64:
				ids = append(ids, v)
			}
		}
		has := false
		for _, id := range ids {
			if id == cid {
				has = true
				break
			}
		}
		if !has || len(ids) < 2 {
			continue
		}
		for _, id := range ids {
			if id != cid {
				co[id]++
			}
		}
	}
	type rec struct {
		CapabilityID uint64 `json:"capability_id"`
		Name         string `json:"name"`
		AppName      string `json:"app_name"`
		CoCount      int    `json:"co_count"`
	}
	out := make([]rec, 0, 3)
	for id, n := range co {
		m, err := d.Caps.ByID(id)
		if err != nil {
			continue
		}
		appName := ""
		if a, err := d.Apps.ByID(m.AppID); err == nil {
			appName = a.Name
		}
		out = append(out, rec{CapabilityID: id, Name: m.Name, AppName: appName, CoCount: n})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].CoCount != out[j].CoCount {
			return out[i].CoCount > out[j].CoCount
		}
		return out[i].CapabilityID < out[j].CapabilityID
	})
	if len(out) > 3 {
		out = out[:3]
	}
	c.JSON(200, gin.H{"items": out})
}
