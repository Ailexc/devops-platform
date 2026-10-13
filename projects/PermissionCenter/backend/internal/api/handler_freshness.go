package api

import (
	"github.com/gin-gonic/gin"
)

// listDataContracts 数据契约登记表（1.5 保留）：
// 契约 fields = 判定字段清单（点查白名单/包门禁取材用，方案 §3.1）；
// 确认制时钟/巡检/新鲜度状态机已随投影退役（1.5 T3）——本接口仅返回登记面字段，不暴露时钟态。
func (d *Deps) listDataContracts(c *gin.Context) {
	items, err := d.Contracts.ListEnabled()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	out := make([]gin.H, 0, len(items))
	for _, dc := range items {
		out = append(out, gin.H{
			"model":               dc.ModelCode,
			"fields":              dc.Fields,
			"algorithm":           dc.Algorithm,
			"staleness_sla_sec":   dc.StalenessSlaSec,
			"degrade_max_age_sec": dc.DegradeMaxAgeSec,
			"enabled":             dc.Enabled,
		})
	}
	c.JSON(200, gin.H{"items": out})
}
