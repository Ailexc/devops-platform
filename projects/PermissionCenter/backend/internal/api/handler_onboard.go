package api

import (
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/onboard"
)

// v1.5 T4 接入体检（§3.9）：注册/导入/发版重新导入时自动跑，报告回执 API + 前端展示。
// 五类硬校验引擎在 internal/onboard（纯函数）；本文件管数据加载与触发点。

// buildOnboardReport 组装体检报告：active 动作 + 待确认队列 + 契约（pick/schema 校验）+ 客户端凭证（裸豁免校验）
func (d *Deps) buildOnboardReport(appID uint64) (onboard.Report, error) {
	app, err := d.Apps.ByID(appID)
	if err != nil {
		return onboard.Report{}, err
	}
	acts, err := d.Access.AllActions(appID)
	if err != nil {
		return onboard.Report{}, err
	}
	pend, _ := d.Access.Pendings(appID, "")
	contracts, _ := d.Contracts.ByApp(appID)
	clis, _ := d.Apps.Clients(appID)
	cliMap := make(map[string]model.Client, len(clis))
	for _, c := range clis {
		cliMap[c.ClientID] = c
	}
	return onboard.Run(app, acts, pend, contracts, cliMap), nil
}

// onboardReport GET /apps/:id/onboard-report 体检报告回执（前端体检报告页数据源）
func (d *Deps) onboardReport(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	rep, err := d.buildOnboardReport(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	c.JSON(200, rep)
}

// setExemptPaths PUT /apps/:id/exempt-paths 凭证豁免配置（§3.1：豁免主语=中心 M2M 凭证不是路由）。
// 配置期即拦裸豁免：每条豁免必须绑 M2M 凭证且该凭证存在并启用——配置页不让存，体检兜存量。
func (d *Deps) setExemptPaths(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	var body struct {
		Paths map[string]string `json:"paths"` // path → client_id
	}
	if err := c.ShouldBindJSON(&body); err != nil || body.Paths == nil {
		c.JSON(400, gin.H{"error": "paths required（map[path]client_id）"})
		return
	}
	for path, clientID := range body.Paths {
		if !strings.HasPrefix(path, "/") {
			c.JSON(400, gin.H{"error": "裸豁免被拒：路径须以 / 开头：" + path})
			return
		}
		if clientID == "" {
			c.JSON(400, gin.H{"error": "裸豁免被拒：豁免必须绑定中心 M2M 凭证（只配路径不绑凭证=自锁或裸奔）：" + path})
			return
		}
		cli, cerr := d.Apps.ClientByID(clientID)
		if cerr != nil || cli.AppID != app.ID || cli.Status != model.StatusEnabled {
			c.JSON(400, gin.H{"error": "裸豁免被拒：M2M 凭证不存在/不属于本应用/已禁用：" + clientID})
			return
		}
	}
	m := model.JSONMap{}
	for path, clientID := range body.Paths {
		m[path] = clientID
	}
	if err := d.Apps.SetExemptPaths(appID, m); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "app.exempt_paths.update", "app", strconv.FormatUint(appID, 10), gin.H{"paths": body.Paths})
	c.JSON(200, gin.H{"exempt_paths": m})
}
