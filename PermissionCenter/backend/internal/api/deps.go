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

	JWT *auth.Manager

	Checker  *authz.Checker
	DataPlane *authz.DataPlane
	Builder  *authz.Builder
	OFGA     *openfga.Client

	OpenAPISyncer *sync.OpenAPISyncer
	CMDBConnector *sync.CMDBConnector
	IdentityConn  *sync.IdentityConnector
	BundleMgr     *bundle.Manager
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
	tpls := store.NewPolicyTemplateRepo(db)

	jwt := auth.NewManager(cfg.JWTSecret, cfg.JWTAccessTTL, cfg.JWTRefreshTTL)

	ofga := openfga.NewClient(cfg.OpenFGAServerURL)
	builder := authz.NewBuilder(cache, apps, users, groups, access, pol, apps)
	enforcer, _ := authz.NewEnforcer()
	checker := authz.NewChecker(cfg, cache, builder, enforcer, users, apps, pol, syncs)
	dataPlane := authz.NewDataPlane(ofga, res, users, groups, apps, pol)

	bundleMgr := bundle.NewManager(syncs, pol, access, apps, users, groups, cache)

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
		Tpls:          tpls,
		JWT:           jwt,
		Checker:       checker,
		DataPlane:     dataPlane,
		Builder:       builder,
		OFGA:          ofga,
		OpenAPISyncer: sync.NewOpenAPISyncer(access, syncs),
		CMDBConnector: sync.NewCMDBConnector(cfg.CMDBBaseURL, res, syncs),
		IdentityConn:  sync.NewIdentityConnector(cfg.IdentityBaseURL, users, groups, syncs),
		BundleMgr:     bundleMgr,
	}
}
