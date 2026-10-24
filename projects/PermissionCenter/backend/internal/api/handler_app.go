package api

import (
	"crypto/rand"
	"encoding/hex"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
)

type registerAppReq struct {
	Code         string           `json:"code"`
	Name         string           `json:"name"`
	Type         int16            `json:"type"`
	OpenAPIURL   string           `json:"openapi_url"`
	Description  string           `json:"description"`
	Language     string           `json:"language"`
	DocURL       string           `json:"doc_url"`        // 产品文档/操作手册链接（人可读，纯展示）
	OwnerGroupID *uint64          `json:"owner_group_id"` // 所属组（组织兜底锚点）
	OwnerIDs     []uint64         `json:"owner_ids"`      // 额外负责人（注册者自动成为 owner，需再指定 ≥1 人）
	NetInfo      map[string]any   `json:"net_info"`       // v12：网络信息（云/账号/区域/VPC/子网/安全组/容器/健康检查）
	Auth         []map[string]any `json:"auth"`           // v12：鉴权方式列表
}

// registerApp 应用注册（demo 简化自审批；真实场景走工单+网络打通）
// 注册者成为 owner，并绑定 ≥2 负责人（程序化兜底前提）
func (d *Deps) registerApp(c *gin.Context) {
	var req registerAppReq
	if err := c.ShouldBindJSON(&req); err != nil || req.Code == "" || req.Name == "" {
		c.JSON(400, gin.H{"error": "code/name required"})
		return
	}
	registrarID := d.currentUserID(c)

	// 去重：注册者自动成为 owner，额外 owner 不能包含自己
	extraOwnerIDs := make([]uint64, 0, len(req.OwnerIDs))
	seen := map[uint64]bool{registrarID: true}
	for _, oid := range req.OwnerIDs {
		if oid > 0 && !seen[oid] {
			extraOwnerIDs = append(extraOwnerIDs, oid)
			seen[oid] = true
		}
	}

	// 强制 ≥2 负责人：注册者 + 额外 ≥1 人
	if len(extraOwnerIDs) < 1 {
		c.JSON(400, gin.H{"error": "owner_ids required: app must have at least 2 owners (you + 1 more)"})
		return
	}

	appType := req.Type
	if appType == 0 {
		appType = model.AppTypeAPI
	}
	app := &model.App{
		Code:         req.Code,
		Name:         req.Name,
		Type:         appType,
		OpenAPIURL:   req.OpenAPIURL,
		Status:       model.StatusEnabled,
		OwnerID:      registrarID,
		Description:  req.Description,
		Language:     req.Language,
		DocURL:       req.DocURL,
		OwnerGroupID: req.OwnerGroupID,
		NetInfo:      model.JSONMap(req.NetInfo),
		Auth:         toJSONAny(req.Auth),
	}
	if err := d.Apps.Create(app); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// 注册者为 primary owner
	d.Apps.AddOwner(&model.AppOwner{AppID: app.ID, UserID: registrarID, IsPrimary: true})
	// 额外负责人
	for _, oid := range extraOwnerIDs {
		d.Apps.AddOwner(&model.AppOwner{AppID: app.ID, UserID: oid, IsPrimary: false})
	}

	d.audit(c, "app.register", "app", strconv.FormatUint(app.ID, 10),
		gin.H{"code": app.Code, "owners": append([]uint64{registrarID}, extraOwnerIDs...)})
	// T4：注册即体检（§3.9 触发点之一）——空路由表=ready，报告随回执返回
	rep, _ := d.buildOnboardReport(app.ID)
	c.JSON(201, gin.H{"app": app, "onboard": rep})
}

// appDetail 应用详情（v12：含网络信息 + 鉴权方式 + 负责人 + 程序身份）
func (d *Deps) appDetail(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	var owners []model.AppOwner
	d.DB.Where("app_id = ?", id).Find(&owners)
	var clients []model.Client
	d.DB.Where("app_id = ? AND status = ?", id, model.StatusEnabled).Find(&clients)
	// 负责人可读视图（用户名/姓名/主次）
	ownerViews := make([]gin.H, 0, len(owners))
	for _, o := range owners {
		un, dn := "", ""
		if u, err := d.Users.ByID(o.UserID); err == nil {
			un, dn = u.Username, u.DisplayName
		}
		ownerViews = append(ownerViews, gin.H{
			"user_id": o.UserID, "username": un, "display_name": dn,
			"is_primary": o.IsPrimary,
		})
	}
	// 所属组可读视图
	var ownerGroup *gin.H
	if app.OwnerGroupID != nil {
		if g, err := d.Groups.ByID(*app.OwnerGroupID); err == nil {
			ownerGroup = &gin.H{"id": g.ID, "name": g.Name, "path_names": d.orgPathNames(*g)}
		}
	}
	c.JSON(200, gin.H{
		"app":         app,
		"owners":      ownerViews,
		"owner_group": ownerGroup,
		"clients":     clients,
	})
}

