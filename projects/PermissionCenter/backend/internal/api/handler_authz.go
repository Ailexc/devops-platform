package api

import (
	"strings"

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

// handleCheckInstance / handleFilter 已随投影机制退役（1.5 T3，方案 §2/§9 #1）：
// 数据级判定统一走网关链路（path 材料）与带体调用 /v1/authz/check-material（body/信封材料），
// 取材一律点查权威行——投影存在性/新鲜度门/OpenFGA 关系检查不再参与判定。

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

// subjectOFGAKey 用户/服务 → 判定主体 key（保留通道合同参数名；1.5：关系引擎已退役）
func subjectOFGAKey(user string) string {
	if strings.HasPrefix(user, "client:") {
		return "service:" + strings.TrimPrefix(user, "client:")
	}
	return "user:" + user
}
