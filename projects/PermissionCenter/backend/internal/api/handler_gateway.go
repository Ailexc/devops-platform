package api

import (
	"crypto/rand"
	"encoding/hex"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/authz"
)

// handleGatewayCheck Traefik forwardAuth 回调（PEP→PDP）
// Traefik 把原始请求整体转发到本端点，原始 method/path 经 X-Forwarded-Method / X-Forwarded-Uri 传递；
// 在此完成"请求 → action 映射"（PEP 职责，对应 APISIX ext-authz 行为），再调中心 PDP。
// 200 = 放行；403 = 拦截（deny-by-default）。
func (d *Deps) handleGatewayCheck(c *gin.Context) {
	// 主体：网关透传业务侧身份头
	user := c.GetHeader("X-User")
	if user == "" {
		c.AbortWithStatusJSON(403, gin.H{"error": "X-User header required"})
		return
	}
	appCode := c.GetHeader("X-App")
	if appCode == "" {
		appCode = "cmdb"
	}

	// 原始请求的 method / path（Traefik 注入的转发头）
	method := c.GetHeader("X-Forwarded-Method")
	if method == "" {
		method = c.Request.Method
	}
	uri := c.GetHeader("X-Forwarded-Uri")
	if uri == "" {
		uri = c.Request.URL.Path
	}
	path := uri
	if i := strings.IndexByte(uri, '?'); i >= 0 {
		path = uri[:i]
	}

	app, err := d.Apps.ByCode(appCode)
	if err != nil {
		c.AbortWithStatusJSON(403, gin.H{"error": "app not found: " + appCode})
		return
	}
	// X-Resource-Type：统一查询入口（/api/v1/entities）经此头解析真实资源类型（网关可信边界注入）
	resourceType := c.GetHeader("X-Resource-Type")
	trace := d.Access.ResolveActionSteps(app.ID, method, path, resourceType)
	if trace.Action == nil {
		// deny-by-default：未注册路径 / 通用接口无法落具体资源类型（防权限漂移）
		c.AbortWithStatusJSON(403, gin.H{"error": "no action resolved for " + method + " " + path})
		return
	}

	// 链路追踪：TraceID 贯穿 PEP → PDP（决策日志），PEP 解析细节随日志落库
	traceID := c.GetHeader("X-Trace-ID")
	if traceID == "" {
		traceID = newTraceID()
	}
	pepInfo := map[string]any{
		"method": method, "path": path,
		"match_mode": trace.MatchMode, "pattern": trace.PathPattern,
		"resolved_resource": trace.ResolvedResource,
		"action":            trace.Action.Code,
		// 路由表版本快照（§3.9）：判定审计可复现"当时按哪版路由表判的"
		"route_version": d.Access.CurrentRouteVersion(app.ID),
		"steps":         trace.Steps,
	}
	dec, _, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
		User:    user,
		App:     appCode,
		Action:  trace.Action.Code,
		Context: map[string]any{"ip": c.ClientIP()},
		TraceID: traceID,
		PEP:     pepInfo,
	})
	if err != nil || !dec.Allow {
		c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "NO_PERMISSION"})
		return
	}
	c.Status(200)
}

// newTraceID 生成链路追踪 ID（8 字节随机 hex）
func newTraceID() string {
	b := make([]byte, 8)
	rand.Read(b)
	return hex.EncodeToString(b)
}