func (d *Deps) listApps(c *gin.Context) {
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	// 管理面：仅返回当前用户 owner 的应用（含另一 owner）；admin 返回全量
	if claims, ok := auth.ClaimsFrom(c); ok {
		if u, err := d.Users.ByUsername(claims.Username); err == nil && u.Username == "admin" {
			as, total, err := d.Apps.List(offset, limit)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(200, gin.H{"items": as, "total": total})
			return
		}
	}
	uid := d.currentUserID(c)
	as, err := d.Apps.ByOwnerID(uid)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": as, "total": len(as)})
}

// marketplaceApps 应用市场公开目录：所有已启用应用（仅公开字段 + 能力数，不含管理信息）
func (d *Deps) marketplaceApps(c *gin.Context) {
	as, _, err := d.Apps.List(0, 200)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	items := make([]gin.H, 0, len(as))
	for _, a := range as {
		caps, _ := d.Caps.List(a.ID)
		items = append(items, gin.H{
			"id":          a.ID,
			"code":        a.Code,
			"name":        a.Name,
			"type":        a.Type,
			"description": a.Description,
			"doc_url":     a.DocURL,
			"cap_count":   len(caps),
		})
	}
	c.JSON(200, gin.H{"items": items})
}

// marketplaceAppDetail 应用市场公开详情：仅申请接入所需（基本信息 + 网络信息 + 鉴权方式）
// 不含权限点/数据模型/凭证/接入记录等管理信息
func (d *Deps) marketplaceAppDetail(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	caps, _ := d.Caps.List(app.ID)
	c.JSON(200, gin.H{
		"id":          app.ID,
		"code":        app.Code,
		"name":        app.Name,
		"type":        app.Type,
		"description": app.Description,
		"doc_url":     app.DocURL,
		"net_info":    app.NetInfo,
		"auth":        app.Auth,
		"cap_count":   len(caps),
	})
}

// syncApp 触发 OpenAPI 同步 → 生成权限点 + 板块模板
func (d *Deps) syncApp(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	if app.OpenAPIURL == "" {
		c.JSON(400, gin.H{"error": "openapi_url not configured"})
		return
	}
	res, err := d.OpenAPISyncer.Sync(c.Request.Context(), app)
	if err != nil {
		c.JSON(502, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "app.sync", "app", strconv.FormatUint(id, 10), res)
	c.JSON(200, res)
}

func (d *Deps) listActions(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	as, err := d.Access.Actions(id)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": as})
}

func (d *Deps) addOwner(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		UserID uint64 `json:"user_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.UserID == 0 {
		c.JSON(400, gin.H{"error": "user_id required"})
		return
	}
	if err := d.Apps.AddOwner(&model.AppOwner{AppID: appID, UserID: req.UserID, IsPrimary: false}); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "app.add_owner", "app", strconv.FormatUint(appID, 10), gin.H{"user_id": req.UserID})
	c.JSON(200, gin.H{"ok": true})
}

// createClient 创建程序身份（M2M）：返回明文 secret 一次
func (d *Deps) createClient(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	clientID := "client-" + strconv.FormatUint(appID, 10) + "-" + randHex(4)
	secret := randHex(16)
	hash, err := auth.HashPassword(secret)
	if err != nil {
		c.JSON(500, gin.H{"error": "hash failed"})
		return
	}
	cli := &model.Client{AppID: appID, ClientID: clientID, ClientSecretHash: hash, Status: model.StatusEnabled}
	if err := d.Apps.CreateClient(cli); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "app.create_client", "client", strconv.FormatUint(cli.ID, 10), gin.H{"client_id": clientID})
	c.JSON(201, gin.H{"client": cli, "client_secret": secret})
}

func (d *Deps) rotateClient(c *gin.Context) {
	clientID := c.Param("cid")
	cli, err := d.Apps.ClientByID(clientID)
	if err != nil {
		c.JSON(404, gin.H{"error": "client not found"})
		return
	}
	secret := randHex(16)
	hash, _ := auth.HashPassword(secret)
	cli.ClientSecretHash = hash
	d.Apps.UpdateClient(cli)
	d.audit(c, "app.rotate_client", "client", clientID, nil)
	c.JSON(200, gin.H{"client_secret": secret})
}

func (d *Deps) listClients(c *gin.Context) {
	cs, err := d.Apps.AllClients()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": cs})
}

func randHex(n int) string {
	b := make([]byte, n)
	rand.Read(b)
	return hex.EncodeToString(b)
}
