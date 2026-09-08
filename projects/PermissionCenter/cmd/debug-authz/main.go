package main
// 临时调试：直接加载策略快照并求值
package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/store"
)

func main() {
	cfg := config.Load()
	db, err := store.Open(cfg.PGDSN)
	if err != nil {
		panic(err)
	}
	cache, err := store.NewCache(cfg.RedisAddr)
	if err != nil {
		panic(err)
	}
	apps := store.NewAppRepo(db)
	users := store.NewUserRepo(db)
	groups := store.NewGroupRepo(db)
	access := store.NewAccessRepo(db)
	pol := store.NewPolicyRepo(db)
	b := authz.NewBuilder(cache, apps, users, groups, access, pol, apps)
	ps, err := b.LoadOrBuild(context.Background(), 1)
	if err != nil {
		panic(err)
	}
	raw, _ := json.MarshalIndent(ps.Conditions, "", "  ")
	fmt.Println("CONDITIONS:", string(raw))

	en, _ := authz.NewEnforcer()
	en.Reset(ps.Policies, ps.Groupings)

	for _, tc := range [][]string{
		{"u:3", "cmdb", "cmdb:host:create"},
		{"u:3", "cmdb", "cmdb:host:update"},
		{"u:3", "cmdb", "cmdb:host:read"},
	} {
		ok, matched, err := en.EnforceEx(tc[0], tc[1], tc[2], "*")
		fmt.Printf("Enforce %v -> ok=%v matched=%v err=%v\n", tc, ok, matched, err)
	}
	// matchPids 验证
	closure := en.ResolveClosure("u:3", ps.Groupings)
	fmt.Println("closure u:3:", closure)
}
