// iam-server：中心 PDP + 管理 API + Sync（控制面+数据面主体服务）
package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/api"
	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/store"
)

func main() {
	// 子命令：go run ./cmd/iam-server seed [--reset]
	// --reset：先清空 demo 域数据再重建（一键重置初始化）
	if len(os.Args) > 1 && os.Args[1] == "seed" {
		reset := false
		for _, a := range os.Args[2:] {
			if a == "--reset" {
				reset = true
			}
		}
		if err := seed(reset); err != nil {
			log.Fatalf("[seed] %v", err)
		}
		return
	}

	cfg := config.Load()

	db, err := store.Open(cfg.PGDSN)
	if err != nil {
		log.Fatalf("[iam-server] db: %v", err)
	}
	cache, err := store.NewCache(cfg.RedisAddr)
	if err != nil {
		log.Fatalf("[iam-server] redis: %v", err)
	}

	deps := api.NewDeps(cfg, db, cache)

	// 初始化 OpenFGA：store + 授权模型（幂等）
	// 启动初期 OpenFGA 可能未就绪（容器编排时序），重试直至成功，避免 storeID 为空导致数据级鉴权失效
	ctx := context.Background()
	if err := ensureOpenFGA(ctx, deps); err != nil {
		log.Printf("[iam-server] openfga init warn: %v（数据级鉴权将降级 fail-closed）", err)
	} else {
		log.Println("[iam-server] openfga schema ready")
	}

	// 后台 worker：消费 CMDB 变更事件（Redis Streams，与审计事件总线两用）
	go consumeCMDBEvents(ctx, deps)
	// 数据契约巡检 + 深对账双定时循环（清单 A4/A5b：指纹比对→增量同步→确认制时钟刷新；天级全量兜底）
	go patrolLoop(ctx, deps)

	gin.SetMode(gin.ReleaseMode)
	r := api.NewRouter(deps)
	log.Printf("[iam-server] listening %s", cfg.HTTPAddr)
	if err := r.Run(cfg.HTTPAddr); err != nil {
		log.Fatal(err)
	}
}

// ensureOpenFGA 重试 EnsureSchema（最多 10 次，间隔 2s）
func ensureOpenFGA(ctx context.Context, deps *api.Deps) error {
	var err error
	for i := 1; i <= 10; i++ {
		if err = deps.DataPlane.EnsureSchema(ctx); err == nil {
			return nil
		}
		log.Printf("[iam-server] openfga init retry %d/10: %v", i, err)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return err
}
