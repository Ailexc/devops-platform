// iam-sync：同步组件独立进程（1.5 T3 后仅存 TTL 回收——CMDB 事件 worker 与巡检/深对账已随
// 投影机制退役下线；策略 TTL 到期回收继续在此自治运行）。设计要点（清单 v1.1）：
//   - 逐轮 recover：panic 不杀进程、循环不静默死亡（外层）+ 单活锁 defer 释放（内层）
//   - signal.NotifyContext 优雅退出（原全仓无 signal、ctx 永不取消）
//   - 单活锁：ttl tick 抢锁执行（多副本仅一活）
//   - healthz 仅容器内网（S7：compose 禁发布宿主口——宿主 8090 已被 devops-gateway 占用、scale 前提）
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/xcy/permission-center/internal/api"
	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/store"
)

func main() {
	cfg := config.Load()

	db, err := store.Open(cfg.PGDSN)
	if err != nil {
		log.Fatalf("[iam-sync] db: %v", err)
	}
	cache, err := store.NewCache(cfg.RedisAddr)
	if err != nil {
		log.Fatalf("[iam-sync] redis: %v", err)
	}
	deps := api.NewDeps(cfg, db, cache)

	// S1：signal 接管 ctx——TERM/INT 优雅退出；锁内执行中断后 defer 仍释放锁
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	// （1.5 T3）OpenFGA 数据面已退役——本进程仅存 TTL 回收循环（投影同步管道已下线）
	loops := []struct {
		name string
		run  func(context.Context, *api.Deps)
	}{
		{"ttl", ttlSweepLoop},
	}
	var wg sync.WaitGroup
	for _, l := range loops {
		wg.Add(1)
		go func(name string, run func(context.Context, *api.Deps)) {
			defer wg.Done()
			run(ctx, deps)
		}(l.name, l.run)
	}

	// healthz：仅容器内网监听（S7）
	go runHealthz(cfg.SyncHealthAddr)

	log.Printf("[iam-sync] started（loops=ttl healthz=%s）", cfg.SyncHealthAddr)

	<-ctx.Done()
		log.Println("[iam-sync] ctx canceled——等待 TTL 循环退出（锁内执行等本轮返回）")
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
		log.Println("[iam-sync] graceful exit")
	case <-time.After(10 * time.Second):
		log.Println("[iam-sync] exit timeout——强制退出（未释放的锁等 TTL 过期由他副本接管，R1 设计内）")
	}
}

func runHealthz(addr string) {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Printf("[iam-sync] healthz %s: %v", addr, err)
	}
}
