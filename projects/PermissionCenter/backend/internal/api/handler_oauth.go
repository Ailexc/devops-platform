package api

import (
	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

// handleToken OAuth2 Client Credentials：client_id + secret → access token（JWT, sub=client:xxx）
func (d *Deps) handleToken(c *gin.Context) {
	var req struct {
		GrantType    string `json:"grant_type"`
		ClientID     string `json:"client_id"`
		ClientSecret string `json:"client_secret"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	if req.GrantType != "client_credentials" {
		c.JSON(400, gin.H{"error": "unsupported grant_type"})
		return
	}
	cli, err := d.Apps.ClientByID(req.ClientID)
	if err != nil {
		c.JSON(401, gin.H{"error": "invalid client"})
		return
	}
	if cli.Status != model.StatusEnabled {
		c.JSON(403, gin.H{"error": "client disabled"})
		return
	}
	if !auth.CheckPassword(cli.ClientSecretHash, req.ClientSecret) {
		c.JSON(401, gin.H{"error": "invalid client_secret"})
		return
	}
	app, err := d.Apps.ByID(cli.AppID)
	if err != nil {
		c.JSON(500, gin.H{"error": "app not found"})
		return
	}
	token, err := d.JWT.Sign(&auth.Claims{
		SubjectType: model.SubjectService,
		SubjectKey:  "s:" + cli.ClientID,
		Username:    cli.ClientID,
		TokenType:   "access",
		AppID:       app.ID,
		Scope:       "app:" + app.Code,
	})
	if err != nil {
		c.JSON(500, gin.H{"error": "sign failed"})
		return
	}

	c.JSON(200, gin.H{
		"access_token": token,
		"token_type":   "Bearer",
		"expires_in":   int(d.JWT.AccessTTL().Seconds()),
		"scope":        "app:" + app.Code,
	})
}
