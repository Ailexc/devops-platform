package auth

import (
	"strings"

	"github.com/gin-gonic/gin"
)

// 管理面角色（内置）
const (
	RoleUser         = "user"          // 普通用户：自助申请、查看自己
	RoleAppOwner     = "app-owner"     // 应用 owner：管理自家应用
	RoleAuditAdmin   = "audit-admin"   // 审计管理员：全局只读
)

// AdminRoleSet 管理面角色（内置用户挂这些角色）
var AdminRoleSet = []string{RoleUser, RoleAppOwner, RoleAuditAdmin}

// Middleware 管理 API 认证：解析 Bearer token，注入 claims 到 context
func Middleware(m *Manager) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 网关 forwardAuth 已校验统一 JWT 并注入身份（见 GatewayTrust）：
		// 身份已由网关统一认证，本地无需再解析 Bearer，直接放行本地授权
		if c.GetBool("gateway_trusted") {
			c.Next()
			return
		}
		h := c.GetHeader("Authorization")
		if !strings.HasPrefix(h, "Bearer ") {
			c.AbortWithStatusJSON(401, gin.H{"error": "missing token"})
			return
		}
		claims, err := m.Parse(strings.TrimPrefix(h, "Bearer "))
		if err != nil {
			c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
			return
		}
		c.Set("claims", claims)
		c.Next()
	}
}

// PEPAuth PEP→PDP 信任：校验共享密钥（防绕过网关直连 PDP）
func PEPAuth(secret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		h := c.GetHeader("X-PEP-Token")
		if h != secret {
			c.AbortWithStatusJSON(403, gin.H{"error": "forbidden: PEP token required"})
			return
		}
		c.Next()
	}
}

func ClaimsFrom(c *gin.Context) (*Claims, bool) {
	v, ok := c.Get("claims")
	if !ok {
		return nil, false
	}
	cc, ok := v.(*Claims)
	return cc, ok
}
