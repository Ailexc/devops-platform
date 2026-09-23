package main

import (
	"context"
	"fmt"
	"log"
	"runtime/debug"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/xcy/permission-center/internal/api"
)

// claimLimit S3 认领次数上限：毒消息防死循环（超限投 DLQ，清单 R3）
const claimLimit = 5

// consumeCMDBEvents 消费 CMDB 变更事件 → 增量更新本地资源索引（解耦数据源）
// S3 消费组版（多 Worker 分摊）：XREADGROUP 同一事件仅一个 consumer 处理；
// 降级演示：CMDB 宕机时 IAM 仍用最后同步索引鉴权
func consumeCMDBEvents(ctx context.Context, deps *api.Deps) {
	rdb := deps.Cache.Client()
	stream, group := "cmdb-events", "iam-sync-workers"
	consumer := ownerID()
	minIdle := deps.Cfg.WorkerClaimMinIdle

	ensureGroup := func() {
		// S3① 建组起点 $——与原 XRead "$" 等价（只消费新事件）+ 组建立后宕机期间事件留在 PEL 不丢；
		// 防历史事件重放把 reset 后种子投影又删掉（对抗审查 M-2）；BUSYGROUP 幂等吞掉
		if err := rdb.XGroupCreateMkStream(ctx, stream, group, "$").Err(); err != nil &&
			!strings.Contains(err.Error(), "BUSYGROUP") && ctx.Err() == nil {
			log.Printf("[worker] xgroup create: %v", err)
		}
	}
	ensureGroup()

	for {
		if ctx.Err() != nil {
			return
		}
		// S3③ 每轮 XRead 返回后顺带认领僵死副本 pending（min-idle 可配）
		autoclaimPending(ctx, deps, stream, group, consumer, minIdle)

		msgs, err := rdb.XReadGroup(ctx, &redis.XReadGroupArgs{
			Group:    group,
			Consumer: consumer,
			Streams:  []string{stream, ">"},
			Count:    10,
			Block:    2 * time.Second,
		}).Result()
		if err != nil {
			if err == redis.Nil {
				continue
			}
			if strings.Contains(err.Error(), "NOGROUP") {
				ensureGroup()
				continue
			}
			if ctx.Err() != nil {
				return
			}
			log.Printf("[worker] xreadgroup: %v", err)
			// L-1：select 而非裸 Sleep——shutdown 退出延迟 ≈0
			select {
			case <-ctx.Done():
				return
			case <-time.After(time.Second):
			}
			continue
		}
		for _, m := range msgs {
			for _, msg := range m.Messages {
				// S3② 仅处理成功才 XACK；失败留 PEL 等 XAUTOCLAIM 重投（次数上限→DLQ）
				if processCMDBMessage(ctx, deps, msg) {
					if err := rdb.XAck(ctx, stream, group, msg.ID).Err(); err != nil {
						log.Printf("[worker] ack %s: %v", msg.ID, err)
					}
				}
			}
		}
	}
}

// processCMDBMessage 单条事件处理——返回是否可 ACK；S1 单条 recover：毒消息 panic 不杀消费循环
// （panic 不 ACK → 留 PEL → 认领次数上限兜底 DLQ）
func processCMDBMessage(ctx context.Context, deps *api.Deps, msg redis.XMessage) (acked bool) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[panic-recover] worker msg %s: %v\n%s", msg.ID, r, debug.Stack())
			acked = false
		}
	}()
	ev := map[string]any{}
	for k, v := range msg.Values {
		ev[k] = v
	}
	if err := deps.CMDBConnector.HandleEvent(ctx, ev); err != nil {
		log.Printf("[worker] cmdb event failed: %v（不 ACK——留 PEL 重投）", err)
		return false
	}
	// A5a 实例删除级联清理：PG 投影行（HandleEvent 内）+ OpenFGA 关系元组（此处）——
	// 已删实例的关系授权必须同步失效，否则 check-instance 对已删资源仍放行 = 幽灵授权 = 判多红线
	if evType, _ := ev["type"].(string); evType == "delete" {
		modelCode, _ := ev["model"].(string)
		instID, _ := ev["instance_id"].(string)
		if modelCode != "" && instID != "" {
			if perr := deps.DataPlane.PurgeInstanceTuples(ctx, modelCode, instID); perr != nil {
				log.Printf("[worker] purge tuples %s/%s: %v（不 ACK——留 PEL 重投）", modelCode, instID, perr)
				return false
			}
		}
	}
	return true
}

// autoclaimPending S3③：认领僵死副本的 pending 消息——认领计数存 Hash（清单 L-4 选型），
// 超上限投 cmdb-events:dlq + 告警 + ACK 原消息（R3：DLQ 投递时同时 ACK，防死循环）
func autoclaimPending(ctx context.Context, deps *api.Deps, stream, group, consumer string, minIdle time.Duration) {
	rdb := deps.Cache.Client()
	// go-redis v9.21 签名：Result() (messages []XMessage, start string, err error)
	claimed, _, err := rdb.XAutoClaim(ctx, &redis.XAutoClaimArgs{
		Group: group, Consumer: consumer, MinIdle: minIdle, Start: "0-0", Count: 50,
	}).Result()
	if err != nil && err != redis.Nil {
		if ctx.Err() == nil {
			log.Printf("[worker] xautoclaim: %v", err)
		}
		return
	}
	if len(claimed) == 0 {
		return
	}
	attemptsKey := stream + ":attempts"
	for _, msg := range claimed {
		n, herr := rdb.HIncrBy(ctx, attemptsKey, msg.ID, 1).Result()
		if herr == nil && n > claimLimit {
			rdb.XAdd(ctx, &redis.XAddArgs{Stream: stream + ":dlq", Values: map[string]any{
				"orig_id": msg.ID, "attempts": n, "values": fmt.Sprintf("%v", msg.Values),
			}})
			rdb.XAck(ctx, stream, group, msg.ID)
			rdb.HDel(ctx, attemptsKey, msg.ID)
			log.Printf("[worker] DLQ: %s attempts=%d 超上限 %d——已投 %s:dlq 并 ACK（告警人工介入）", msg.ID, n, claimLimit, stream)
			continue
		}
		if processCMDBMessage(ctx, deps, msg) {
			rdb.XAck(ctx, stream, group, msg.ID)
			rdb.HDel(ctx, attemptsKey, msg.ID)
		}
	}
}
