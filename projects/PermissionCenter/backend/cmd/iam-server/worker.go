package main

import (
	"context"
	"log"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/xcy/permission-center/internal/api"
)

// consumeCMDBEvents 消费 CMDB 变更事件 → 增量更新本地资源索引（解耦数据源）
// 降级演示：CMDB 宕机时 IAM 仍用最后同步索引鉴权
func consumeCMDBEvents(ctx context.Context, deps *api.Deps) {
	rdb := deps.Cache.Client()
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}
		msgs, err := rdb.XRead(ctx, &redis.XReadArgs{
			Streams: []string{"cmdb-events", "$"},
			Count:   10,
			Block:   2 * time.Second,
		}).Result()
		if err != nil {
			if err == redis.Nil {
				continue
			}
			time.Sleep(time.Second)
			continue
		}
		for _, m := range msgs {
			for _, msg := range m.Messages {
				ev := map[string]any{}
				for k, v := range msg.Values {
					ev[k] = v
				}
				if err := deps.CMDBConnector.HandleEvent(ctx, ev); err != nil {
					log.Printf("[worker] cmdb event failed: %v", err)
					continue
				}
				// A5a 实例删除级联清理：PG 投影行（HandleEvent 内）+ OpenFGA 关系元组（此处）——
				// 已删实例的关系授权必须同步失效，否则 check-instance 对已删资源仍放行 = 幽灵授权 = 判多红线
				if evType, _ := ev["type"].(string); evType == "delete" {
					modelCode, _ := ev["model"].(string)
					instID, _ := ev["instance_id"].(string)
					if modelCode != "" && instID != "" {
						if perr := deps.DataPlane.PurgeInstanceTuples(ctx, modelCode, instID); perr != nil {
							log.Printf("[worker] purge tuples %s/%s: %v", modelCode, instID, perr)
						}
					}
				}
			}
		}
	}
}
