package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"runtime/debug"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/xcy/permission-center/internal/api"
)

// 单活锁键（清单 S4 三把锁，覆盖四执行点：启动轮/patrol tick/recon tick/ttl tick）
const (
	lockPatrol    = "lock:iam:patrol"
	lockReconcile = "lock:iam:reconcile"
	lockTTL       = "lock:iam:ttl"
)

// releaseScript 仅-owner 释放（Lua 原子）：正常与 panic 路径都经 defer 走这里，不等 TTL 过期
var releaseScript = redis.NewScript(`if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) end return 0`)

func ownerID() string {
	hn, _ := os.Hostname()
	return fmt.Sprintf("%s:%d", hn, os.Getpid())
}

// runLocked S4 单活锁执行体——顺序硬约束（对抗审查 M-5）：
//
//	外层 defer recover（**逐轮**包裹：panic 后上层循环继续，进程活、循环也活）
//	  → 抢锁失败恒打 [lock-skip]（stdlib log 无级别机制）
//	  → 内层 defer 仅-owner 释放（锁获取后立即注册：panic 时不等 TTL；释放用独立 background ctx——TERM 落锁内时也能释放）
//
// 锁 TTL = 周期/2 必须 > 单轮耗时（R1）：单轮超 TTL 80% 打 warn；Redis 故障本轮跳过
// （巡检停摆 = 确认制时钟老化进入降级三档，属设计内 fail-safe）。
func runLocked(ctx context.Context, deps *api.Deps, key string, ttl time.Duration, tag string, fn func()) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[panic-recover] %s/%s: %v\n%s", key, tag, r, debug.Stack())
		}
	}()
	if ctx.Err() != nil {
		return
	}
	owner := ownerID()
	rdb := deps.Cache.Client()
	ok, err := rdb.SetNX(ctx, key, owner, ttl).Result()
	if err != nil {
		log.Printf("[lock] %s acquire error（本轮跳过）: %v", key, err)
		return
	}
	if !ok {
		log.Printf("[lock-skip] %s（另一副本执行中，tag=%s）", key, tag)
		return
	}
	defer func() {
		// 独立 ctx：shutdown（外层 ctx 已取消）时仍能释放锁
		relCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		if err := releaseScript.Run(relCtx, rdb, []string{key}, owner).Err(); err != nil {
			log.Printf("[lock] %s release: %v（等 TTL 过期由他副本接管）", key, err)
		}
	}()
	start := time.Now()
	fn()
	if elapsed := time.Since(start); ttl > 0 && elapsed > ttl*8/10 {
		log.Printf("[lock] warn: %s/%s 单轮耗时 %v 超锁 TTL(%v) 80%%——可能双副本接管双跑，幂等三道门+CAS 兜底（R1）", key, tag, elapsed, ttl)
	}
}
