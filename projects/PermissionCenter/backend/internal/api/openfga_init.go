package api

import (
	"context"
	"log"
	"time"
)

// EnsureOpenFGA 重试 EnsureSchema（最多 10 次，间隔 2s）——从 cmd/iam-server 抽出共享（清单 S1）：
// 判定进程（数据级鉴权需 schema）与同步进程（删除级联/关系写入必须 schema）共用同一装配步骤。
func (d *Deps) EnsureOpenFGA(ctx context.Context) error {
	var err error
	for i := 1; i <= 10; i++ {
		if err = d.DataPlane.EnsureSchema(ctx); err == nil {
			return nil
		}
		log.Printf("[openfga] init retry %d/10: %v", i, err)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return err
}
