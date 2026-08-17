package api

import (
	"strconv"

	"github.com/gin-gonic/gin"
)

func (d *Deps) listResourceModels(c *gin.Context) {
	ms, err := d.Res.Models()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": ms})
}

func (d *Deps) listResourceInstances(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	is, total, err := d.Res.Instances(id, offset, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"items": is, "total": total})
}

func (d *Deps) syncCMDB(c *gin.Context) {
	// 资源归属应用：demo 中资源模型由 cmdb 提供（"我接入了谁"按此展示对方数据模型）
	if a, err := d.Apps.ByCode("cmdb"); err == nil {
		d.CMDBConnector.SetAppID(a.ID)
	}
	if err := d.CMDBConnector.SyncModels(c.Request.Context()); err != nil {
		c.JSON(502, gin.H{"error": err.Error()})
		return
	}
	if err := d.CMDBConnector.SyncInstances(c.Request.Context()); err != nil {
		c.JSON(502, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}

func (d *Deps) syncIdentity(c *gin.Context) {
	if err := d.IdentityConn.Sync(c.Request.Context()); err != nil {
		c.JSON(502, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}
