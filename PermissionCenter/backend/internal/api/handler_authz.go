package api

import (
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/model"
)

// handleCheck 动作级鉴权（供网关 APISIX ext-authz / 下游）
func (d *Deps) handleCheck(c *gin.Context) {
	var req authz.CheckRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	dec, _, err := d.Checker.CheckWithPids(c.Request.Context(), req)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	if dec.Allow {
		c.JSON(200, gin.H{"decision": "allow"})
		return
	}
	c.JSON(403, gin.H{"decision": "deny", "code": dec.Code, "message": dec.Reason})
}

// handleCheckInstance 数据点操作：Casbin(动作) 短路 + OpenFGA Check(实例)
func (d *Deps) handleCheckInstance(c *gin.Context) {
	var req struct {
		User       string `json:"user"`
		App        string `json:"app"`
		Action     string `json:"action"`
		Model      string `json:"model"`
		InstanceID string `json:"instance_id"`
		Operation  string `json:"operation"`
		TraceID    string `json:"trace_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	app, _ := d.Apps.ByCode(req.App)
	start := time.Now()
	// 动作级短路
	dec, matchedPids, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
		User:    req.User,
		App:     req.App,
		Action:  req.Action,
		TraceID: req.TraceID,
		PEP:     map[string]any{"engine": "action", "model": req.Model, "operation": req.Operation},
	})
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	if !dec.Allow {
		d.logDecision(req.TraceID, req.User, app, req.Action, req.Model+":"+req.InstanceID, false, "action denied", map[string]any{"engine": "data", "model": req.Model, "instance": req.InstanceID, "step": "action_short_circuit"})
		c.JSON(403, gin.H{"decision": "deny", "code": dec.Code, "message": "action denied"})
		return
	}
	// 实例级（OpenFGA）
	userKey := subjectOFGAKey(req.User)
	allow, err := d.DataPlane.CheckInstance(c.Request.Context(), userKey, req.Action, req.Model, req.InstanceID, req.Operation, matchedPids)
	if err != nil {
		// OpenFGA 不可用 → 数据级 fail-closed
		d.logDecision(req.TraceID, req.User, app, req.Action, req.Model+":"+req.InstanceID, false, "data engine unavailable", map[string]any{"engine": "data", "model": req.Model, "instance": req.InstanceID, "error": err.Error()})
		c.JSON(503, gin.H{"decision": "deny", "code": "DATA_ENGINE_UNAVAILABLE", "message": err.Error()})
		return
	}
	d.logDecision(req.TraceID, req.User, app, req.Action, req.Model+":"+req.InstanceID, allow, "openfga check", map[string]any{
		"engine": "data", "model": req.Model, "instance": req.InstanceID,
		"operation": req.Operation, "matched_policy_count": len(matchedPids),
		"latency_ms": time.Since(start).Milliseconds(),
	})
	if allow {
		c.JSON(200, gin.H{"decision": "allow"})
		return
	}
	c.JSON(403, gin.H{"decision": "deny", "code": "NO_PERMISSION", "message": "instance not permitted"})
}

// handleFilter 数据列表：OpenFGA ListObjects → 允许实例集
func (d *Deps) handleFilter(c *gin.Context) {
	var req struct {
		User    string `json:"user"`
		App     string `json:"app"`
		Action  string `json:"action"`
		Model   string `json:"model"`
		TraceID string `json:"trace_id"`
		Query   struct {
			Page int `json:"page"`
			Size int `json:"size"`
		} `json:"query"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	app, _ := d.Apps.ByCode(req.App)
	start := time.Now()
	dec, matchedPids, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
		User:    req.User,
		App:     req.App,
		Action:  req.Action,
		TraceID: req.TraceID,
		PEP:     map[string]any{"engine": "action", "model": req.Model, "op": "list"},
	})
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	if !dec.Allow {
		c.JSON(403, gin.H{"decision": "deny", "code": dec.Code, "message": "action denied"})
		return
	}
	userKey := subjectOFGAKey(req.User)
	result, err := d.DataPlane.Filter(c.Request.Context(), userKey, req.Action, req.Model, "read", matchedPids)
	if err != nil {
		c.JSON(503, gin.H{"decision": "deny", "code": "DATA_ENGINE_UNAVAILABLE", "message": err.Error()})
		return
	}
	d.logDecision(req.TraceID, req.User, app, req.Action, req.Model, true, "openfga list-objects", map[string]any{
		"engine": "data", "model": req.Model, "op": "list",
		"visible_instances": len(result.InstanceIDs), "instance_ids": result.InstanceIDs,
		"matched_policy_count": len(matchedPids), "latency_ms": time.Since(start).Milliseconds(),
	})
	c.JSON(200, gin.H{
		"instance_ids":    result.InstanceIDs,
		"total":           len(result.InstanceIDs),
		"scope_condition": result.ScopeCondition,
	})
}

// logDecision 写一条链路追踪决策日志（数据级等 PEP 外部步骤）
func (d *Deps) logDecision(traceID, user string, app *model.App, action, resource string, allow bool, reason string, pep map[string]any) {
	userID := uint64(0)
	if !strings.HasPrefix(user, "client:") {
		if u, err := d.Users.ByUsername(user); err == nil {
			userID = u.ID
		}
	}
	dec := model.DecisionAllow
	if !allow {
		dec = model.DecisionDeny
	}
	appID := uint64(0)
	if app != nil {
		appID = app.ID
	}
	go func() {
		d.Syncs.CreateDecision(&model.DecisionLog{
			TraceID:  traceID,
			UserID:   userID,
			AppID:    appID,
			Action:   action,
			Resource: resource,
			Decision: int16(dec),
			Reason:   reason,
			Channel:  model.ChannelRemote,
			PEP:      pep,
		})
	}()
}



// subjectOFGAKey 用户/服务 → OpenFGA 主体 key
func subjectOFGAKey(user string) string {
	if strings.HasPrefix(user, "client:") {
		return "service:" + strings.TrimPrefix(user, "client:")
	}
	return "user:" + user
}
