package api

import (
	"github.com/gin-gonic/gin"

	"github.com/xcy/permission-center/internal/auth"
)

// NewRouter 构建路由
// /api/v1 管理 API（JWT 保护）；/v1/authz 鉴权 API（PEP 共享密钥）；/v1/oauth 程序身份
func NewRouter(d *Deps) *gin.Engine {
	r := gin.Default()

	r.GET("/healthz", func(c *gin.Context) { c.JSON(200, gin.H{"status": "ok"}) })

	// ---- 公开 ----
	api := r.Group("/api/v1")
	api.POST("/auth/login", d.handleLogin)
	api.POST("/auth/refresh", d.handleRefresh)
	api.GET("/auth/people", d.handlePeople)         // demo 登录人员列表
	api.POST("/auth/demo-login", d.handleDemoLogin) // demo 一键登录（免密码）

	// ---- 管理 API（JWT 保护 + 管理面 PEP 授权域边界）----
	// 网关信任接入：统一网关 forwardAuth 通过后注入 X-Auth-Username，直接放行
	mg := api.Group("", auth.GatewayTrust(), jwtMiddleware(d), d.mgScope)
	{
		// 用户
		mg.GET("/users/me", d.getCurrentUser)
		mg.GET("/users", d.listUsers)
		mg.POST("/users", d.createUser)
		mg.PATCH("/users/:id", d.updateUser)
		// 我的视图（以我为中心，FR-1/FR-2）
		mg.GET("/me/overview", d.meOverview)
		mg.GET("/me/permissions", d.mePermissions)
		mg.GET("/me/capability-permissions", d.meCapabilityPermissions)
		mg.GET("/me/org/permissions", d.meOrgPermissions)
		mg.GET("/me/capabilities/:cid/presets", d.meCapabilityPresets)
		mg.POST("/me/capabilities/:cid/presets/:pid/revoke", d.meRevokePreset)
		mg.GET("/me/groups", d.meGroups)
		// 组织/组
		mg.GET("/groups", d.listGroups)
		mg.POST("/groups", d.createGroup)
		mg.PATCH("/groups/:id", d.updateGroup)
		mg.POST("/groups/:id/members", d.addMember)
		mg.DELETE("/groups/:id/members/:uid", d.removeMember)
		// 应用
		mg.GET("/apps", d.listApps)
		mg.GET("/apps/:id", d.appDetail)
		mg.POST("/apps", d.registerApp)
		mg.POST("/apps/:id/sync", d.syncApp)
		mg.GET("/apps/:id/actions", d.listActions)
		// v1.5 T1 动作码路由表（§3.7 五格登记 / §3.8 导入推断 / §3.9 生命周期）
		mg.GET("/apps/:id/routes", d.listRoutes)
		mg.POST("/apps/:id/routes", d.importRoutes)
		mg.PATCH("/apps/:id/routes/:rid", d.updateRouteRegistration)
		mg.POST("/apps/:id/routes/:rid/migrate-code", d.migrateRouteCode)
		mg.POST("/apps/:id/routes/:rid/archive", d.archiveRoute)
		mg.POST("/apps/:id/routes/:rid/restore", d.restoreRoute)
		mg.POST("/apps/:id/pending-routes/:pid/confirm", d.confirmPending)
		mg.POST("/apps/:id/pending-routes/:pid/discard", d.discardPending)
		// T2 通用点查配置（§3.1 应用注册：回查地址+M2M 凭证，owner）
		mg.PUT("/apps/:id/perm-query", d.setPermQuery)
		// T4 接入体检（§3.9 五类硬校验，报告回执——注册/导入时也自动跑）
		mg.GET("/apps/:id/onboard-report", d.onboardReport)
		mg.PUT("/apps/:id/exempt-paths", d.setExemptPaths)
		// 能力声明（L1，仅 owner）
		mg.GET("/apps/:id/capabilities", d.listCapabilities)
		mg.POST("/apps/:id/capabilities", d.createCapability)
		mg.PUT("/apps/:id/capabilities/:cid", d.updateCapability)
		mg.DELETE("/apps/:id/capabilities/:cid", d.deleteCapability)
		mg.POST("/apps/:id/capabilities/:cid/publish", d.publishCapability)
		mg.GET("/apps/:id/capabilities/:cid/authz", d.capabilityAuthz)
		mg.POST("/apps/:id/sync-capabilities", d.syncCapabilities)
		mg.POST("/apps/:id/validate", d.validateApp)
		// 策略模板（L3，仅 owner）
		mg.GET("/apps/:id/templates", d.listTemplates)
		mg.POST("/apps/:id/templates", d.createTemplate)
		mg.PUT("/apps/:id/templates/:tid", d.updateTemplate)
		mg.DELETE("/apps/:id/templates/:tid", d.deleteTemplate)
		mg.POST("/apps/:id/templates/:tid/publish", d.publishTemplate)
		// 双向账本（FR-7）
		mg.GET("/apps/:id/accessors", d.listAccessors)
		mg.GET("/apps/:id/accessors/:sid/grants", d.accessorGrants)
		mg.GET("/apps/:id/upstreams", d.listUpstreams)
		mg.POST("/grants/:id/revoke", d.revokeGrant)
		mg.GET("/revoke-requests", d.listRevokeRequests)
		mg.POST("/revoke-requests/:id/approve", d.approveRevokeRequest)
		// 权限市场（FR-3）
		mg.GET("/marketplace/capabilities", d.marketplaceCapabilities)
		mg.GET("/marketplace/capabilities/:cid/prereqs", d.marketplacePrereqs)
		mg.GET("/marketplace/templates", d.marketplaceTemplates)
		// 应用市场公开目录（申请接入用：网络/鉴权公开，不含管理信息）
		mg.GET("/marketplace/apps", d.marketplaceApps)
		mg.GET("/marketplace/apps/:id", d.marketplaceAppDetail)
		mg.GET("/marketplace/recommend", d.marketplaceRecommend) // T7 共现推荐（非依赖）
		// 能力打包申请（能力包向导）：范围选项（预设×模型粒度）+ 元数据 + 校验 + 申请单预览
		mg.GET("/capabilities/:cid/presets/:pid/models/:mc/options", d.presetScopeOptions)
		mg.GET("/capabilities/:cid/presets/:pid/scope-meta", d.presetScopeMeta)
		mg.POST("/capabilities/:cid/presets/:pid/scope-options/validate", d.validateScopeOptions)
		mg.POST("/capabilities/:cid/presets/:pid/models/:mc/options", d.savePresetScopeOptions)
		mg.POST("/requests/preview", d.previewRequest)
		mg.POST("/apps/:id/owners", d.addOwner)
		mg.POST("/apps/:id/clients", d.createClient)
		mg.POST("/apps/:id/clients/:cid/rotate", d.rotateClient)
		// 组权限（组即角色）
		mg.POST("/groups/:id/permissions", d.setGroupPermissions)
		mg.GET("/groups/:id/permissions", d.getGroupPermissions)
		mg.GET("/groups/:id/capability-permissions", d.getGroupCapabilityPermissions)
		// 策略
		mg.GET("/policies", d.listPolicies)
		mg.POST("/policies", d.createPolicy)
		mg.PATCH("/policies/:id", d.updatePolicy)
		mg.POST("/policies/:id/publish", d.publishPolicy)
		mg.GET("/policies/:id/versions", d.policyVersions)
		// 资源索引
		mg.GET("/resource-models", d.listResourceModels)
		mg.GET("/resource-models/:id/instances", d.listResourceInstances)
		// 同步（1.5：CMDB 运行期同步已下线——资源目录=seed 时快照；身份同步保留）
		mg.POST("/sync/identity", d.syncIdentity)
		// 申请/审批
		mg.POST("/requests", d.submitRequest)
		mg.GET("/requests", d.listRequests)
		mg.GET("/requests/:id", d.requestDetail)
		mg.POST("/requests/:id/approve", d.approveRequest)
		// A8 定制需求卡：非目录请求创建与 owner 处置（grant 直授带 TTL / package 转为能力包）
		mg.POST("/apps/:id/custom-requests", d.createCustomRequest)
		mg.POST("/requests/:id/fulfill", d.fulfillCustomRequest)
		// 审批中心统一工单视图（内部 mock 聚合）
		mg.GET("/tickets", d.listTickets)
		// 系统观测（黑盒显性化：鉴权链路/PEP解析/PIP身份/Agent/分发/同步）
		mg.POST("/debug/resolve", d.debugResolve)
		mg.GET("/debug/pip/:user", d.debugPIP)
		mg.GET("/debug/cache", d.debugCache)
		mg.POST("/debug/cache/clear", d.debugCacheClear)
		mg.GET("/debug/metrics", d.debugMetrics)
		mg.GET("/debug/owners", d.debugOwners)
		mg.GET("/agents", d.listAgents)
		mg.GET("/apps/:id/bundles", d.listBundles)
		mg.GET("/sync-jobs", d.listSyncJobs)
		// 系统知识库（复盘文档：目录 + HTML 内容）
		mg.GET("/knowledge/docs", d.listKnowledgeDocs)
		mg.GET("/knowledge/docs/:id", d.getKnowledgeDoc)
		// 审计（含我的三视图 FR-8）
		mg.GET("/audit-logs", d.listAuditLogs)
		mg.GET("/decision-logs", d.listDecisionLogs)
		mg.GET("/audit/my-requests", d.auditMyRequests)
		mg.GET("/audit/my-approvals", d.auditMyApprovals)
		mg.GET("/audit/my-publishes", d.auditMyPublishes)
		// 数据契约登记（1.5：契约 fields=判定字段清单；巡检/深对账已随投影退役下线）
		mg.GET("/sync/contracts", d.listDataContracts)
		// 程序化兜底
		mg.POST("/apps/:id/claim", d.ClaimApp)
		mg.POST("/owner-check", d.CheckOwnerResponsive)
		// 程序身份/agent 状态
		mg.GET("/clients", d.listClients)
	}

	// ---- 鉴权 API（PEP→PDP 共享密钥信任，防绕过网关直连）----
	az := r.Group("/v1/authz", pepMiddleware(d))
	{
		az.POST("/check", d.handleCheck)
		// T2 带体调用：创建 / 存量 body-id / fetch_source 的供材通道（业务持有请求体，材料随请求带到判定点）
		az.POST("/check-material", d.handleCheckMaterial)
	}

	// ---- 网关回调（Traefik forwardAuth → PEP→PDP，请求→action 映射）----
	// forwardAuth 默认以 GET 转发鉴权请求（preserveRequestMethod=false），故用 Any 注册
	gw := r.Group("/v1/gateway", pepMiddleware(d))
	{
		gw.Any("/check", d.handleGatewayCheck)
	}

	// ---- 程序身份（M2M）----
	r.POST("/v1/oauth/token", d.handleToken)

	// ---- 策略分发（agent 拉取）----
	r.GET("/v1/bundles/:app", d.handleBundle)
	r.POST("/v1/agents/status", d.handleAgentStatus)

	return r
}

func jwtMiddleware(d *Deps) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 统一网关已信任（X-Auth-* 身份头由 forwardAuth 注入）→ 跳过本地 JWT 校验
		if _, ok := c.Get("gateway_trusted"); ok {
			c.Next()
			return
		}
		h := c.GetHeader("Authorization")
		if len(h) < 7 || h[:7] != "Bearer " {
			c.AbortWithStatusJSON(401, gin.H{"error": "missing token"})
			return
		}
		claims, err := d.JWT.Parse(h[7:])
		if err != nil {
			c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
			return
		}
		c.Set("claims", claims)
		c.Next()
	}
}

func pepMiddleware(d *Deps) gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.GetHeader("X-PEP-Token") != d.Cfg.PEPSharedSecret {
			c.AbortWithStatusJSON(403, gin.H{"error": "forbidden: PEP token required"})
			return
		}
		c.Next()
	}
}
