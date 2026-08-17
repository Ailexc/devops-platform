package api

import (
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

type createUserReq struct {
	Username    string         `json:"username"`
	DisplayName string         `json:"display_name"`
	Email       string         `json:"email"`
	Password    string         `json:"password"`
	Attributes  map[string]any `json:"attributes"`
}

// getCurrentUser 获取当前登录用户信息（含所属组、拥有的应用）
func (d *Deps) getCurrentUser(c *gin.Context) {
	claims, ok := auth.ClaimsFrom(c)
	if !ok {
		c.JSON(401, gin.H{"error": "invalid token"})
		return
	}
	u, err := d.Users.ByUsername(claims.Username)
	if err != nil {
		c.JSON(404, gin.H{"error": "user not found"})
		return
	}
	// 获取用户所属组
	groups, _ := d.Groups.ByUserID(u.ID)
	// 获取用户拥有的应用
	apps, _ := d.Apps.ByOwnerID(u.ID)
	c.JSON(200, gin.H{
		"user":   u,
		"groups": groups,
		"apps":   apps,
	})
}

func (d *Deps) createUser(c *gin.Context) {
	var req createUserReq
	if err := c.ShouldBindJSON(&req); err != nil || req.Username == "" {
		c.JSON(400, gin.H{"error": "username required"})
		return
	}
	hash, err := auth.HashPassword(req.Password)
	if err != nil {
		c.JSON(500, gin.H{"error": "hash failed"})
		return
	}
	u := &model.User{
		Username:     req.Username,
		DisplayName:  req.DisplayName,
		Email:        req.Email,
		PasswordHash: hash,
		Status:       model.StatusEnabled,
		Attributes:   req.Attributes,
		Source:       model.SourceLocal,
	}
	if err := d.Users.Create(u); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "user.create", "user", strconv.FormatUint(u.ID, 10), gin.H{"username": u.Username})
	c.JSON(201, u)
}

func (d *Deps) listUsers(c *gin.Context) {
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	us, total, err := d.Users.List(offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": us, "total": total})
}

func (d *Deps) updateUser(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		DisplayName *string         `json:"display_name"`
		Email       *string         `json:"email"`
		Status      *int16          `json:"status"`
		Password    *string         `json:"password"`
		Attributes  map[string]any  `json:"attributes"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	u, err := d.Users.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "user not found"})
		return
	}
	if req.DisplayName != nil {
		u.DisplayName = *req.DisplayName
	}
	if req.Email != nil {
		u.Email = *req.Email
	}
	if req.Status != nil {
		u.Status = *req.Status
		// 停用/改密 → token_version +1，旧 token 即时失效
		u.TokenVersion++
	}
	if req.Password != nil && *req.Password != "" {
		if hash, err := auth.HashPassword(*req.Password); err == nil {
			u.PasswordHash = hash
			u.TokenVersion++
		}
	}
	if req.Attributes != nil {
		u.Attributes = req.Attributes
	}
	if err := d.Users.Update(u); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	// 用户变更可能影响组策略快照 → 使缓存失效（全部 app 简单处理）
	d.bumpAllCaches(c)
	d.audit(c, "user.update", "user", strconv.FormatUint(u.ID, 10), gin.H{"status": u.Status})
	c.JSON(200, u)
}
