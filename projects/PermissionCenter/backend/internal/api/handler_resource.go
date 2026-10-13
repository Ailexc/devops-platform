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

// listResourceInstances 资源实例列表——**申请选择器/授权表单的数据源（清单 A7 口径固化）**：
// 直查本地投影表（ResourceRepo），不调发布方接口——三理由：鸡生蛋（申请人对目标资源零权限）、
// 解耦（申请/审批不依赖发布方在线）、最小暴露（选择器只需判断字段）。
// 代价=分钟级新鲜度窗口（新资源投影未同步到时选择器选不到）：演示前先触发同步；生产演进方向=手动输入 external_id + 审批时后台校验。
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

// （1.5 T3）syncCMDB 运行期同步已下线——资源目录=seed 时快照（CMDBConnector 仅供 seed 期目录取数）
func (d *Deps) syncIdentity(c *gin.Context) {
	if err := d.IdentityConn.Sync(c.Request.Context()); err != nil {
		c.JSON(502, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}
