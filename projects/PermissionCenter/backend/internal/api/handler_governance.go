package api

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

// submitRequest 提交权限申请（自助 / 业务系统对接）
// content: {action_ids:[], resource_scope:{...}}
// 扩展（FR-3 智能申请）：subject_type 申请主体（1=我 2=自建组 3=组织 4=下游应用）、
//   items 申请项 [{capability_id, action_ids, data_scope, ttl}]、prereq_actions 联动接口权限点、expires_at TTL
// 扩展（能力打包申请）：capability_id + preset_id + scope + scope_params
//   → 后端解析预设 action_codes → action_ids、风险组合升级、条件表达式生成（Casbin/OpenFGA）
// 审批规则（审批即策略）：
//   - 低风险：可自动审批（应用 owner 在线时自动路由）
//   - 中风险：需应用 owner 审批（组织上级可参与）
//   - 高风险：需应用 owner + 安全复核
func (d *Deps) submitRequest(c *gin.Context) {
	var req struct {
		AppID         uint64         `json:"app_id"`
		SubjectType   int16          `json:"subject_type"`
		SubjectID     uint64         `json:"subject_id"`
		Content       map[string]any `json:"content"`
		Items         map[string]any `json:"items"`
		PrereqActions []uint64       `json:"prereq_actions"`
		Reason        string         `json:"reason"`
		RiskLevel     int16          `json:"risk_level"`
		ExpiresAt     *time.Time     `json:"expires_at"`
		// 能力打包申请（能力包向导）：预设 + 数据范围 + 范围参数
		CapabilityID uint64           `json:"capability_id"`
		PresetID     string           `json:"preset_id"`
		Scope        string           `json:"scope"`
		ScopeParams  map[string]any   `json:"scope_params"`
		// v12 双主体 + 范围字段类型系统
		GranteeType     string           `json:"grantee_type"`     // user|org|group|app
		GranteeName     string           `json:"grantee_name"`     // client:xxx / 用户名 / 组织路径
		GranteeID       uint64           `json:"grantee_id"`
		ScopeSelections []map[string]any `json:"scope_selections"` // v12：[{model,type,selectedValue,selectedValues[]}]
		// 接入申请（Phase 6.5，D4 定案）：request_type=3
		RequestType   int16  `json:"request_type"`    // 1=自助申请 2=owner授权 3=接入申请
		ConsumerAppID uint64 `json:"consumer_app_id"` // 申请方（下游应用）
		ProviderAppID uint64 `json:"provider_app_id"` // 目标应用（提供方）
		AuthMethod    string `json:"auth_method"`     // 选自提供方 app.auth 支持列表
		NetworkTicket bool   `json:"network_ticket"`  // 网络打通工单并入接入申请（一次落地）
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	applicantID := d.currentUserID(c)

	// 接入申请（Phase 6.5）：前置鉴权 + 网络开通，凭证一次签发、能力包多次追加 scope
	if req.RequestType == model.RequestOnboard {
		req.AppID = req.ProviderAppID
		if req.ProviderAppID == 0 || req.ConsumerAppID == 0 {
			c.JSON(400, gin.H{"error": "consumer_app_id / provider_app_id required"})
			return
		}
		provider, err := d.Apps.ByID(req.ProviderAppID)
		if err != nil {
			c.JSON(404, gin.H{"error": "provider app not found"})
			return
		}
		if _, err := d.Apps.ByID(req.ConsumerAppID); err != nil {
			c.JSON(404, gin.H{"error": "consumer app not found"})
			return
		}
		r := &model.AccessRequest{
			ApplicantID:    applicantID,
			RequestType:    model.RequestOnboard,
			ApplicantSubjectType: model.ReqSubjectApp,
			ApplicantSubjectID:   req.ConsumerAppID,
			GranteeType:          model.GranteeApp,
			GranteeName:          "client:" + req.AuthMethod,
			GranteeID:            req.ConsumerAppID,
			AppID:                req.ProviderAppID,
			Content: model.JSONMap{
				"onboard":        true,
				"consumer_app_id": req.ConsumerAppID,
				"provider_app_id": req.ProviderAppID,
				"auth_method":     req.AuthMethod,
				"network_ticket":  req.NetworkTicket,
			},
			Reason:    req.Reason,
			RiskLevel: model.RiskMedium, // 凭证签发 → 至少中风险，走审批
			Status:    model.ReqPending,
		}
		if err := d.DB.Create(r).Error; err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
		chain := d.buildApprovalChain(r, provider, applicantID)
		d.audit(c, "request.onboard", "request", strconv.FormatUint(r.ID, 10),
			gin.H{"consumer_app_id": req.ConsumerAppID, "provider_app_id": req.ProviderAppID,
				"auth_method": req.AuthMethod, "network_ticket": req.NetworkTicket})
		c.JSON(201, gin.H{"id": r.ID, "status": "pending", "approval_chain": chain})
		return
	}

	if req.AppID == 0 {
		c.JSON(400, gin.H{"error": "app_id required"})
		return
	}

	// SoD 硬约束 ①：申请人 ≠ 审批人（申请时即校验应用负责人）
	app, err := d.Apps.ByID(req.AppID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}

	subjectType := req.SubjectType
	if subjectType == 0 {
		subjectType = model.ReqSubjectUser
	}
	subjectID := req.SubjectID
	if subjectID == 0 {
		subjectID = applicantID
	}
	// 申请主体有效性：自建组须存在且申请人可代表（成员）
	if subjectType == model.ReqSubjectGroup {
		if _, err := d.Groups.ByID(subjectID); err != nil {
			c.JSON(400, gin.H{"error": "group not found"})
			return
		}
	}
	if subjectType == model.ReqSubjectApp {
		if _, err := d.Apps.ByID(subjectID); err != nil {
			c.JSON(400, gin.H{"error": "app not found"})
			return
		}
	}

	// 能力打包申请：解析预设 → action_ids + items + 风险组合 + 条件表达式
	if req.CapabilityID > 0 && req.PresetID != "" {
		cap, err := d.Caps.ByID(req.CapabilityID)
		if err != nil {
			c.JSON(404, gin.H{"error": "capability not found"})
			return
		}
		preset := d.findPreset(cap.Presets, req.PresetID)
		if preset == nil {
			c.JSON(400, gin.H{"error": "preset not found in capability"})
			return
		}
		resolved := d.enrichOnePreset(cap.AppID, preset)
		aids, _ := resolved["action_ids"].([]uint64)
		ops, _ := resolved["ops"].([]map[string]any)
		if len(aids) == 0 {
			c.JSON(400, gin.H{"error": "preset resolves to no actions"})
			return
		}
		// 组装申请项（兼容旧 grantFromRequest 解析）
		var modelCode *string
		if cap.DataModel != nil {
			modelCode = cap.DataModel
		}
		actionCodes := make([]string, 0, len(ops))
		for _, op := range ops {
			if code, ok := op["action"].(string); ok {
				actionCodes = append(actionCodes, code)
			}
		}
		subjName := d.subjectNameForExpression(subjectType, subjectID, req.AppID)
		var engine, code string
		if len(req.ScopeSelections) > 0 {
			// v12：范围字段类型系统——按模型结构化选择，后端生成 CEL（§4.5）
			engine, code, err = d.buildV12ScopeExpression(cap, preset, req.ScopeSelections, actionCodes, subjName)
			if err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			req.Items = map[string]any{"items": []any{map[string]any{
				"capability_id": req.CapabilityID, "preset_id": req.PresetID,
				"action_ids": aids, "data_scope": map[string]any{
					"type": "selections", "selections": req.ScopeSelections,
				},
			}}}
			req.Content = map[string]any{
				"capability_id":     req.CapabilityID,
				"preset_id":         req.PresetID,
				"scope_selections":  req.ScopeSelections,
				"scope_expression":  code,
				"expression_engine": engine,
			}
			// 数据级控制 → 至少中风险（demo applyRisk 一致）
			if dc, _ := preset["data_control"].(bool); dc && req.RiskLevel < model.RiskMedium {
				req.RiskLevel = model.RiskMedium
			}
		} else {
			// 旧语义：单 scope + scope_params（兼容）
			ds := map[string]any{"type": req.Scope}
			for k, v := range req.ScopeParams {
				ds[k] = v
			}
			if cap.DataModel != nil {
				ds["model"] = *cap.DataModel
			}
			for _, op := range ops {
				if o, ok := op["operation"].(string); ok && o != model.OpList {
					ds["operation"] = o
					break
				}
			}
			if req.Scope == model.ScopeDimension {
				if v, ok := ds["dimension"].(string); ok {
					ds["values"] = []any{v}
				}
			}
			req.Items = map[string]any{"items": []any{map[string]any{
				"capability_id": req.CapabilityID, "preset_id": req.PresetID,
				"action_ids": aids, "data_scope": ds,
			}}}
			engine, code = buildScopeExpression(req.Scope, req.ScopeParams, modelCode, actionCodes, subjName)
			req.Content = map[string]any{
				"capability_id":     req.CapabilityID,
				"preset_id":         req.PresetID,
				"scope":             req.Scope,
				"scope_params":      req.ScopeParams,
				"scope_expression":  code,
				"expression_engine": engine,
			}
		}
		// 风险组合升级（§5.4）
		if len(req.ScopeSelections) == 0 {
			req.RiskLevel = comboRiskFromOps(subjectType, req.Scope, ops)
		}
	}

	risk := req.RiskLevel
	if risk == 0 {
		risk = model.RiskLow
	}
	// 风险规则：申请主体为下游应用（M2M）→ 至少中风险
	if subjectType == model.ReqSubjectApp && risk < model.RiskMedium {
		risk = model.RiskMedium
	}

	r := &model.AccessRequest{
		ApplicantID:          applicantID,
		RequestType:          model.RequestApply,
		ApplicantSubjectType: subjectType,
		ApplicantSubjectID:   subjectID,
		GranteeType:          req.GranteeType,
		GranteeName:          req.GranteeName,
		GranteeID:            req.GranteeID,
		ScopeSelections:      toJSONAny(req.ScopeSelections),
		AppID:                req.AppID,
		Content:              req.Content,
		Items:                req.Items,
		PrereqActions:        req.PrereqActions,
		Reason:               req.Reason,
		RiskLevel:            risk,
		Status:               model.ReqPending,
		ExpiresAt:            req.ExpiresAt,
	}
	if r.GranteeType == "" {
		r.GranteeType, r.GranteeName, r.GranteeID = d.granteeFields(subjectType, subjectID)
	}
	if err := d.DB.Create(r).Error; err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 审批即策略（approval-as-policy）：根据风险等级自动路由审批链
	approvalChain := d.buildApprovalChain(r, app, applicantID)

	// 低风险 + 有可自动审批的 owner → 自动通过
	if risk == model.RiskLow && len(approvalChain) > 0 {
		autoApprover := approvalChain[0]
		if autoApprover != applicantID { // SoD：自动审批人不能是申请人
			r.Status = model.ReqApproved
			d.DB.Save(&r)
			d.DB.Create(&model.ApprovalTask{
				RequestID:  r.ID, Step: 1, ApproverID: autoApprover,
				Action: model.ApproveYes, Comment: "auto-approved (low risk)",
			})
			if err := d.grantFromRequest(c, r, autoApprover); err != nil {
				r.Status = model.ReqPending
				d.DB.Save(&r)
				d.audit(c, "request.auto_grant_fail", "request", strconv.FormatUint(r.ID, 10), gin.H{"error": err.Error()})
			} else {
				d.audit(c, "request.auto_approve", "request", strconv.FormatUint(r.ID, 10),
					gin.H{"approver": autoApprover, "risk": risk})
				c.JSON(201, gin.H{"id": r.ID, "status": "auto-approved"})
				return
			}
		}
	}

	d.audit(c, "request.submit", "request", strconv.FormatUint(r.ID, 10),
		gin.H{"app_id": req.AppID, "risk": risk, "approval_chain": approvalChain})
	c.JSON(201, r)
}

// buildApprovalChain 审批链构建（审批即策略，授权无直授后门）：
// SoD 硬约束：申请人（发起人）∉ 审批链
// 方向：
//   - 自助申请（apply）：应用 owner（排除申请人）→ 高风险追加安全复核
//   - owner 授权（grant）：被授权方确认（本人/组长/对方应用 owner）+ 应用其他 owner 复核
//     → owner 给自己授权时跳过"本人确认"（SoD），仅其他 owner 审批
func (d *Deps) buildApprovalChain(r *model.AccessRequest, app *model.App, applicantID uint64) []uint64 {
	chain := make([]uint64, 0, 4)

	// owner 授权：被授权方确认（"让他知道、让他同意"）
	// SoD：申请人若同时是被授权方确认人（组长给自己组申请），跳过本人确认，由其他 owner 复核
	if r.RequestType == model.RequestGrant && r.ApplicantSubjectID != applicantID {
		if confirm := d.granteeConfirm(r); confirm > 0 && confirm != applicantID && !d.inChain(confirm, chain) {
			chain = append(chain, confirm)
		}
	}

	// 应用其他 owner 复核（排除发起人自身）
	var owners []model.AppOwner
	d.DB.Where("app_id = ?", app.ID).Find(&owners)
	for _, o := range owners {
		if o.UserID != applicantID && !d.inChain(o.UserID, chain) { // SoD
			chain = append(chain, o.UserID)
		}
	}

	// 高风险 → 追加安全复核节点（admin 兜底）
	if r.RiskLevel >= model.RiskHigh {
		admin, err := d.Users.ByUsername("admin")
		if err == nil && admin.ID != applicantID && !d.inChain(admin.ID, chain) {
			chain = append(chain, admin.ID)
		}
	}

	return chain
}

// granteeConfirm 被授权方确认人：
//   - 授予用户 → 本人
//   - 授予组/组织 → 组长（组 admin）
//   - 授予下游应用(M2M) → 对方应用 primary owner
func (d *Deps) granteeConfirm(r *model.AccessRequest) uint64 {
	switch r.ApplicantSubjectType {
	case model.ReqSubjectUser:
		return r.ApplicantSubjectID
	case model.ReqSubjectGroup, model.ReqSubjectOrg:
		var ug model.UserGroup
		if err := d.DB.Where("group_id = ? AND role = ?", r.ApplicantSubjectID, model.GroupRoleAdmin).First(&ug).Error; err == nil {
			return ug.UserID
		}
		return 0
	case model.ReqSubjectApp:
		var ao model.AppOwner
		if err := d.DB.Where("app_id = ? AND is_primary = ?", r.ApplicantSubjectID, true).First(&ao).Error; err == nil {
			return ao.UserID
		}
	}
	return 0
}

func (d *Deps) listRequests(c *gin.Context) {
	userID := d.currentUserID(c)
	var rs []model.AccessRequest
	// 支持查看待审批（管理员可看所有 pending）
	role := c.Query("role")
	if role == "approver" {
		// 查看待我审批的：pending 状态 + 我在审批链中
		if err := d.DB.Where("status = ?", model.ReqPending).Order("id desc").Find(&rs).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		// 过滤：只保留我在审批链中的
		var filtered []model.AccessRequest
		for _, r := range rs {
			app, err := d.Apps.ByID(r.AppID)
			if err != nil {
				continue
			}
			chain := d.buildApprovalChain(&r, app, r.ApplicantID)
			if d.inChain(userID, chain) {
				filtered = append(filtered, r)
			}
		}
		c.JSON(200, gin.H{"items": filtered})
		return
	}
	if err := d.DB.Where("applicant_id = ?", userID).Order("id desc").Find(&rs).Error; err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": rs})
}

// requestDetail 申请单详情（Phase 6：双主体 + 范围选择 + 表达式 + 审批链 + 状态）
func (d *Deps) requestDetail(c *gin.Context) {
	rid, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var r model.AccessRequest
	if err := d.DB.First(&r, rid).Error; err != nil {
		c.JSON(404, gin.H{"error": "request not found"})
		return
	}
	uid := d.currentUserID(c)
	if r.ApplicantID != uid {
		admin := false
		if u, err := d.Users.ByID(uid); err == nil && u.Username == "admin" {
			admin = true
		}
		// 授权作用到当前用户的申请单（本人 / 所属组织 / 所属自建组）也可见
		relevant := false
		if r.GranteeType == model.GranteeUser && r.GranteeID == uid {
			relevant = true
		} else if r.GranteeType == model.GranteeOrg || r.GranteeType == model.GranteeGroup {
			groups, _ := d.Groups.ByUserID(uid)
			for _, id := range d.allGroupIDsForUser(uid, groups) {
				if id == r.GranteeID {
					relevant = true
					break
				}
			}
		}
		if !admin && !relevant {
			c.JSON(403, gin.H{"error": "not your request"})
			return
		}
	}
	var tasks []model.ApprovalTask
	d.DB.Where("request_id = ?", rid).Order("step").Find(&tasks)
	applicant := ""
	if u, err := d.Users.ByID(r.ApplicantID); err == nil {
		applicant = u.DisplayName + " (" + u.Username + ")"
	}
	capName, presetName := "", ""
	if v, ok := r.Content["capability_id"].(float64); ok {
		if m, err := d.Caps.ByID(uint64(v)); err == nil {
			capName = m.Name
			if pid, ok := r.Content["preset_id"].(string); ok {
				if p := d.findPreset(m.Presets, pid); p != nil {
					presetName, _ = p["name"].(string)
				}
			}
		}
	}
	// 关联生效策略（退还/管理用）
	var policyID uint64
	var p model.Policy
	if err := d.DB.Where("request_id = ? AND status = ?", rid, model.PolicyActive).First(&p).Error; err == nil {
		policyID = p.ID
	}
	// 审批任务装饰（审批人姓名 + 时间）
	taskView := make([]gin.H, 0, len(tasks))
	for _, t := range tasks {
		name := ""
		if u, err := d.Users.ByID(t.ApproverID); err == nil {
			name = u.DisplayName + " (" + u.Username + ")"
		}
		taskView = append(taskView, gin.H{
			"step": t.Step, "approver_id": t.ApproverID, "approver_name": name,
			"action": t.Action, "comment": t.Comment, "created_at": t.CreatedAt.Format("2006-01-02 15:04"),
		})
	}
	title := "权限申请"
	if capName != "" {
		if presetName != "" {
			title = "申请「" + capName + " / " + presetName + "」"
		} else {
			title = "申请「" + capName + "」"
		}
	}
	if r.RequestType == model.RequestOnboard {
		title = "接入申请：" + capName
	}
	c.JSON(200, gin.H{
		"request":         r,
		"ticket_no":       "REQ-" + pad4(rid),
		"title":           title,
		"policy_id":       policyID,
		"approval_tasks":  taskView,
		"applicant":       applicant,
		"capability_name": capName,
		"preset_name":     presetName,
	})
}

// approveRequest 审批（含 SoD 校验 + 审批凭证回存）
func (d *Deps) approveRequest(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		Action  int16  `json:"action"` // 1=通过 2=驳回
		Comment string `json:"comment"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	var r model.AccessRequest
	if err := d.DB.First(&r, id).Error; err != nil {
		c.JSON(404, gin.H{"error": "request not found"})
		return
	}
	if r.Status != model.ReqPending {
		c.JSON(400, gin.H{"error": "request not in pending status"})
		return
	}
	approver := d.currentUserID(c)

	// SoD 硬约束 ①：申请人与审批人互斥
	if approver == r.ApplicantID {
		c.JSON(403, gin.H{"error": "SoD: applicant cannot approve own request"})
		return
	}

	// SoD 硬约束 ③：审批凭证回存（审批人必须在审批链中）
	// owner 授权（grant）方向无条件强制：被授权方确认/其他 owner 复核，谁都能审就是没审
	app, _ := d.Apps.ByID(r.AppID)
	chain := d.buildApprovalChain(&r, app, r.ApplicantID)
	if !d.inChain(approver, chain) && (r.RiskLevel >= model.RiskMedium || r.RequestType == model.RequestGrant) {
		c.JSON(403, gin.H{"error": "approver not in approval chain"})
		return
	}

	if req.Action == model.ApproveNo {
		r.Status = model.ReqRejected
		d.DB.Save(&r)
		d.DB.Create(&model.ApprovalTask{
			RequestID: r.ID, Step: 1, ApproverID: approver,
			Action: model.ApproveNo, Comment: req.Comment,
		})
		d.audit(c, "request.reject", "request", strconv.FormatUint(r.ID, 10),
			gin.H{"comment": req.Comment, "approver": approver})
		c.JSON(200, gin.H{"status": "rejected"})
		return
	}

	// 通过：回存审批凭证，然后检查审批链是否全部通过
	d.DB.Create(&model.ApprovalTask{
		RequestID: r.ID, Step: len(chain), ApproverID: approver,
		Action: model.ApproveYes, Comment: req.Comment,
	})
	d.audit(c, "request.approve", "request", strconv.FormatUint(r.ID, 10),
		gin.H{"comment": req.Comment, "approver": approver, "chain": chain})

	// 多级审批：链上所有审批人必须全部通过，最后一人通过时才开通权限
	var remaining []uint64
	for _, id := range chain {
		var cnt int64
		d.DB.Model(&model.ApprovalTask{}).
			Where("request_id = ? AND approver_id = ? AND action = ?", r.ID, id, model.ApproveYes).Count(&cnt)
		if cnt == 0 {
			remaining = append(remaining, id)
		}
	}
	if len(remaining) > 0 {
		// 尚有待审批人（被授权方确认 / 其他 owner 复核 / 高风险复核）
		c.JSON(200, gin.H{"status": "partially_approved", "remaining": remaining})
		return
	}

	// 全部通过：开通权限（创建策略并发布，复用策略发布链路）
	if err := d.grantFromRequest(c, &r, approver); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	r.Status = model.ReqApproved
	d.DB.Save(&r)
	c.JSON(200, gin.H{"status": "approved"})
}

func (d *Deps) inChain(userID uint64, chain []uint64) bool {
	for _, id := range chain {
		if id == userID {
			return true
		}
	}
	return false
}

// grantFromRequest 申请内容 → 策略（开通）+ 审批凭证回存
// 支持：申请主体（我/组/组织/下游应用）+ 申请项（items，含 capability_id/data_scope/ttl）
func (d *Deps) grantFromRequest(c *gin.Context, r *model.AccessRequest, approver uint64) error {
	content := r.Content

	// 主体：优先申请单扩展字段，兼容旧 content 格式
	subjectType := int16(model.SubjectUser)
	subjectID := r.ApplicantID
	switch r.ApplicantSubjectType {
	case model.ReqSubjectGroup, model.ReqSubjectOrg:
		subjectType = model.SubjectGroup
		subjectID = r.ApplicantSubjectID
	case model.ReqSubjectApp:
		subjectType = model.SubjectService
		subjectID = r.ApplicantSubjectID
	default:
		if v, ok := content["subject_type"].(float64); ok {
			subjectType = int16(v)
		}
		if v, ok := content["subject_id"].(float64); ok {
			subjectID = uint64(v)
		}
	}

	// 动作 + 数据范围：优先 items（能力声明维度），兼容旧 content
	var actionIDs []uint64
	var scope map[string]any
	var capabilityID *uint64
	dataScopeType := ""
	if items, ok := r.Items["items"].([]any); ok && len(items) > 0 {
		// 合并所有 item 的 action_ids
		seen := map[uint64]bool{}
		for _, it := range items {
			item, _ := it.(map[string]any)
			// capability_id 兼容 float64（JSON 反序列化）与 uint64（Go 程序构造）
			switch cid := item["capability_id"].(type) {
			case float64:
				cidv := uint64(cid)
				capabilityID = &cidv
			case uint64:
				capabilityID = &cid
			}
			for _, id := range parseActionIDs(item["action_ids"]) {
				if !seen[id] {
					seen[id] = true
					actionIDs = append(actionIDs, id)
				}
			}
			if ds, ok := item["data_scope"].(map[string]any); ok {
				scope = ds
				if t, ok := ds["type"].(string); ok {
					dataScopeType = t
				}
			}
		}
	} else {
		actionIDs = parseActionIDs(content["action_ids"])
		if v, ok := content["resource_scope"].(map[string]any); ok {
			scope = v
		}
	}

	// 组权限申请（组长为组申请接口权限）：审批通过后落 GroupPermission 并关联申请单留痕
	if v, ok := content["group_permission"].(bool); ok && v {
		groupID := uint64(0)
		if gv, ok2 := content["group_id"].(float64); ok2 {
			groupID = uint64(gv)
		}
		var aids []uint64
		if raw, ok2 := content["action_ids"].([]any); ok2 {
			for _, x := range raw {
				if f, ok3 := x.(float64); ok3 {
					aids = append(aids, uint64(f))
				}
			}
		}
		if groupID > 0 {
			if err := d.Access.SetGroupPermissions(groupID, aids); err != nil {
				return err
			}
			// 关联申请单（留痕：谁申请、哪张单）
			d.DB.Model(&model.GroupPermission{}).Where("group_id = ?", groupID).Update("request_id", r.ID)
			d.bumpAllCaches(c)
			d.BundleMgr.Publish(c.Request.Context(), r.AppID)
			return nil
		}
	}

	// 接入申请（Phase 6.5）：签发凭证（client_id/secret，一次性返回明文；后续仅可轮换）
	if r.RequestType == model.RequestOnboard {
		consumerAppID := uint64(0)
		if v, ok := r.Content["consumer_app_id"].(float64); ok {
			consumerAppID = uint64(v)
		}
		authMethod, _ := r.Content["auth_method"].(string)
		if consumerAppID == 0 {
			return fmt.Errorf("onboard: consumer_app_id missing")
		}
		clientID := "client-" + strconv.FormatUint(consumerAppID, 10) + "-" + randHex(4)
		secret := randHex(16)
		hash, err := auth.HashPassword(secret)
		if err != nil {
			return err
		}
		cli := &model.Client{
			AppID:            consumerAppID,
			ClientID:         clientID,
			ClientSecretHash: hash,
			Status:           model.StatusEnabled,
			AuthMethod:       authMethod,
			ProviderAppID:    r.AppID,
		}
		if err := d.Apps.CreateClient(cli); err != nil {
			return err
		}
		r.Content["onboard_secret"] = secret
		r.Content["client_id"] = clientID
		r.Content["onboard_status"] = "issued"
		d.DB.Save(&r)
		d.audit(c, "onboard.credential_issued", "client", clientID,
			gin.H{"provider_app_id": r.AppID, "auth_method": authMethod})
		d.bumpAllCaches(c)
		return nil
	}

	// 来源（留痕）：owner 授权 = owner_grant；自助申请 = via_request；两者都关联申请单
	source := int16(model.SourceViaRequest)
	if r.RequestType == model.RequestGrant {
		source = model.SourceOwnerGrant
	}
	p := &model.Policy{
		Name:          "grant:req:" + strconv.FormatUint(r.ID, 10),
		Effect:        model.EffectAllow,
		SubjectType:   subjectType,
		SubjectID:     subjectID,
		AppID:         r.AppID,
		ActionIDs:     actionIDs,
		ResourceScope: scope,
		Conditions:    map[string]any{},
		Status:        model.PolicyActive,
		CreatedBy:     approver,
		Source:        source,  // owner 授权走审批单后仍留痕（request_id）
		RequestID:     &r.ID,   // 关联申请单（"为什么给我授权"可查）
		CapabilityID:  capabilityID,
		DataScopeType: dataScopeType,
		ExpiresAt:     r.ExpiresAt, // 策略级 TTL
	}
	if err := d.Pol.Create(p); err != nil {
		return err
	}
	// 关联策略模板被申请次数 +1
	if tplID, ok := r.Items["template_id"].(float64); ok && tplID > 0 {
		d.Tpls.IncApply(uint64(tplID))
	}
	if scope != nil {
		d.DataPlane.PublishPolicy(c.Request.Context(), p)
	}
	d.bumpAllCaches(c)
	d.BundleMgr.Publish(c.Request.Context(), r.AppID)
	return nil
}

// ---- 能力打包申请：预览 + 风险组合 + 条件表达式 ----

// previewRequest 申请单预览（不提交）：解析预设 + 风险组合升级 + 审批链 + 条件表达式
// 能力包向导 Step 5 确认页调用，实时展示最终风险等级与审批链
func (d *Deps) previewRequest(c *gin.Context) {
	var req struct {
		AppID           uint64           `json:"app_id"`
		SubjectType     int16            `json:"subject_type"`
		SubjectID       uint64           `json:"subject_id"`
		CapabilityID    uint64           `json:"capability_id"`
		PresetID        string           `json:"preset_id"`
		Scope           string           `json:"scope"`
		ScopeParams     map[string]any   `json:"scope_params"`
		GranteeType     string           `json:"grantee_type"`
		GranteeName     string           `json:"grantee_name"`
		GranteeID       uint64           `json:"grantee_id"`
		ScopeSelections []map[string]any `json:"scope_selections"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.AppID == 0 {
		c.JSON(400, gin.H{"error": "app_id required"})
		return
	}
	applicantID := d.currentUserID(c)
	app, err := d.Apps.ByID(req.AppID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	subjectType := req.SubjectType
	if subjectType == 0 {
		subjectType = model.ReqSubjectUser
	}
	subjectID := req.SubjectID
	if subjectID == 0 {
		subjectID = applicantID
	}
	if subjectType == model.ReqSubjectGroup {
		if _, err := d.Groups.ByID(subjectID); err != nil {
			c.JSON(400, gin.H{"error": "group not found"})
			return
		}
	}
	if subjectType == model.ReqSubjectApp {
		if _, err := d.Apps.ByID(subjectID); err != nil {
			c.JSON(400, gin.H{"error": "app not found"})
			return
		}
	}

	var cap *model.CapabilityManifest
	var preset map[string]any
	var ops []map[string]any
	var actionCodes []string
	if req.CapabilityID > 0 {
		cap, err = d.Caps.ByID(req.CapabilityID)
		if err != nil {
			c.JSON(404, gin.H{"error": "capability not found"})
			return
		}
		if req.PresetID != "" {
			preset = d.findPreset(cap.Presets, req.PresetID)
			if preset == nil {
				c.JSON(400, gin.H{"error": "preset not found in capability"})
				return
			}
			resolved := d.enrichOnePreset(cap.AppID, preset)
			ops, _ = resolved["ops"].([]map[string]any)
			for _, op := range ops {
				if code, ok := op["action"].(string); ok {
					actionCodes = append(actionCodes, code)
				}
			}
		}
	}

	risk := comboRiskFromOps(subjectType, req.Scope, ops)

	// 审批链（不落库，仅预览）
	rm := &model.AccessRequest{
		ApplicantID:          applicantID,
		RequestType:          model.RequestApply,
		ApplicantSubjectType: subjectType,
		ApplicantSubjectID:   subjectID,
		AppID:                req.AppID,
		RiskLevel:            risk,
		Status:               model.ReqPending,
	}
	chain := d.buildApprovalChain(rm, app, applicantID)
	chainView := d.decorateApprovalChain(chain, app)

	// 条件表达式
	var modelCode *string
	if cap != nil && cap.DataModel != nil {
		modelCode = cap.DataModel
	}
	subjName := d.subjectNameForExpression(subjectType, subjectID, req.AppID)
	var engine, exprCode string
	if len(req.ScopeSelections) > 0 && cap != nil && preset != nil {
		engine, exprCode, err = d.buildV12ScopeExpression(cap, preset, req.ScopeSelections, actionCodes, subjName)
		if err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
	} else {
		engine, exprCode = buildScopeExpression(req.Scope, req.ScopeParams, modelCode, actionCodes, subjName)
	}

	// 数据范围标签 + 选中值文本
	scopeLabel, scopeValueText := req.Scope, ""
	if cap != nil && len(req.ScopeSelections) > 0 {
		scopeLabel = "selections"
		scopeValueText = selectionsText(req.ScopeSelections)
	}
	granteeType, granteeName, granteeID := req.GranteeType, req.GranteeName, req.GranteeID
	if granteeType == "" {
		granteeType, granteeName, granteeID = d.granteeFields(subjectType, subjectID)
	}

	c.JSON(200, gin.H{
		"risk_level":     risk,
		"risk_label":     riskLabel(risk),
		"risk_reasons":   riskReasons(subjectType, req.Scope, ops),
		"approval_chain": chainView,
		"scope":          req.Scope,
		"scope_label":    scopeLabel,
		"scope_value_text": scopeValueText,
		"expression": gin.H{
			"engine": engine,
			"code":   exprCode,
		},
		"preset":   preset,
		"capability": cap,
		"grantee": gin.H{"type": granteeType, "name": granteeName, "id": granteeID},
		"scope_selections": req.ScopeSelections,
	})
}

// findPreset 按 id 查找能力预设（presets 为 JSONB 对象数组）
func (d *Deps) findPreset(presets model.JSONAny, presetID string) map[string]any {
	for _, raw := range presets {
		p, _ := raw.(map[string]any)
		if p == nil {
			continue
		}
		if id, ok := p["id"].(string); ok && id == presetID {
			return p
		}
	}
	return nil
}

// comboRiskFromOps 风险组合升级（§5.4）：
//   完整管理（含 delete）→ 高；运维操作（create/update）→ 中；
//   只读 + 所有数据 → 中；下游应用(M2M) → 至少中
func comboRiskFromOps(subjectType int16, scope string, ops []map[string]any) int16 {
	risk := int16(model.RiskLow)
	hasDelete, hasWrite := false, false
	for _, op := range ops {
		switch op["operation"] {
		case model.OpDelete:
			hasDelete = true
		case model.OpCreate, model.OpUpdate:
			hasWrite = true
		}
	}
	switch {
	case hasDelete:
		risk = model.RiskHigh
	case hasWrite:
		risk = model.RiskMedium
	case scope == model.ScopeAll:
		risk = model.RiskMedium // 只读 + 所有数据
	default:
		risk = model.RiskLow
	}
	if subjectType == model.ReqSubjectApp && risk < model.RiskMedium {
		risk = model.RiskMedium // 下游应用 → 至少中
	}
	return risk
}

// riskReasons 风险升级原因（前端展示）
func riskReasons(subjectType int16, scope string, ops []map[string]any) []string {
	var reasons []string
	hasDelete, hasWrite := false, false
	for _, op := range ops {
		switch op["operation"] {
		case model.OpDelete:
			hasDelete = true
		case model.OpCreate, model.OpUpdate:
			hasWrite = true
		}
	}
	if hasDelete {
		reasons = append(reasons, "完整管理组合升级为高风险")
	} else if hasWrite {
		reasons = append(reasons, "运维操作组合至少中风险")
	} else if scope == model.ScopeAll {
		reasons = append(reasons, "只读 + 所有数据升级为中风险")
	}
	if subjectType == model.ReqSubjectApp {
		reasons = append(reasons, "下游应用申请自动升级为中风险")
	}
	return reasons
}

func riskLabel(risk int16) string {
	switch risk {
	case model.RiskLow:
		return "低"
	case model.RiskMedium:
		return "中"
	case model.RiskHigh:
		return "高"
	}
	return "?"
}

// buildScopeExpression 数据范围 + 参数 → 条件表达式（Casbin / OpenFGA 模板）
// 前端 Step 4/5 实时展示；提交时后端同样生成并落申请单留痕
func buildScopeExpression(scope string, params map[string]any, modelCode *string, actions []string, subjName string) (string, string) {
	modelName := "resource"
	if modelCode != nil && *modelCode != "" {
		modelName = *modelCode
	}
	actionStr := strings.Join(actions, ", ")
	if actionStr == "" {
		actionStr = "{actions}"
	}
	subj := subjName
	if subj == "" {
		subj = "{user}"
	}
	switch scope {
	case model.ScopeAll:
		return "Casbin", fmt.Sprintf("p, %s, {app}, %s, *, allow\n// 无数据层限制", subj, actionStr)
	case model.ScopeOwner:
		return "OpenFGA", fmt.Sprintf("// Casbin 动作级\np, %s, {app}, %s, *, allow\n\n// OpenFGA 关系\n(%s:xxx, owner, user:%s)\n→ Check(user:%s, reader, %s:xxx) if owner_id == %s",
			subj, actionStr, modelName, subj, subj, modelName, subj)
	case model.ScopeDimension:
		dim := stringParam(params, "dimension", "value")
		return "OpenFGA", fmt.Sprintf("// Casbin 动作级\np, %s, {app}, %s, *, allow\n\n// OpenFGA 组织维度\n(group:%s, member, user:%s)\n(%s:xxx, org, group:%s)\n→ ListObjects(user:%s, reader, %s)\n  仅返回 org=%s 的实例",
			subj, actionStr, dim, subj, modelName, dim, subj, modelName, dim)
	case "account":
		acc := stringParam(params, "account", "value")
		return "OpenFGA", fmt.Sprintf("// Casbin 动作级\np, %s, {app}, %s, *, allow\n\n// OpenFGA 账号维度\n(cloud_account:%s, member, user:%s)\n(%s:xxx, account, cloud_account:%s)\n→ Check(user:%s, reader, %s:xxx)\n  仅返回账号 %s 的资源",
			subj, actionStr, acc, subj, modelName, acc, subj, modelName, acc)
	case "tag":
		expr := stringParam(params, "expression", "value")
		return "Casbin ABAC", fmt.Sprintf("// ABAC 条件策略\np, %s, {app}, %s,\n  { %s },\n  allow", subj, actionStr, expr)
	case model.ScopeInstance:
		var names []string
		if v, ok := params["instance_names"].([]any); ok {
			for _, x := range v {
				if s, ok := x.(string); ok {
					names = append(names, s)
				}
			}
		}
		if len(names) == 0 {
			return "OpenFGA", "// 未选择实例"
		}
		var b strings.Builder
		b.WriteString("// 直接授权 tuple\n")
		for _, n := range names {
			fmt.Fprintf(&b, "(%s:%s, reader, user:%s)\n", modelName, n, subj)
		}
		b.WriteString("\n// Check\n")
		for _, n := range names {
			fmt.Fprintf(&b, "Check(user:%s, reader, %s:%s) → true\n", subj, modelName, n)
		}
		return "OpenFGA", b.String()
	}
	return "-", ""
}

// buildV12ScopeExpression v12 范围字段类型系统：按模型结构化选择 → CEL（§4.5 规则）
// 字段/操作符/变量取自 owner 配置的 ScopeOption（独立表），applicant 只提供值；
// variable 类型保存变量名，运行时按 grantee（权限作用主体）解析
func (d *Deps) buildV12ScopeExpression(cap *model.CapabilityManifest, preset map[string]any, selections []map[string]any, actions []string, subjName string) (string, string, error) {
	actionStr := strings.Join(actions, ", ")
	if actionStr == "" {
		actionStr = "{actions}"
	}
	subj := subjName
	if subj == "" {
		subj = "{user}"
	}
	presetID, _ := preset["id"].(string)
	var b strings.Builder
	b.WriteString("// Casbin 动作级\n")
	fmt.Fprintf(&b, "p, %s, {app}, %s, *, allow\n", subj, actionStr)
	var conds []string
	var tuples []string
	for _, sel := range selections {
		modelCode, _ := sel["model"].(string)
		typ, _ := sel["type"].(string)
		if typ == "" {
			typ = model.ScopeOptAll
		}
		if typ == model.ScopeOptAll {
			continue
		}
		opts, err := d.Caps.ScopeOptions(cap.ID, presetID, modelCode)
		if err != nil {
			return "", "", err
		}
		var opt *model.ScopeOption
		for i := range opts {
			if opts[i].Type == typ {
				opt = &opts[i]
				break
			}
		}
		if opt == nil {
			return "", "", fmt.Errorf("scope option type %q not configured for model %q", typ, modelCode)
		}
		switch typ {
		case model.ScopeOptInstance:
			for _, n := range anyStrings(sel["selectedValues"]) {
				tuples = append(tuples, fmt.Sprintf("(%s:%s, reader, %s)", modelCode, n, subj))
			}
		case model.ScopeOptSelect:
			cond, cerr := buildConditionCEL(opt.Field, opt.Op, anyString(sel["selectedValue"]), nil)
			if cerr != nil {
				return "", "", cerr
			}
			conds = append(conds, cond)
		case model.ScopeOptMultiSelect:
			cond, cerr := buildConditionCEL(opt.Field, opt.Op, "", anyStrings(sel["selectedValues"]))
			if cerr != nil {
				return "", "", cerr
			}
			conds = append(conds, cond)
		case model.ScopeOptVariable:
			cond, cerr := buildConditionCEL(opt.Field, opt.Op, opt.Variable, nil)
			if cerr != nil {
				return "", "", cerr
			}
			conds = append(conds, cond)
		case model.ScopeOptInput:
			if v := anyString(sel["selectedValue"]); v != "" {
				cond, cerr := buildConditionCEL(opt.Field, opt.Op, v, nil)
				if cerr != nil {
					return "", "", cerr
				}
				conds = append(conds, cond)
			}
		}
	}
	if len(tuples) > 0 {
		b.WriteString("\n// OpenFGA 直接授权 tuple（instance 类型）\n")
		for _, t := range tuples {
			b.WriteString(t + "\n")
		}
	}
	if len(conds) > 0 {
		b.WriteString("\n// OpenFGA 数据级条件（CEL 落库格式；variable 运行时按 grantee 解析）\n")
		for _, c := range conds {
			if err := validateCEL(c); err != nil {
				return "", "", err
			}
			b.WriteString("# " + c + "\n")
		}
	}
	if len(tuples) == 0 && len(conds) == 0 {
		b.WriteString("\n// 无数据层限制（all 类型）\n")
	}
	engine := "Casbin"
	if len(tuples) > 0 || len(conds) > 0 {
		engine = "OpenFGA"
	}
	return engine, b.String(), nil
}

// granteeFields 双主体：由 subjectType/subjectID 派生 grantee（权限作用主体）字符串形态
func (d *Deps) granteeFields(subjectType int16, subjectID uint64) (string, string, uint64) {
	switch subjectType {
	case model.ReqSubjectGroup:
		if g, err := d.Groups.ByID(subjectID); err == nil {
			if g.Type == model.GroupTypeOrg {
				return model.GranteeOrg, g.Name, subjectID
			}
			return model.GranteeGroup, g.Name, subjectID
		}
		return model.GranteeGroup, "", subjectID
	case model.ReqSubjectApp:
		if a, err := d.Apps.ByID(subjectID); err == nil {
			return model.GranteeApp, "client:" + a.Code, subjectID
		}
		return model.GranteeApp, "", subjectID
	default:
		if u, err := d.Users.ByID(subjectID); err == nil {
			return model.GranteeUser, u.Username, subjectID
		}
		return model.GranteeUser, "", subjectID
	}
}

func anyString(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func anyStrings(v any) []string {
	arr, _ := v.([]any)
	var out []string
	for _, x := range arr {
		if s, ok := x.(string); ok {
			out = append(out, s)
		}
	}
	return out
}

// stringParam 从 scope_params 取字符串参数（兼容多 key）
func stringParam(params map[string]any, keys ...string) string {
	for _, k := range keys {
		if params == nil {
			return ""
		}
		if v, ok := params[k].(string); ok {
			return v
		}
	}
	return ""
}

// parseActionIDs 兼容多种 action_ids 形态：
//   - []any（JSON 反序列化，元素为 float64/json.Number/string/uint64）
//   - []uint64（Go 程序构造，如能力包向导 submitRequest）
func parseActionIDs(v any) []uint64 {
	var out []uint64
	switch t := v.(type) {
	case []any:
		for _, x := range t {
			switch n := x.(type) {
			case float64:
				out = append(out, uint64(n))
			case json.Number:
				if iv, err := n.Int64(); err == nil {
					out = append(out, uint64(iv))
				}
			case uint64:
				out = append(out, n)
			case int:
				out = append(out, uint64(n))
			case string:
				if iv, err := strconv.ParseUint(n, 10, 64); err == nil {
					out = append(out, iv)
				}
			}
		}
	case []uint64:
		out = append(out, t...)
	case []int:
		for _, n := range t {
			out = append(out, uint64(n))
		}
	case []float64:
		for _, n := range t {
			out = append(out, uint64(n))
		}
	}
	return out
}

// subjectNameForExpression 条件表达式中的主体名：我→用户名；组/组织→组名；下游应用→应用 code
func (d *Deps) subjectNameForExpression(subjectType int16, subjectID, appID uint64) string {
	switch subjectType {
	case model.ReqSubjectUser:
		if u, err := d.Users.ByID(subjectID); err == nil {
			return u.Username
		}
	case model.ReqSubjectGroup, model.ReqSubjectOrg:
		if g, err := d.Groups.ByID(subjectID); err == nil {
			return g.Name
		}
	case model.ReqSubjectApp:
		if a, err := d.Apps.ByID(subjectID); err == nil {
			return a.Code
		}
	}
	return ""
}

// decorateApprovalChain 审批链用户信息装饰（预览展示）
func (d *Deps) decorateApprovalChain(chain []uint64, app *model.App) []gin.H {
	out := make([]gin.H, 0, len(chain))
	for _, id := range chain {
		role, desc := "应用 Owner", app.Name+" 应用负责人"
		if u, err := d.Users.ByID(id); err == nil {
			// admin 若为该应用 owner 则按 owner 标注；仅当 admin 非 owner 时（高风险追加）标为安全审批
			if u.Username == "admin" && !d.isAppOwner(id, app.ID) {
				role, desc = "安全审批", "高风险复核（安全审批）"
			}
			out = append(out, gin.H{
				"user_id": id, "username": u.Username,
				"display_name": u.DisplayName, "role": role, "desc": desc,
			})
		}
	}
	return out
}

// selectionsText v12 范围选择可读文本（预览/留痕）
func selectionsText(selections []map[string]any) string {
	parts := make([]string, 0, len(selections))
	for _, sel := range selections {
		modelCode, _ := sel["model"].(string)
		typ, _ := sel["type"].(string)
		switch typ {
		case model.ScopeOptAll:
			parts = append(parts, modelCode+": 全部")
		case model.ScopeOptInstance:
			parts = append(parts, modelCode+": 实例 ["+strings.Join(anyStrings(sel["selectedValues"]), ",")+"]")
		case model.ScopeOptSelect:
			parts = append(parts, modelCode+": "+anyString(sel["selectedValue"]))
		case model.ScopeOptMultiSelect:
			parts = append(parts, modelCode+": ["+strings.Join(anyStrings(sel["selectedValues"]), ",")+"]")
		case model.ScopeOptVariable:
			parts = append(parts, modelCode+": 自动匹配")
		case model.ScopeOptInput:
			parts = append(parts, modelCode+": "+anyString(sel["selectedValue"]))
		default:
			parts = append(parts, modelCode+": "+typ)
		}
	}
	return strings.Join(parts, " · ")
}
