package api

import (
	"encoding/json"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

type policyReq struct {
	Name          string         `json:"name"`
	Effect        int16          `json:"effect"` // 1=allow 2=deny
	SubjectType   int16          `json:"subject_type"`
	SubjectID     uint64         `json:"subject_id"`
	AppID         uint64         `json:"app_id"`
	ActionIDs     []uint64       `json:"action_ids"`
	ResourceScope map[string]any `json:"resource_scope"`
	Conditions    map[string]any `json:"conditions"`
	ForceRemote   bool           `json:"force_remote"`
}

func (d *Deps) listPolicies(c *gin.Context) {
	var appID *uint64
	if v := c.Query("app_id"); v != "" {
		if id, err := strconv.ParseUint(v, 10, 64); err == nil {
			appID = &id
		}
	}
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	ps, total, err := d.Pol.List(appID, offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": ps, "total": total})
}

// createPolicy 发起 owner 授权（授权即审批：无直授后门）
// 不再直接创建生效策略：生成授权申请单（grant 方向），被授权方确认 + 应用其他 owner 复核，
// 全部通过后才生成策略并关联申请单留痕
func (d *Deps) createPolicy(c *gin.Context) {
	var req struct {
		Name          string         `json:"name"`
		Effect        int16          `json:"effect"`
		SubjectType   int16          `json:"subject_type"` // 1=user 2=group 3=service
		SubjectID     uint64         `json:"subject_id"`
		AppID         uint64         `json:"app_id"`
		ActionIDs     []uint64       `json:"action_ids"`
		ResourceScope map[string]any `json:"resource_scope"`
		Conditions    map[string]any `json:"conditions"`
		ForceRemote   bool           `json:"force_remote"`
		Reason        string         `json:"reason"` // 授权理由（必填，"为什么给我授权"）
		ExpiresAt     *time.Time     `json:"expires_at"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.SubjectID == 0 || req.AppID == 0 {
		c.JSON(400, gin.H{"error": "subject_id/app_id required"})
		return
	}
	applicantID := d.currentUserID(c)
	app, err := d.Apps.ByID(req.AppID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	if !d.isAppOwner(applicantID, req.AppID) {
		c.JSON(403, gin.H{"error": "only app owner can grant permissions"})
		return
	}

	// 主体类型 → 申请单主体枚举
	subjType := int16(model.ReqSubjectUser)
	switch req.SubjectType {
	case model.SubjectGroup:
		subjType = model.ReqSubjectGroup
	case model.SubjectService:
		subjType = model.ReqSubjectApp
	}
	// 被授权主体存在性
	if subjType == model.ReqSubjectGroup {
		if _, err := d.Groups.ByID(req.SubjectID); err != nil {
			c.JSON(400, gin.H{"error": "group not found"})
			return
		}
	}

	// 风险：写操作/数据范围/高权限 → 中或高；默认中（授权需双方确认，不给低风险自动）
	risk := int16(model.RiskMedium)
	if req.ForceRemote || req.ResourceScope != nil {
		risk = model.RiskHigh
	}

	r := &model.AccessRequest{
		ApplicantID:          applicantID,
		RequestType:          model.RequestGrant,
		ApplicantSubjectType: subjType,
		ApplicantSubjectID:   req.SubjectID,
		AppID:                req.AppID,
		Content: map[string]any{
			"name": req.Name, "effect": req.Effect, "action_ids": req.ActionIDs,
			"resource_scope": req.ResourceScope, "conditions": req.Conditions,
			"force_remote": req.ForceRemote, "subject_type": req.SubjectType, "subject_id": req.SubjectID,
		},
		Reason:    req.Reason,
		RiskLevel: risk,
		Status:    model.ReqPending,
		ExpiresAt: req.ExpiresAt,
	}
	if err := d.DB.Create(r).Error; err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	// 授权方向不走自动审批：必须被授权方确认
	chain := d.buildApprovalChain(r, app, applicantID)
	d.audit(c, "policy.grant.request", "request", strconv.FormatUint(r.ID, 10),
		gin.H{"app_id": req.AppID, "subject_type": req.SubjectType, "subject_id": req.SubjectID, "reason": req.Reason, "chain": chain})
	c.JSON(201, gin.H{"id": r.ID, "status": "pending", "request_type": "grant", "approval_chain": chain})
}

func (d *Deps) updatePolicy(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	p, err := d.Pol.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "policy not found"})
		return
	}
	var req policyReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	if req.Name != "" {
		p.Name = req.Name
	}
	if req.Effect != 0 {
		p.Effect = req.Effect
	}
	if req.ActionIDs != nil {
		p.ActionIDs = req.ActionIDs
	}
	if req.ResourceScope != nil {
		p.ResourceScope = req.ResourceScope
	}
	if req.Conditions != nil {
		p.Conditions = req.Conditions
	}
	if err := d.Pol.Update(p); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.bumpAllCaches(c)
	d.audit(c, "policy.update", "policy", strconv.FormatUint(id, 10), nil)
	c.JSON(200, p)
}

// publishPolicy 发布：version++ + 快照 + 生成 bundle + 数据策略写 OpenFGA 关系
func (d *Deps) publishPolicy(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		Reason string `json:"reason"`
	}
	c.ShouldBindJSON(&req)
	p, err := d.Pol.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "policy not found"})
		return
	}

	// 1. 快照历史
	content, _ := json.Marshal(p)
	d.Pol.CreateVersion(&model.PolicyVersion{
		PolicyID:  p.ID,
		Version:   p.Version,
		Content:   map[string]any{"policy": string(content)},
		ChangedBy: d.currentUserID(c),
		Reason:    req.Reason,
	})
	// 2. version++
	p.Version++
	if err := d.Pol.Update(p); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 3. 数据策略 → OpenFGA 关系（Write）
	if p.ResourceScope != nil {
		if p.Status == model.PolicyActive {
			d.DataPlane.PublishPolicy(c.Request.Context(), p)
		} else {
			d.DataPlane.RevokePolicy(c.Request.Context(), p)
		}
	}

	// 4. 缓存失效 + bundle 生成（动作级）
	d.bumpAllCaches(c)
	if _, err := d.BundleMgr.Publish(c.Request.Context(), p.AppID); err != nil {
		c.JSON(500, gin.H{"error": "bundle publish: " + err.Error()})
		return
	}
	d.audit(c, "policy.publish", "policy", strconv.FormatUint(id, 10), gin.H{"version": p.Version, "reason": req.Reason})
	c.JSON(200, gin.H{"ok": true, "version": p.Version})
}

func (d *Deps) policyVersions(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	vs, err := d.Pol.Versions(id)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": vs})
}
