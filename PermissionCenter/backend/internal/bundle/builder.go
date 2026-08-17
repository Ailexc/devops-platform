// Package bundle 策略分发（借鉴 OPA bundle）：全量快照 + 版本 + checksum
package bundle

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"

	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// Manager 生成/校验/拉取 bundle
type Manager struct {
	syncs *store.SyncRepo
	pol   *store.PolicyRepo
	acc   *store.AccessRepo
	apps  *store.AppRepo
	users *store.UserRepo
	grps  *store.GroupRepo
	cache *store.Cache
}

func NewManager(syncs *store.SyncRepo, pol *store.PolicyRepo, acc *store.AccessRepo, apps *store.AppRepo, users *store.UserRepo, grps *store.GroupRepo, cache *store.Cache) *Manager {
	return &Manager{syncs: syncs, pol: pol, acc: acc, apps: apps, users: users, grps: grps, cache: cache}
}

// BundleContent bundle 内容：model + 动作级策略快照 + 元数据
type BundleContent struct {
	AppCode      string        `json:"app_code"`
	Revision     int64         `json:"revision"`
	GeneratedAt  string        `json:"generated_at"`
	Policies     []PolicyEntry `json:"policies"`
	GroupPerms   []GroupPermEntry `json:"group_permissions"`
	Groupings    [][]string    `json:"groupings"`
	CasbinModel  string        `json:"casbin_model"`
	// Users username → 主体 key（agent 本地解析：alice → u:2）
	Users map[string]string `json:"users"`
	// ForceRemote 高风险动作：agent 本地命中但标记为强制回源中心
	ForceRemote []string `json:"force_remote"`
}

type PolicyEntry struct {
	SubjectKey string          `json:"subject_key"`
	AppCode    string          `json:"app_code"`
	Actions    []string        `json:"actions"`
	Effect     string          `json:"effect"`
	Conditions json.RawMessage `json:"conditions,omitempty"`
}

type GroupPermEntry struct {
	GroupID uint64   `json:"group_id"`
	Actions []string `json:"actions"`
}

// Publish 全量生成并落库（发布 = version++ → bundle）
func (m *Manager) Publish(ctx context.Context, appID uint64) (*model.Bundle, error) {
	app, err := m.apps.ByID(appID)
	if err != nil {
		return nil, err
	}
	last, err := m.syncs.LatestBundle(appID)
	rev := int64(1)
	if err == nil && last != nil {
		rev = last.Revision + 1
	}
	content, err := m.build(ctx, app)
	if err != nil {
		return nil, err
	}
	raw, _ := json.Marshal(content)
	contentMap := map[string]any{}
	json.Unmarshal(raw, &contentMap)
	// checksum 基于存储形态（sorted-key JSON，与响应中 content 的字节一致）
	servedRaw, _ := json.Marshal(contentMap)
	checksum := sha256.Sum256(servedRaw)
	b := &model.Bundle{
		AppID:       appID,
		Revision:    rev,
		Content:     contentMap,
		Checksum:    hex.EncodeToString(checksum[:]),
		PublishedBy: 0,
	}
	if err := m.syncs.CreateBundle(b); err != nil {
		return nil, err
	}
	return b, nil
}

// Fetch 拉取：带当前版本，无更新返回 nil（304）
func (m *Manager) Fetch(ctx context.Context, appCode string, currentRev int64) (*model.Bundle, bool, error) {
	app, err := m.apps.ByCode(appCode)
	if err != nil {
		return nil, false, err
	}
	last, err := m.syncs.LatestBundle(app.ID)
	if err != nil || last == nil {
		return nil, false, nil
	}
	if currentRev >= last.Revision {
		return nil, false, nil
	}
	return last, true, nil
}

