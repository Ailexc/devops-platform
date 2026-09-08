package authz

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"strconv"
	"strings"
	"time"

	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// Decision 决策结果
type Decision struct {
	Allow  bool   `json:"decision"`
	Code   string `json:"code,omitempty"`
	Reason string `json:"reason,omitempty"`
}

// CheckRequest 鉴权请求（供网关/下游）
type CheckRequest struct {
	User     string         `json:"user"`      // "alice" 或 "client:cloud-mgmt"
	App      string         `json:"app"`       // 应用 code
	Action   string         `json:"action"`    // 权限点 code
	Resource string         `json:"resource"`  // 可选
	Context  map[string]any `json:"context"`   // ip / time 等
	TraceID  string         `json:"trace_id"`  // 链路追踪 ID（网关注入/生成）
	PEP      map[string]any `json:"pep"`       // 网关 PEP 解析信息（method/path/匹配方式/解析资源）
}

// Checker 中心 PDP 决策核心（动作级）
type Checker struct {
	cfg      *config.Config
	cache    *store.Cache
	builder  *Builder
	enforcer *Enforcer
	users    *store.UserRepo
	apps     *store.AppRepo
	pol      *store.PolicyRepo
	logs     *store.SyncRepo
}

func NewChecker(cfg *config.Config, cache *store.Cache, builder *Builder, enforcer *Enforcer, users *store.UserRepo, apps *store.AppRepo, pol *store.PolicyRepo, logs *store.SyncRepo) *Checker {
	return &Checker{cfg: cfg, cache: cache, builder: builder, enforcer: enforcer, users: users, apps: apps, pol: pol, logs: logs}
}

// Check 执行动作级鉴权：RBAC(Casbin) + ABAC conditions(自研求值)
func (c *Checker) Check(ctx context.Context, req CheckRequest) (*Decision, error) {
	d, _, err := c.CheckWithPids(ctx, req)
	return d, err
}

// CheckWithPids 同 Check，额外返回命中策略 ID（数据级授权复用）
func (c *Checker) CheckWithPids(ctx context.Context, req CheckRequest) (*Decision, []string, error) {
	start := time.Now()

	// 1. 解析主体
	sub, subType, userID, err := c.resolveSubject(ctx, req.User)
	if err != nil {
		return deny("NO_PERMISSION", "unknown subject"), nil, nil
	}
	app, err := c.apps.ByCode(req.App)
	if err != nil {
		return deny("APP_NOT_FOUND", "app not found"), nil, nil
	}

	// 2. 决策缓存（值格式：allow|pid1,pid2）
	cacheKey := fmt.Sprintf("authz:dec:%s:%s:%s", sub, req.App, req.Action)
	if v, err := c.cache.Get(ctx, cacheKey); err == nil && v != "" {
		parts := strings.SplitN(v, "|", 2)
		allow := parts[0] == "1"
		var pids []string
		if len(parts) == 2 && parts[1] != "" {
			pids = strings.Split(parts[1], ",")
		}
		c.writeLog(ctx, userID, app.ID, req, allow, "cache", start)
		if allow {
			return &Decision{Allow: true}, pids, nil
		}
		return deny("NO_PERMISSION", "denied"), pids, nil
	}

	// 3. 加载策略快照（Redis 版本化缓存）
	ps, err := c.builder.LoadOrBuild(ctx, app.ID)
	if err != nil {
		return nil, nil, err
	}
	if err := c.enforcer.Reset(ps.Policies, ps.Groupings); err != nil {
		return nil, nil, err
	}

	// 4. Casbin 求值（RBAC）：deny 优先由 Casbin 策略效果处理
	ok, _, err := c.enforcer.EnforceEx(sub, req.App, req.Action, "*")
	if err != nil {
		return nil, nil, err
	}
	if !ok {
		c.cache.Set(ctx, cacheKey, "0|", c.cfg.DecisionCacheTTL)
		c.writeLog(ctx, userID, app.ID, req, false, "remote", start)
		return deny("NO_PERMISSION", "no matching policy"), nil, nil
	}

	// 5. 收集命中的 allow 策略（供 ABAC conditions + 数据级授权）
	condCtx := &condContext{IP: c.ipFrom(req.Context), Now: time.Now(), UserAttrs: nil}
	if subType == model.SubjectUser && userID > 0 {
		if u, err := c.users.ByID(userID); err == nil {
			condCtx.UserAttrs = u.Attributes
		}
	}
	matchedPids := c.matchPids(ps, sub, req.App, req.Action)
	granted := false
	for _, pid := range matchedPids {
		if conds, exists := ps.Conditions[pid]; exists {
			if !evalConditions(conds, condCtx) {
				continue // 该策略 ABAC 条件不满足，不授予
			}
		}
		granted = true
	}
	if !granted {
		c.cache.Set(ctx, cacheKey, "0|", c.cfg.DecisionCacheTTL)
		c.writeLog(ctx, userID, app.ID, req, false, "remote", start)
		return deny("CONDITION_FAILED", "ABAC condition not satisfied"), nil, nil
	}

	// 6. allow：写决策缓存（带 pid）+ 决策日志（异步）
	c.cache.Set(ctx, cacheKey, "1|"+strings.Join(matchedPids, ","), c.cfg.DecisionCacheTTL)
	c.writeLog(ctx, userID, app.ID, req, true, "remote", start)
	return &Decision{Allow: true}, matchedPids, nil
}

