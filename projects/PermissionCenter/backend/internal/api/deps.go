// Package api HTTP 层：管理 API + 鉴权 API
package api

import (
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/bundle"
	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/openfga"
	"github.com/xcy/permission-center/internal/store"
	"github.com/xcy/permission-center/internal/sync"
	"gorm.io/gorm"
)

// Deps 依赖容器
type Deps struct {
	Cfg   *config.Config
	DB    *gorm.DB
	Cache *store.Cache

	Users  *store.UserRepo
	Groups *store.GroupRepo
	Apps   *store.AppRepo
	Access *store.AccessRepo
	Pol    *store.PolicyRepo
	Res    *store.ResourceRepo
	Syncs  *store.SyncRepo
	Caps   *store.CapabilityRepo
	Tpls   *store.PolicyTemplateRepo
	// Contracts 数据契约 + 巡检日志（清单 A2/A4：注册期契约、确认制时钟、失败历史）
	Contracts *store.ContractRepo

	JWT *auth.Manager

	Checker   *authz.Checker
	DataPlane *authz.DataPlane
	Builder   *authz.Builder
	OFGA      *openfga.Client

	OpenAPISyncer *sync.OpenAPISyncer
	CMDBConnector *sync.CMDBConnector
	IdentityConn  *sync.IdentityConnector
	BundleMgr     *bundle.Manager
	// Patrol 巡检 + 深对账服务（清单 A4/A5b；API 手动触发 /sync/reconcile 与后台定时循环共用单实例）
	Patrol *sync.PatrolService
}

// NewDeps 组装全部依赖
func NewDeps(cfg *config.Config, db *gorm.DB, cache *store.Cache) *Deps {
	users := store.NewUserRepo(db)
	groups := store.NewGroupRepo(db)
	apps := store.NewAppRepo(db)
	access := store.NewAccessRepo(db)
	pol := store.NewPolicyRepo(db)
	res := store.NewResourceRepo(db)
	syncs := store.NewSyncRepo(db)
	caps := store.NewCapabilityRepo(db)
	contracts := store.NewContractRepo(db)
	tpls := store.NewPolicyTemplateRepo(db)

	jwt := auth.NewManager(cfg.JWTSecret, cfg.JWTAccessTTL, cfg.JWTRefreshTTL)

	ofga := openfga.NewClient(cfg.OpenFGAServerURL)
	builder := authz.NewBuilder(cache, apps, users, groups, access, pol, apps)
	enforcer, _ := authz.NewEnforcer()
	checker := authz.NewChecker(cfg, cache, builder, enforcer, users, apps, pol, syncs)
	dataPlane := authz.NewDataPlane(ofga, res, users, groups, apps, pol)

	bundleMgr := bundle.NewManager(syncs, pol, access, apps, users, groups, cache)

	cmdbConn := sync.NewCMDBConnector(cfg.CMDBBaseURL, res, syncs)
	// 巡检周期 10% 作增量水位重叠窗口（回拨兜两侧时钟偏差，清单 A4）
	overlap := cfg.PatrolInterval / 10
	patrol := sync.NewPatrolService(contracts, res, cmdbConn, syncs, overlap, dataPlane.PurgeInstanceTuples)

	return &Deps{
		Cfg:           cfg,
		DB:            db,
		Cache:         cache,
		Users:         users,
		Groups:        groups,
		Apps:          apps,
		Access:        access,
		Pol:           pol,
		Res:           res,
		Syncs:         syncs,
		Caps:          caps,
		Contracts:     contracts,
		Tpls:          tpls,
		JWT:           jwt,
		Checker:       checker,
		DataPlane:     dataPlane,
		Builder:       builder,
		OFGA:          ofga,
		OpenAPISyncer: sync.NewOpenAPISyncer(access, syncs),
		CMDBConnector: cmdbConn,
		IdentityConn:  sync.NewIdentityConnector(cfg.IdentityBaseURL, users, groups, syncs),
		BundleMgr:     bundleMgr,
		Patrol:        patrol,
	}
}
