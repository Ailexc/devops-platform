// iam-server：中心 PDP + 管理 API（判定与控制面 HTTP——1.5 起后台仅 iam-sync 的 TTL 回收）
package main

import (
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

	// （1.5 T3）OpenFGA 数据面与后台同步循环均已退役：数据级=点查权威行（material/CheckRow），
	// 后台仅存 iam-sync 的 TTL 回收；本进程纯判定/API，可独立多副本

	gin.SetMode(gin.ReleaseMode)
	r := api.NewRouter(deps)
	log.Printf("[iam-server] listening %s", cfg.HTTPAddr)
	if err := r.Run(cfg.HTTPAddr); err != nil {
		log.Fatal(err)
	}
}

// ensureOpenFGA 已抽至 internal/api 的 (*Deps).EnsureOpenFGA——cmd/iam-server 与 cmd/iam-sync 共用（清单 S1）
