package auth

import (
	"strings"

	"github.com/gin-gonic/gin"
)

// 统一网关信任接入（forwardAuth 模式）
//
// 真实场景：Traefik forwardAuth 校验统一 JWT 通过后，向本系统注入身份头
// X-Auth-Username / X-Auth-User / X-Auth-Name / X-Auth-Source。
// 本中间件信任该头，直接构造 claims 注入 context（身份已由网关统一认证）：
// - 身份统一（认证中心/网关）：用户是谁
// - 授权分散（本系统）：用户在本系统的角色/权限由本地数据自治
// 无网关头时不拦截，交回原 Bearer token 解析（本地 JWT 登录兜底）。
func GatewayTrust() gin.HandlerFunc {
	return func(c *gin.Context) {
		username := c.GetHeader("X-Auth-Username")
		if username == "" {
			c.Next() // 无网关头 → 交给原 jwtMiddleware 走 Bearer 解析
			return
		}
		// 账号作用域收口：iam_ 前缀账号剥前缀映射本地（iam_alice→alice），admin 为全局超管；
		// 其它系统账号（release_/workflow_/cloud_…）无权进入权限中心 → 明确拒绝
		if username != "admin" {
			if !strings.HasPrefix(username, "iam_") {
				c.AbortWithStatusJSON(403, gin.H{"error": "账号未在权限中心开通"})
				return
			}
			username = strings.TrimPrefix(username, "iam_")
		}
		c.Set("claims", &Claims{
			SubjectType: 1,        // 用户
			SubjectKey:  "u:" + username,
			Username:    username,
			TokenType:   "access", // 网关已验证
		})
		c.Set("gateway_trusted", true)
		c.Next()
	}
}