// matchPids 在策略快照中找出该主体可达的 allow 策略 ID（不依赖 Casbin 单规则返回）
func (c *Checker) matchPids(ps *PolicySet, sub, app, action string) []string {
	closure := c.enforcer.ResolveClosure(sub, ps.Groupings)
	in := map[string]bool{}
	for _, s := range closure {
		in[s] = true
	}
	var pids []string
	for _, row := range ps.Policies {
		if len(row) < 6 || row[4] != "allow" {
			continue
		}
		if !in[row[0]] || row[1] != app {
			continue
		}
		if row[2] != "*" && row[2] != action {
			continue
		}
		pids = append(pids, row[5])
	}
	return pids
}

// resolveSubject 用户 "alice" → u:{id}；"client:xxx" → s:xxx
func (c *Checker) resolveSubject(ctx context.Context, user string) (string, int16, uint64, error) {
	if strings.HasPrefix(user, "client:") {
		cid := strings.TrimPrefix(user, "client:")
		return SubjService(cid), model.SubjectService, 0, nil
	}
	u, err := c.users.ByUsername(user)
	if err != nil {
		return "", 0, 0, err
	}
	if u.Status != model.StatusEnabled {
		return "", 0, 0, fmt.Errorf("user disabled")
	}
	return SubjUser(u.ID), model.SubjectUser, u.ID, nil
}

func (c *Checker) ipFrom(ctx map[string]any) string {
	if ctx == nil {
		return ""
	}
	if v, ok := ctx["ip"].(string); ok {
		return v
	}
	return ""
}

func (c *Checker) writeLog(ctx context.Context, userID, appID uint64, req CheckRequest, allow bool, channel string, start time.Time) {
	ch := model.ChannelRemote
	if channel == "cache" {
		ch = model.ChannelRemote
	}
	dec := model.DecisionDeny
	reason := "deny"
	if allow {
		dec = model.DecisionAllow
		reason = "allow"
	}
	// 异步写入决策日志（不阻塞鉴权路径）
	go func() {
		pep := model.JSONMap{}
		if req.PEP != nil {
			for k, v := range req.PEP {
				pep[k] = v
			}
		}
		// 来源标记（观测：cache/remote），供鉴权指标聚合命中率
		pep["from"] = channel
		if err := c.logs.CreateDecision(&model.DecisionLog{
			TraceID:   req.TraceID,
			UserID:    userID,
			AppID:     appID,
			Action:    req.Action,
			Resource:  req.Resource,
			Decision:  int16(dec),
			Reason:    reason,
			Channel:   int16(ch),
			LatencyMS: time.Since(start).Milliseconds(),
			PEP:       pep,
			Context:   req.Context,
		}); err != nil {
			log.Printf("[authz] write decision log failed: %v", err)
		}
	}()
}

func deny(code, reason string) *Decision {
	return &Decision{Allow: false, Code: code, Reason: reason}
}

// ---- ABAC 条件求值（自研策略模型层）----

type condContext struct {
	IP        string
	Now       time.Time
	UserAttrs map[string]any
}

// 支持条件：
// {"time": {"op":"within","from":"09:00","to":"18:00"}}
// {"ip":  {"op":"in","values":["10.0.0.0/8","192.168.1.0/24"]}}
// {"attr":{"op":"eq","field":"level","value":"L3"}}   （读用户 attributes）
func evalConditions(conds map[string]any, ctx *condContext) bool {
	for key, raw := range conds {
		val, ok := raw.(map[string]any)
		if !ok {
			// 兼容 JSONB 解析为嵌套 map
			b, _ := json.Marshal(raw)
			var m map[string]any
			if json.Unmarshal(b, &m) != nil {
				return false
			}
			val = m
		}
		switch key {
		case "time":
			if !evalTimeCond(val, ctx.Now) {
				return false
			}
		case "ip":
			if !evalIPCond(val, ctx.IP) {
				return false
			}
		case "attr":
			if !evalAttrCond(val, ctx.UserAttrs) {
				return false
			}
		default:
			return false
		}
	}
	return true
}

func evalTimeCond(cond map[string]any, now time.Time) bool {
	op, _ := cond["op"].(string)
	if op == "within" {
		from, _ := cond["from"].(string)
		to, _ := cond["to"].(string)
		cur := now.Format("15:04")
		return cur >= from && cur <= to
	}
	return false
}

func evalIPCond(cond map[string]any, ip string) bool {
	if ip == "" {
		return false
	}
	op, _ := cond["op"].(string)
	if op != "in" {
		return false
	}
	rawValues, _ := cond["values"].([]any)
	for _, rv := range rawValues {
		cidr, _ := rv.(string)
		if _, ipnet, err := net.ParseCIDR(cidr); err == nil {
			if ipnet.Contains(net.ParseIP(ip)) {
				return true
			}
		} else if net.ParseIP(cidr) != nil && net.ParseIP(ip).Equal(net.ParseIP(cidr)) {
			return true
		}
	}
	return false
}

func evalAttrCond(cond map[string]any, attrs map[string]any) bool {
	op, _ := cond["op"].(string)
	field, _ := cond["field"].(string)
	want, _ := cond["value"].(string)
	got, ok := attrs[field]
	if !ok {
		return false
	}
	gotStr := fmt.Sprintf("%v", got)
	switch op {
	case "eq":
		return gotStr == want
	case "neq":
		return gotStr != want
	default:
		return false
	}
}

// ScopeCondition 供 filter 输出（加分项：可拼 SQL 条件片段）
func (c *Checker) ScopeConditionFor(pid string) string {
	return strconv.Quote(pid)
}
