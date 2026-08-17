package authz

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// PolicySet Casbin 策略快照（构建自 users/groups/roles/policies，策略即数据）
type PolicySet struct {
	AppID      uint64                     `json:"app_id"`
	Version    int64                      `json:"version"`
	Policies   [][]string                 `json:"policies"`   // [sub, dom, obj, act, eft, pid]
	Groupings  [][]string                 `json:"groupings"`  // [child, parent]
	Conditions map[string]map[string]any  `json:"conditions"` // pid -> ABAC 条件
}

const (
	psetKeyFmt = "authz:pset:%d"
	verKeyFmt  = "authz:ver:%d"
)

// Builder 从 DB 构建策略快照，并带 Redis 版本化缓存
type Builder struct {
	cache *store.Cache
	apps  *store.AppRepo
	users *store.UserRepo
	grps  *store.GroupRepo
	acc   *store.AccessRepo
	pol   *store.PolicyRepo
	clis  *store.AppRepo
}

func NewBuilder(cache *store.Cache, apps *store.AppRepo, users *store.UserRepo, grps *store.GroupRepo, acc *store.AccessRepo, pol *store.PolicyRepo, clis *store.AppRepo) *Builder {
	return &Builder{cache: cache, apps: apps, users: users, grps: grps, acc: acc, pol: pol, clis: clis}
}

// Bump 策略变更时递增版本号（使缓存失效）
func (b *Builder) Bump(ctx context.Context, appID uint64) error {
	return b.cache.Set(ctx, fmt.Sprintf(verKeyFmt, appID), strconv.FormatInt(time.Now().UnixNano(), 10), 0)
}

// LoadOrBuild 优先读 Redis 快照，未命中则从 DB 构建并缓存
func (b *Builder) LoadOrBuild(ctx context.Context, appID uint64) (*PolicySet, error) {
	ver, err := b.cache.Get(ctx, fmt.Sprintf(verKeyFmt, appID))
	if err == nil {
		if raw, err2 := b.cache.Get(ctx, fmt.Sprintf(psetKeyFmt, appID)); err2 == nil {
			var ps PolicySet
			if json.Unmarshal([]byte(raw), &ps) == nil && strconv.FormatInt(ps.Version, 10) == ver {
				return &ps, nil
			}
		}
	}
	ps, err := b.Build(ctx, appID)
	if err != nil {
		return nil, err
	}
	if raw, err := json.Marshal(ps); err == nil {
		b.cache.Set(ctx, fmt.Sprintf(psetKeyFmt, appID), string(raw), time.Minute*5)
	}
	return ps, nil
}