// Verify checksum 校验（失败保留 last-known-good）
func (m *Manager) Verify(b *model.Bundle) bool {
	raw, err := json.Marshal(b.Content)
	if err != nil {
		return false
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]) == b.Checksum
}
// build 组装 bundle：动作级策略快照 + 组关系（数据级不回源进 bundle，agent 只做动作级）
func (m *Manager) build(ctx context.Context, app *model.App) (*BundleContent, error) {
	policies, err := m.pol.ActiveByApp(app.ID)
	if err != nil {
		return nil, err
	}
	actions, err := m.acc.Actions(app.ID)
	if err != nil {
		return nil, err
	}
	actionCode := map[uint64]string{}
	for _, a := range actions {
		actionCode[a.ID] = a.Code
	}
	userName := map[uint64]string{}
	clientID := map[uint64]string{}
	users := map[string]string{} // username → u:{id}（agent 本地解析）
	var forceRemote []string

	// 组关系
	var groupings [][]string
	groups, err := m.grps.Tree()
	if err != nil {
		return nil, err
	}
	for _, g := range groups {
		if g.ParentID != nil {
			groupings = append(groupings, []string{authz.SubjGroup(g.ID), authz.SubjGroup(*g.ParentID)})
		}
	}
	var allUG []model.UserGroup
	if err := m.grps.AllMemberships(&allUG); err != nil {
		return nil, err
	}
	for _, ug := range allUG {
		groupings = append(groupings, []string{authz.SubjUser(ug.UserID), authz.SubjGroup(ug.GroupID)})
	}

	// 用户映射（agent 需要 username → subject key）
	userIDs := map[uint64]bool{}
	for _, p := range policies {
		if p.SubjectType == model.SubjectUser {
			userIDs[p.SubjectID] = true
		}
		if p.ForceRemote {
			for _, aid := range p.ActionIDs {
				if code, ok := actionCode[aid]; ok {
					forceRemote = append(forceRemote, code)
				}
			}
		}
	}
	for id := range userIDs {
		if u, err := m.users.ByID(id); err == nil {
			userName[id] = authz.SubjUser(u.ID)
			users[u.Username] = authz.SubjUser(u.ID)
		}
	}

	// 策略条目
	var entries []PolicyEntry
	for i := range policies {
		p := &policies[i]
		sub, ok := m.subjectKey(p, userName, clientID)
		if !ok {
			continue
		}
		objs := []string{"*"}
		if len(p.ActionIDs) > 0 {
			objs = nil
			for _, aid := range p.ActionIDs {
				if code, ok := actionCode[aid]; ok {
					objs = append(objs, code)
				}
			}
		}
		eft := "allow"
		if p.Effect == model.EffectDeny {
			eft = "deny"
		}
		conds, _ := json.Marshal(p.Conditions)
		entries = append(entries, PolicyEntry{
			SubjectKey: sub,
			AppCode:    app.Code,
			Actions:    objs,
			Effect:     eft,
			Conditions: conds,
		})
	}

	// 组权限（组即角色）
	var groupPerms []GroupPermEntry
	groups, err = m.grps.ActiveGroups()
	if err == nil {
		for _, g := range groups {
			ids, err := m.acc.GroupPermissionIDs(g.ID)
			if err != nil || len(ids) == 0 {
				continue
			}
			var codes []string
			for _, id := range ids {
				if c, ok := actionCode[id]; ok {
					codes = append(codes, c)
				}
			}
			groupPerms = append(groupPerms, GroupPermEntry{GroupID: g.ID, Actions: codes})
		}
	}

	return &BundleContent{
		AppCode:     app.Code,
		Revision:    0, // 由 Publish 填充
		GeneratedAt: fmt.Sprintf("%d", 0),
		Policies:    entries,
		GroupPerms:  groupPerms,
		Groupings:   groupings,
		CasbinModel: authz.CasbinModel,
		Users:       users,
		ForceRemote: forceRemote,
	}, nil
}

func (m *Manager) subjectKey(p *model.Policy, userName, clientID map[uint64]string) (string, bool) {
	switch p.SubjectType {
	case model.SubjectUser:
		if _, ok := userName[p.SubjectID]; !ok {
			u, err := m.users.ByID(p.SubjectID)
			if err != nil {
				return "", false
			}
			userName[p.SubjectID] = authz.SubjUser(u.ID)
		}
		return userName[p.SubjectID], true
	case model.SubjectGroup:
		return authz.SubjGroup(p.SubjectID), true
	case model.SubjectService:
		if _, ok := clientID[p.SubjectID]; !ok {
			c, err := m.apps.ClientByRowID(p.SubjectID)
			if err != nil {
				return "", false
			}
			clientID[p.SubjectID] = authz.SubjService(c.ClientID)
		}
		return clientID[p.SubjectID], true
	default:
		return "", false
	}
}
