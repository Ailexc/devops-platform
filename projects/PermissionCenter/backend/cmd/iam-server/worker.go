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
				}
			}
		}
	}
}
