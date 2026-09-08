package authz

import (
	"strconv"

	"github.com/casbin/casbin/v2"
	"github.com/casbin/casbin/v2/model"
)

// Enforcer Casbin 封装：动作级 RBAC 判断
type Enforcer struct {
	e *casbin.Enforcer
}

func NewEnforcer() (*Enforcer, error) {
	m, err := model.NewModelFromString(CasbinModel)
	if err != nil {
		return nil, err
	}
	e, err := casbin.NewEnforcer(m)
	if err != nil {
		return nil, err
	}
	return &Enforcer{e: e}, nil
}

// Reset 重建策略（原子替换，用于缓存加载）
func (en *Enforcer) Reset(policies, groupings [][]string) error {
	en.e.ClearPolicy()
	for _, g := range groupings {
		if _, err := en.e.AddGroupingPolicy(g); err != nil {
			return err
		}
	}
	for _, p := range policies {
		if _, err := en.e.AddPolicy(p); err != nil {
			return err
		}
	}
	return en.e.BuildRoleLinks()
}

// EnforceEx 求值并返回命中的第一条策略行（第 6 列 = pid）
func (en *Enforcer) EnforceEx(sub, dom, obj, act string) (bool, []string, error) {
	return en.e.EnforceEx(sub, dom, obj, act)
}

// Check 布尔判断
func (en *Enforcer) Check(sub, dom, obj, act string) (bool, error) {
	return en.e.Enforce(sub, dom, obj, act)
}

// ResolveClosure 解析主体可达闭包（成员 + 组嵌套），用于策略匹配
func (en *Enforcer) ResolveClosure(sub string, groupings [][]string) []string {
	seen := map[string]bool{sub: true}
	queue := []string{sub}
	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		for _, g := range groupings {
			if len(g) != 2 || g[0] != cur {
				continue
			}
			if !seen[g[1]] {
				seen[g[1]] = true
				queue = append(queue, g[1])
			}
		}
	}
	out := make([]string, 0, len(seen))
	for k := range seen {
		out = append(out, k)
	}
	return out
}

// 主体 key：u:{user_id} / g:{group_id} / s:{client_id}
func SubjUser(id uint64) string     { return "u:" + strconv.FormatUint(id, 10) }
func SubjGroup(id uint64) string    { return "g:" + strconv.FormatUint(id, 10) }
func SubjService(cid string) string { return "s:" + cid }