// Build 从 DB 构建策略快照
func (b *Builder) Build(ctx context.Context, appID uint64) (*PolicySet, error) {
	app, err := b.apps.ByID(appID)
	if err != nil {
		return nil, err
	}
	ps := &PolicySet{AppID: appID, Version: time.Now().UnixNano(), Conditions: map[string]map[string]any{}}

	// 权限点 id -> code
	actions, err := b.acc.Actions(appID)
	if err != nil {
		return nil, err
	}
	actionCode := map[uint64]string{}
	for _, a := range actions {
		actionCode[a.ID] = a.Code
	}

	// 主体 id -> key
	userKey := map[uint64]string{}
	clientKey := map[uint64]string{}

	// 组关系：user_group + 组层级（全局 g，无 domain）
	ps.Groupings, err = b.buildGroupings()
	if err != nil {
		return nil, err
	}

	// 策略 → Casbin 规则
	policies, err := b.pol.ActiveByApp(appID)
	if err != nil {
		return nil, err
	}

	// 收集所有涉及的 subject 并解析 key
	userIDs := map[uint64]bool{}
	clientIDs := map[uint64]bool{}
	for _, p := range policies {
		switch p.SubjectType {
		case model.SubjectUser:
			userIDs[p.SubjectID] = true
		case model.SubjectService:
			clientIDs[p.SubjectID] = true
		}
	}
	for id := range userIDs {
		if u, err := b.users.ByID(id); err == nil {
			userKey[id] = SubjUser(u.ID)
		}
	}
	// service subject：subject_id = clients.id，需解析 client_id
	var cliIDs []uint64
	for id := range clientIDs {
		cliIDs = append(cliIDs, id)
	}
	if len(cliIDs) > 0 {
		if cls, err := b.clis.ClientsByIDs(cliIDs); err == nil {
			for _, c := range cls {
				clientKey[c.ID] = SubjService(c.ClientID)
			}
		}
	}

	for i := range policies {
		p := &policies[i]
		sub, ok := b.subjectKey(p, userKey, clientKey)
		if !ok {
			continue // 主体已删除（孤儿策略跳过）
		}
		eft := "allow"
		if p.Effect == model.EffectDeny {
			eft = "deny"
		}
		pid := strconv.FormatUint(p.ID, 10)
		objs := []string{"*"}
		if len(p.ActionIDs) > 0 {
			objs = nil
			for _, aid := range p.ActionIDs {
				if code, ok := actionCode[aid]; ok {
					objs = append(objs, code)
				}
			}
		}
		if len(objs) == 0 {
			continue
		}
		if len(p.Conditions) > 0 {
			ps.Conditions[pid] = p.Conditions
		}
		for _, obj := range objs {
			ps.Policies = append(ps.Policies, []string{sub, app.Code, obj, "*", eft, pid})
		}
	}

	// 组权限（组即角色）→ 组可直接拥有权限点
	// 自建组 = 人的集合 + 权限集合，直接生成 g(groupID, app, action, *, allow) 规则
	if err := b.appendGroupPermissions(appID, app.Code, ps); err != nil {
		return nil, err
	}

	return ps, nil
}

func (b *Builder) subjectKey(p *model.Policy, userKey, clientKey map[uint64]string) (string, bool) {
	switch p.SubjectType {
	case model.SubjectUser:
		k, ok := userKey[p.SubjectID]
		return k, ok
	case model.SubjectService:
		k, ok := clientKey[p.SubjectID]
		return k, ok
	case model.SubjectGroup:
		return SubjGroup(p.SubjectID), true
	default:
		return "", false
	}
}

// buildGroupings 构建组关系（成员 + 层级）
func (b *Builder) buildGroupings() ([][]string, error) {
	var groupings [][]string
	groups, err := b.grps.Tree()
	if err != nil {
		return nil, err
	}
	// 组层级 g(g:child, g:parent)
	for _, g := range groups {
		if g.ParentID != nil {
			groupings = append(groupings, []string{SubjGroup(g.ID), SubjGroup(*g.ParentID)})
		}
	}
	// 用户成员关系 g(u:uid, g:gid)
	var all []model.UserGroup
	if err := b.grps.AllMemberships(&all); err != nil {
		return nil, err
	}
	for _, ug := range all {
		groupings = append(groupings, []string{SubjUser(ug.UserID), SubjGroup(ug.GroupID)})
	}
	return groupings, nil
}

// appendGroupPermissions 组权限：g 组关系（已在 buildGroupings 中处理用户→组），
// 组直接拥有权限点：g(groupID, app, action, *, allow)
func (b *Builder) appendGroupPermissions(appID uint64, appCode string, ps *PolicySet) error {
	// 获取所有有权限点的组
	groups, err := b.grps.ActiveGroups()
	if err != nil {
		return err
	}
	for _, g := range groups {
		actionIDs, err := b.acc.GroupPermissionIDs(g.ID)
		if err != nil || len(actionIDs) == 0 {
			continue
		}
		actions, err := b.acc.ActionsByIDs(actionIDs)
		if err != nil || len(actions) == 0 {
			continue
		}
		sub := SubjGroup(g.ID)
		for _, a := range actions {
			ps.Policies = append(ps.Policies, []string{sub, appCode, a.Code, "*", "allow", "gp:" + strconv.FormatUint(g.ID, 10)})
		}
	}
	return nil
}
