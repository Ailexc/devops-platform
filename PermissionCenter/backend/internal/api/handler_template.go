package api

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// templateReq 策略模板请求（L3 可复用授权形状）
type templateReq struct {
	Name         string         `json:"name"`
	Description  string         `json:"description"`
	CapabilityID *uint64        `json:"capability_id"`
	ActionIDs    []uint64       `json:"action_ids"`
	DataScope    map[string]any `json:"data_scope"`
	DefaultScope string         `json:"default_scope"`
	TTLDays      int            `json:"ttl_days"`
	Effect       int16          `json:"effect"`
}

// listTemplates 应用的策略模板清单（L3，替换已退役的板块模板）
func (d *Deps) listTemplates(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	ts, err := d.Tpls.List(appID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	type out struct {
		model.PolicyTemplate
		Actions []model.Action `json:"actions"`
	}
	items := make([]out, 0, len(ts))
	for _, t := range ts {
		acts, _ := d.Access.ActionsByIDs(t.ActionIDs)
		items = append(items, out{t, acts})
	}
	c.JSON(200, gin.H{"items": items})
}

// createTemplate 创建策略模板（仅 owner）
func (d *Deps) createTemplate(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req templateReq
	if err := c.ShouldBindJSON(&req); err != nil || req.Name == "" {
		c.JSON(400, gin.H{"error": "name required"})
		return
	}
	if len(req.ActionIDs) == 0 {
		c.JSON(400, gin.H{"error": "action_ids required"})
		return
	}
	eff := req.Effect
	if eff == 0 {
		eff = model.EffectAllow
	}
	t := &model.PolicyTemplate{
		AppID:         appID,
		Name:          req.Name,
		Description:   req.Description,
		CapabilityID:  req.CapabilityID,
		ActionIDs:     req.ActionIDs,
		DataScope:     req.DataScope,
		DefaultScope:  req.DefaultScope,
		TTLDays:       req.TTLDays,
		Effect:        eff,
		Version:       1,
		Status:        "draft",
		PublishedBy:   d.currentUserID(c),
	}
	if err := d.Tpls.Create(t); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "template.create", "template", strconv.FormatUint(t.ID, 10), gin.H{"app_id": appID})
	c.JSON(201, t)
}

// updateTemplate 更新策略模板（仅 owner；版本自增）
func (d *Deps) updateTemplate(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	t, err := d.Tpls.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "template not found"})
		return
	}
	var req templateReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	if req.Name != "" {
		t.Name = req.Name
	}
	if req.Description != "" {
		t.Description = req.Description
	}
	if req.CapabilityID != nil {
		t.CapabilityID = req.CapabilityID
	}
	if req.ActionIDs != nil {
		t.ActionIDs = req.ActionIDs
	}
	if req.DataScope != nil {
		t.DataScope = req.DataScope
	}
	if req.DefaultScope != "" {
		t.DefaultScope = req.DefaultScope
	}
	if req.TTLDays != 0 {
		t.TTLDays = req.TTLDays
	}
	t.Version++
	if err := d.Tpls.Update(t); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "template.update", "template", strconv.FormatUint(id, 10), gin.H{"version": t.Version})
	c.JSON(200, t)
}

// publishTemplate 发布 / 下架策略模板
func (d *Deps) publishTemplate(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		Status string `json:"status"` // published / disabled
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	t, err := d.Tpls.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "template not found"})
		return
	}
	uid := d.currentUserID(c)
	if req.Status == "published" {
		now := time.Now()
		t.Status = "published"
		t.PublishedAt = &now
		t.PublishedBy = uid
	} else if req.Status == "disabled" {
		t.Status = "disabled"
	} else {
		c.JSON(400, gin.H{"error": "status must be published|disabled"})
		return
	}
	if err := d.Tpls.Update(t); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "template.publish", "template", strconv.FormatUint(id, 10), gin.H{"status": t.Status})
	c.JSON(200, t)
}

// deleteTemplate 删除策略模板
func (d *Deps) deleteTemplate(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	if err := d.Tpls.Delete(id); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "template.delete", "template", strconv.FormatUint(id, 10), nil)
	c.JSON(200, gin.H{"ok": true})
}
