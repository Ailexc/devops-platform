// iam-server：中心 PDP + 管理 API（判定与控制面 HTTP——后台同步三循环已迁独立进程 cmd/iam-sync，清单 S1）
package main

import (
	"context"
	"log"
	"os"

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
	if err := deps.EnsureOpenFGA(ctx); err != nil {
		log.Printf("[iam-server] openfga init warn: %v（数据级鉴权将降级 fail-closed）", err)
	} else {
		log.Println("[iam-server] openfga schema ready")
	}

	// （S1 迁移）后台同步三循环（worker/patrol/ttl）已迁至独立进程 cmd/iam-sync——
	// 判定可用性不再被后台任务绑架，本进程此后可独立多副本

	gin.SetMode(gin.ReleaseMode)
	r := api.NewRouter(deps)
	log.Printf("[iam-server] listening %s", cfg.HTTPAddr)
	if err := r.Run(cfg.HTTPAddr); err != nil {
		log.Fatal(err)
	}
}

// ensureOpenFGA 已抽至 internal/api 的 (*Deps).EnsureOpenFGA——cmd/iam-server 与 cmd/iam-sync 共用（清单 S1）
