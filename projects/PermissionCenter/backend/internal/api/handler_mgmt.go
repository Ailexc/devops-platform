package api

import (
	"bytes"
	"encoding/json"
	"io"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

// mgScope 管理面授权域检查（去中心化授权前提）
// 检查当前用户是否有权操作目标资源，无权则拒绝或进入审批
// 规则：
//   - admin → 全域管理
//   - 应用 owner → 仅管理自己应用的授权
//   - 组 admin → 仅管理自己组的成员
//   - 普通用户 → 仅管理自己的 profile
func (d *Deps) mgScope(c *gin.Context) {
	claims, ok := auth.ClaimsFrom(c)
	if !ok {
		c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
		return
	}
	actor, err := d.Users.ByUsername(claims.Username)
	if err != nil || actor.Status == 0 {
		c.AbortWithStatusJSON(401, gin.H{"error": "user not found or disabled"})
		return
	}

	// admin 全域放行
	if actor.Username == "admin" {
		c.Next()
		return
	}

	path := c.FullPath() // 路由模板如 /api/v1/groups/:id
	method := c.Request.Method

	switch {
	// --- 用户管理 ---
	case path == "/api/v1/users/me":
		c.Next() // 当前用户信息：任何登录用户可查看自己
		return

	case path == "/api/v1/users/:id":
		targetID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if method == "PATCH" && targetID == actor.ID {
			c.Next()
			return
		}
		// 其他用户操作需要 admin
		c.AbortWithStatusJSON(403, gin.H{"error": "can only manage own profile"})
		return

	case path == "/api/v1/users" && method == "GET":
		// 用户列表：任何登录用户可查看（只读）
		c.Next()
		return

	// --- 我的视图（以我为中心，任何登录用户）---
	case strings.HasPrefix(path, "/api/v1/me/"):
		c.Next()
		return

	// --- 组管理 ---
	case path == "/api/v1/groups" && method == "GET":
		c.Next() // 组列表：任何登录用户可查看（只读）
		return

	case path == "/api/v1/groups" && method == "POST":
		c.Next() // 创建组：任何登录用户可创建
		return

	case path == "/api/v1/groups/:id":
		// 更新/删除组：组 admin
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isGroupAdmin(actor.ID, groupID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not admin of this group"})
		return

	case path == "/api/v1/groups/:id/members" && method == "POST":
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isGroupAdmin(actor.ID, groupID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not admin of this group"})
		return

	case path == "/api/v1/groups/:id/members/:uid":
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isGroupAdmin(actor.ID, groupID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not admin of this group"})
		return

	case path == "/api/v1/groups/:id/permissions" && method == "GET":
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isGroupAdmin(actor.ID, groupID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not admin of this group"})
		return

	case path == "/api/v1/groups/:id/capability-permissions" && method == "GET":
		// 组能力包权限：组成员可查看（只读）
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isGroupMember(actor.ID, groupID) || d.isGroupAdmin(actor.ID, groupID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not a member of this group"})
		return

	case path == "/api/v1/groups/:id/permissions" && method == "POST":
		// 组织权限收紧（§2.2）：仅末级（叶子）org / custom 组可配置
		groupID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		g, err := d.Groups.ByID(groupID)
		if err != nil {
			c.AbortWithStatusJSON(404, gin.H{"error": "group not found"})
			return
		}
		if g.Type == model.GroupTypeOrg && !d.isLeafOrg(groupID) {
			c.AbortWithStatusJSON(403, gin.H{"error": "only leaf org can configure permissions"})
			return
		}
		if !d.isGroupAdmin(actor.ID, groupID) {
			c.AbortWithStatusJSON(403, gin.H{"error": "not admin of this group"})
			return
		}
		c.Next()
		return

	// --- 应用管理（管理面：owner 私有；admin 全域）---
	case path == "/api/v1/apps" && method == "GET":
		c.Next() // 应用列表：handler 内按 owner 过滤（admin 返回全量）
		return

	case path == "/api/v1/apps" && method == "POST":
		c.Next() // 注册应用：任何登录用户可注册
		return

	// 应用详情 / 权限点 / 能力 / 模板 / 双向账本（只读视图）：仅 owner/admin
	// （管理信息含网络/鉴权/权限点/接入记录，非 owner 不得查看）
	case path == "/api/v1/apps/:id/actions",
		path == "/api/v1/apps/:id",
		path == "/api/v1/apps/:id/capabilities" && method == "GET",
		path == "/api/v1/apps/:id/templates" && method == "GET",
		path == "/api/v1/apps/:id/accessors",
		path == "/api/v1/apps/:id/accessors/:sid/grants",
		path == "/api/v1/apps/:id/upstreams":
		appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if actor.Username == "admin" || d.isAppOwner(actor.ID, appID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this application"})
		return

	// 能力声明写操作：仅 owner
	case path == "/api/v1/apps/:id/capabilities" ||
		path == "/api/v1/apps/:id/capabilities/:cid" ||
		path == "/api/v1/apps/:id/capabilities/:cid/publish" ||
		path == "/api/v1/apps/:id/capabilities/:cid/authz" ||
		path == "/api/v1/apps/:id/sync-capabilities" ||
		path == "/api/v1/apps/:id/validate":
		appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isAppOwner(actor.ID, appID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this application"})
		return

	// 策略模板写操作：仅 owner
	case path == "/api/v1/apps/:id/templates" ||
		path == "/api/v1/apps/:id/templates/:tid" ||
		path == "/api/v1/apps/:id/templates/:tid/publish":
		appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isAppOwner(actor.ID, appID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this application"})
		return

	// 权限市场 + 范围选项（预设×模型）：任何登录用户
	case strings.HasPrefix(path, "/api/v1/marketplace/") ||
		strings.HasPrefix(path, "/api/v1/capabilities/:cid/presets/"):
		if method == "POST" {
			// 范围选项写操作（保存/校验）：仅能力所属应用 owner
			cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
			cap, err := d.Caps.ByID(cid)
			if err != nil {
				c.AbortWithStatusJSON(404, gin.H{"error": "capability not found"})
				return
			}
			if !d.isAppOwner(actor.ID, cap.AppID) {
				c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this application"})
				return
			}
		}
		c.Next()
		return

	// 授权回收 / 回收审批：仅 owner（handler 内再校验 SoD）
	case path == "/api/v1/grants/:id/revoke":
		c.Next()
		return
	case path == "/api/v1/revoke-requests" || path == "/api/v1/revoke-requests/:id/approve":
		c.Next()
		return

	case path == "/api/v1/apps/:id/sync" || path == "/api/v1/apps/:id/owners" ||
		path == "/api/v1/apps/:id/clients" || path == "/api/v1/apps/:id/clients/:cid/rotate":
		appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		if d.isAppOwner(actor.ID, appID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this application"})
		return

	case path == "/api/v1/apps/:id/claim":
		c.Next() // 认领应用：任何登录用户可尝试认领
		return

	// --- 策略管理：admin 或应用 owner（去中心化授权下，策略变更需审批）---
	case path == "/api/v1/policies" && method == "POST":
		// 创建策略：admin 或应用 owner
		// 注意：中间件中读 body 必须保存并恢复，否则 handler 无法再次读取
		bodyBytes, err := io.ReadAll(c.Request.Body)
		if err != nil {
			c.AbortWithStatusJSON(400, gin.H{"error": "failed to read body"})
			return
		}
		c.Request.Body = io.NopCloser(bytes.NewReader(bodyBytes)) // 恢复 body 供 handler 使用
		var bodyReq struct {
			AppID uint64 `json:"app_id"`
		}
		if json.Unmarshal(bodyBytes, &bodyReq) == nil && bodyReq.AppID > 0 {
			if d.isAppOwner(actor.ID, bodyReq.AppID) {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of target application"})
		return

	case path == "/api/v1/policies/:id/publish":
		id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
		p, err := d.Pol.ByID(id)
		if err != nil {
			c.AbortWithStatusJSON(404, gin.H{"error": "policy not found"})
			return
		}
		if d.isAppOwner(actor.ID, p.AppID) {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{"error": "not owner of this policy's application"})
		return

	// --- 同步 ---
	case path == "/api/v1/sync/cmdb":
		c.Next() // CMDB 同步：任何登录用户可触发
		return

	case path == "/api/v1/sync/identity":
		c.Next() // 身份源同步：任何登录用户可触发
		return

	// --- 申请/审批 ---
	case path == "/api/v1/requests" && method == "POST":
		c.Next() // 提交申请：任何登录用户可提交
		return

	case path == "/api/v1/requests/preview":
		c.Next() // 申请单预览（能力包向导 Step 5，不落库）：任何登录用户
		return

	case path == "/api/v1/requests" && method == "GET":
		c.Next() // 查看申请：任何登录用户可查看自己的申请
		return

	case path == "/api/v1/requests/:id":
		c.Next() // 申请单详情（Phase 6）：handler 内校验归属
		return

	case path == "/api/v1/tickets":
		c.Next() // 审批中心统一工单视图：任何登录用户
		return

	case path == "/api/v1/requests/:id/approve":
		c.Next() // 审批：任何登录用户可尝试审批（SoD 在 handler 中校验）
		return

	// --- 程序化兜底 ---
	case path == "/api/v1/owner-check":
		c.Next() // 巡检：任何登录用户可触发
		return

	case path == "/api/v1/clients" && method == "GET":
		c.Next() // 程序身份列表：任何登录用户可查看
		return

	// --- 资源索引 ---
	case path == "/api/v1/resource-models" || path == "/api/v1/resource-models/:id/instances":
		c.Next() // 资源索引：任何登录用户可查看
		return

	// --- 审计/决策日志 + 我的三视图：任何登录用户只读 ---
	case path == "/api/v1/audit-logs" || path == "/api/v1/decision-logs" ||
		path == "/api/v1/audit/my-requests" || path == "/api/v1/audit/my-approvals" ||
		path == "/api/v1/audit/my-publishes":
		c.Next()
		return

	// --- 系统观测：任何登录用户只读（鉴权链路/PEP解析/PIP身份/Agent/分发/同步/缓存/指标/图谱/owner）---
	case path == "/api/v1/debug/resolve" || path == "/api/v1/debug/pip/:user" ||
		path == "/api/v1/debug/cache" || path == "/api/v1/debug/cache/clear" ||
		path == "/api/v1/debug/metrics" || path == "/api/v1/debug/ofga" ||
		path == "/api/v1/debug/owners" ||
		path == "/api/v1/agents" || path == "/api/v1/apps/:id/bundles" ||
		path == "/api/v1/sync-jobs":
		c.Next()
		return

	// --- 系统知识库：任何登录用户只读（复盘文档）---
	case strings.HasPrefix(path, "/api/v1/knowledge/docs"):
		c.Next()
		return
	}

	// 默认拒绝（deny-by-default）：未明确授权的管理操作一律拦截
	c.AbortWithStatusJSON(403, gin.H{"error": "not authorized for this management operation"})
}

// isAppOwner 检查用户是否为应用 owner
func (d *Deps) isAppOwner(userID, appID uint64) bool {
	app, err := d.Apps.ByID(appID)
	if err != nil {
		return false
	}
	if app.OwnerID == userID {
		return true
	}
	// 检查 app_owners 表
	var count int64
	d.DB.Model(&struct{}{}).Table("app_owners").
		Where("app_id = ? AND user_id = ?", appID, userID).
		Count(&count)
	return count > 0
}

// isGroupAdmin 检查用户是否为组管理员
func (d *Deps) isGroupAdmin(userID, groupID uint64) bool {
	var ug struct{ Role int16 }
	if err := d.DB.Table("user_groups").
		Where("user_id = ? AND group_id = ?", userID, groupID).
		Select("role").Scan(&ug).Error; err != nil {
		return false
	}
	return ug.Role == 2 // admin
}

func (d *Deps) isGroupMember(userID, groupID uint64) bool {
	var count int64
	d.DB.Table("user_groups").
		Where("user_id = ? AND group_id = ?", userID, groupID).
		Count(&count)
	return count > 0
}
