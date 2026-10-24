package api

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"log"
	"net/url"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/material"
	"github.com/xcy/permission-center/internal/model"
)

// Traefik 把原始请求整体转发到本端点，原始 method/path 经 X-Forwarded-Method / X-Forwarded-Uri 传递；
// 在此完成"请求 → action 映射"（PEP 职责，对应 APISIX ext-authz 行为），再调中心 PDP。
// 200 = 放行；403 = 拦截（deny-by-default）。
func (d *Deps) handleGatewayCheck(c *gin.Context) {
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

	// ---- T4 凭证豁免（§3.1）：豁免主语=中心 M2M 凭证，不是路由 ----
	// 路径命中豁免表 + 携带绑定凭证验证通过 → 跳过判定（点查/回源防递归同款规则，审计留痕）；
	// 凭证缺失/不匹配 → 普通请求照常判（普通用户同接口照常判）；裸豁免（未绑凭证）运行时 fail-closed + 体检阻断。
	if raw, hit := app.ExemptPaths[path]; hit {
		want, _ := raw.(string)
		clientID := c.GetHeader("X-Client-ID")
		if want != "" && clientID == want {
			if cli, cerr := d.Apps.ClientByID(clientID); cerr == nil &&
				cli.AppID == app.ID && cli.Status == model.StatusEnabled &&
				auth.CheckPassword(cli.ClientSecretHash, c.GetHeader("X-Client-Secret")) {
				log.Printf("[gw][exempt] app=%s path=%s client=%s 豁免放行（M2M 凭证匹配，免判定）",
					app.Code, path, clientID)
				c.JSON(200, gin.H{"ok": true, "exempt": true})
				return
			}
		}
		// 命中豁免表但凭证不匹配 → 落回正常判定链（未注册动作则 deny-by-default）
	}

	// 主体：网关透传业务侧身份头（豁免放行在前——M2M 回调无业务用户头）
	user := c.GetHeader("X-User")
	if user == "" {
		c.AbortWithStatusJSON(403, gin.H{"error": "X-User header required"})
		return
	}

	// X-Resource-Type：统一查询入口（/api/v1/entities）经此头解析真实资源类型（网关可信边界注入）
	resourceType := c.GetHeader("X-Resource-Type")
	trace := d.Access.ResolveActionSteps(app.ID, method, path, resourceType)
	if trace.Action == nil {
		// deny-by-default：未注册路径 / 通用接口无法落具体资源类型（防权限漂移）
		// T4 告警打点（§3.9 M6 失配闭环）：失配=配置问题（URL 改版没重新导入），必须可被告警发现
		log.Printf("[ALERT][gw403] 失配未命中 app=%s user=%s %s %s——路由表无此动作（发版重新导入?）",
			appCode, user, method, path)
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
	dec, matchedPids, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
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

	// ---- T5 列表判定两步（§5.2 元组集合语义）：契约登记的 list 动作 → 缺参拒 / 子集校验 ----
	// 中心自 X-Forwarded-Uri 的 query 按契约参数位置取值（不依赖前端诚实；授权集=本次回调实时按策略计算）
	if trace.Action.ScopeParam != nil {
		if pname, _ := trace.Action.ScopeParam["param"].(string); pname != "" {
			rawQuery := ""
			if i := strings.IndexByte(uri, '?'); i >= 0 {
				rawQuery = uri[i+1:]
			}
			q, _ := url.ParseQuery(rawQuery)
			reqVals := authz.ParseScopeParamList(q.Get(pname))
			required, _ := trace.Action.ScopeParam["required"].(bool)
			if len(reqVals) == 0 && required {
				d.logDecision(traceID, user, app, trace.Action.Code, method+" "+path, false, "missing_scope_param（列表缺契约范围参数）", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "MISSING_SCOPE_PARAM"})
				return
			}
			if len(reqVals) > 0 {
				full, vals := authz.AuthorizedScopeValues(matchedPids, d.Pol, trace.Action.Resource, pname)
				if bad, ok := authz.SubsetCheck(reqVals, full, vals); !ok {
					pepInfo["list_scope"] = map[string]any{"param": pname, "requested": reqVals}
					d.logDecision(traceID, user, app, trace.Action.Code, method+" "+path, false,
						"list scope not matched（请求值 "+bad+" 超授权集合）", pepInfo)
					c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "NO_PERMISSION"})
					return
				}
				pepInfo["list_scope"] = map[string]any{"param": pname, "requested": reqVals, "full_access": full}
			}
		}
	}

	// ---- T2 数据级：点查取材（§3.5 网关链路即判）----
	// 仅 id_path 且 path.* 声明在网关判（网关持有 URI）；body.*/信封/需 body 的回源 → 带体调用通道。
	// 行=权威行实时点查——不过新鲜度门（无新鲜度税，§3.2）。
	matMode, _ := trace.Action.Material["mode"].(string)
	if trace.Action.NeedData && matMode == "id_path" {
		declPath, _ := trace.Action.Material["path"].(string)
		if declPath == "" || strings.HasPrefix(declPath, "path.") {
			name := strings.TrimPrefix(declPath, "path.")
			id, ok := material.ExtractPathParam(trace.PathPattern, path, name)
			if !ok {
				d.logDecision(traceID, user, app, trace.Action.Code, method+" "+path, false, "material: id 不可从路径提取（fail-closed）", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "MATERIAL_MISSING"})
				return
			}
			pepInfo["material"] = map[string]any{"mode": "id_path", "id": id, "source": "point_query"}
			if app.PermQueryURL == "" {
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "material: 应用未配置回查地址", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "DATA_SOURCE_UNCONFIGURED"})
				return
			}
			// 模型白名单：仅已登记数据契约的域（§3.1 防查任意表）
			if _, cerr := d.Contracts.ByModelCode(trace.Action.Resource); cerr != nil {
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "material: 数据域未登记契约（白名单外）", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "MODEL_NOT_REGISTERED"})
				return
			}
			row, rerr := d.Mat.FetchRow(c.Request.Context(), app.PermQueryURL, app.PermQueryToken, trace.Action.Resource, id)
			switch {
			case rerr == nil:
			case errors.Is(rerr, material.ErrNotFound):
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "data_missing", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "DATA_MISSING"})
				return
			default:
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "material: "+rerr.Error()+"（fail-closed，无隐式降级）", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "DATA_SOURCE_UNAVAILABLE"})
				return
			}
			allow, reason, cerr := d.DataPlane.CheckRow(subjectOFGAKey(user), trace.Action.Resource, id, row, matchedPids)
			if cerr != nil {
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "data engine: "+cerr.Error(), pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": "DATA_ENGINE_UNAVAILABLE"})
				return
			}
			if !allow {
				code := "NO_PERMISSION"
				if reason == "data_missing" {
					code = "DATA_MISSING"
				}
				d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, false, "scope not matched（范围谓词不匹配）", pepInfo)
				c.AbortWithStatusJSON(403, gin.H{"error": "denied", "code": code})
				return
			}
			d.logDecision(traceID, user, app, trace.Action.Code, trace.Action.Resource+":"+id, true, "point query check（权威行实时判定）", pepInfo)
		}
	}
	c.Status(200)
}

// newTraceID 生成链路追踪 ID（8 字节随机 hex）
func newTraceID() string {
	b := make([]byte, 8)
	rand.Read(b)
	return hex.EncodeToString(b)
}
