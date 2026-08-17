package api

import (
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

// demoPerson demo 登录人员（公开）：用户名 + 组织路径，登录页下拉选择
type demoPerson struct {
	Username    string `json:"username"`
	DisplayName string `json:"display_name"`
	OrgPath     string `json:"org_path"` // 总公司 → 研发中心 → 研发一部
	IsAdmin     bool   `json:"is_admin"`
	IsLeader    bool   `json:"is_leader"` // 组长
}

// handlePeople demo 登录人员列表（公开，仅演示环境）
func (d *Deps) handlePeople(c *gin.Context) {
	var us []model.User
	d.DB.Where("status = ?", model.StatusEnabled).Order("id").Find(&us)
	out := make([]demoPerson, 0, len(us))
	for _, u := range us {
		p := demoPerson{Username: u.Username, DisplayName: u.DisplayName, IsAdmin: u.Username == "admin"}
		groups, _ := d.Groups.ByUserID(u.ID)
		for _, g := range groups {
			if g.Type == model.GroupTypeOrg {
				p.OrgPath = strings.Join(d.orgPathNames(g), " → ")
				var ug model.UserGroup
				if err := d.DB.Where("user_id = ? AND group_id = ?", u.ID, g.ID).First(&ug).Error; err == nil && ug.Role == model.GroupRoleAdmin {
					p.IsLeader = true
				}
				break
			}
		}
		out = append(out, p)
	}
	c.JSON(200, gin.H{"items": out})
}

// handleDemoLogin demo 一键登录（仅演示环境）：选择人员直接签发令牌，免密码
func (d *Deps) handleDemoLogin(c *gin.Context) {
	var req struct {
		Username string `json:"username"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.Username == "" {
		c.JSON(400, gin.H{"error": "username required"})
		return
	}
	u, err := d.Users.ByUsername(req.Username)
	if err != nil || u.Status != model.StatusEnabled {
		c.JSON(401, gin.H{"error": "user not found or disabled"})
		return
	}
	access, err := d.JWT.Sign(&auth.Claims{
		SubjectType: model.SubjectUser,
		SubjectKey:  "u:" + u.Username,
		Username:    u.Username,
		TokenVer:    u.TokenVersion,
		TokenType:   "access",
	})
	if err != nil {
		c.JSON(500, gin.H{"error": "sign failed"})
		return
	}
	c.JSON(200, gin.H{"access_token": access, "expires_in": int(d.JWT.AccessTTL().Seconds()), "user": u})
}

type loginReq struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// handleLogin 登录：校验密码 + token_version，签发 access+refresh
func (d *Deps) handleLogin(c *gin.Context) {
	var req loginReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	u, err := d.Users.ByUsername(req.Username)
	if err != nil {
		c.JSON(401, gin.H{"error": "invalid credentials"})
		return
	}
	if u.Status != model.StatusEnabled {
		c.JSON(403, gin.H{"error": "user disabled"})
		return
	}
	if !auth.CheckPassword(u.PasswordHash, req.Password) {
		c.JSON(401, gin.H{"error": "invalid credentials"})
		return
	}
	access, err := d.JWT.Sign(&auth.Claims{
		SubjectType: model.SubjectUser,
		SubjectKey:  "u:" + u.Username,
		Username:    u.Username,
		TokenVer:    u.TokenVersion,
		TokenType:   "access",
	})
	if err != nil {
		c.JSON(500, gin.H{"error": "sign failed"})
		return
	}
	refresh, err := d.JWT.SignWithTTL(&auth.Claims{
		SubjectType: model.SubjectUser,
		SubjectKey:  "u:" + u.Username,
		Username:    u.Username,
		TokenVer:    u.TokenVersion,
		TokenType:   "refresh",
	}, d.JWT.RefreshTTL())
	if err != nil {
		c.JSON(500, gin.H{"error": "sign failed"})
		return
	}
	c.JSON(200, gin.H{
		"access_token":  access,
		"refresh_token": refresh,
		"expires_in":    int(d.JWT.AccessTTL().Seconds()),
		"user":          u,
	})
}

// handleRefresh 刷新令牌
func (d *Deps) handleRefresh(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	claims, err := d.JWT.Parse(req.RefreshToken)
	if err != nil || claims.TokenType != "refresh" {
		c.JSON(401, gin.H{"error": "invalid refresh token"})
		return
	}
	u, err := d.Users.ByUsername(claims.Username)
	if err != nil {
		c.JSON(401, gin.H{"error": "user not found"})
		return
	}
	if claims.TokenVer != u.TokenVersion {
		c.JSON(401, gin.H{"error": "token revoked"})
		return
	}
	access, err := d.JWT.Sign(&auth.Claims{
		SubjectType: model.SubjectUser,
		SubjectKey:  "u:" + u.Username,
		Username:    u.Username,
		TokenVer:    u.TokenVersion,
		TokenType:   "access",
	})
	if err != nil {
		c.JSON(500, gin.H{"error": "sign failed"})
		return
	}
	c.JSON(200, gin.H{"access_token": access, "expires_in": int(d.JWT.AccessTTL().Seconds())})
}
