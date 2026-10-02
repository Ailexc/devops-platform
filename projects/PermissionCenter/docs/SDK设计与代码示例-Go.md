# SDK 设计与代码示例（Go）：icguard —— gin 与 go-restful 双接入

> **状态**：设计定稿示例代码（演进项 P2 的实施蓝图，非已上线代码）｜ 协议与部署见《接入手册-SDK与Agent.md》
> **读者**：要写/要接 SDK 的同学；看完应能回答"SDK 怎么写的、gin 怎么接、BK-CMDB（go-restful）怎么接"。
> **设计铁律贯穿全文**：Agent 纯判定（只算不算数）、SDK 取材（只数不算）、fail-closed（任何错误=拒，永不放行）、零副作用（判不过则业务动作不发生）。

---

## 0. 总览：一份 core，两个壳

```
icguard/                        # 一个 Go module
├── core/                       # ★ 框架无关，全部判定逻辑，只此一份
│   ├── types.go                #   协议结构体（与 Agent 的 /v1/check·filter 对应）
│   ├── client.go               #   判定协议客户端（HTTP + fail-closed）
│   └── router.go               #   路由映射（path 动词 → 动作码，兼容全 POST）
├── gin/                        # 壳①：Gin 服务用（咱自己的 Go 后端）
│   ├── middleware.go           #   gin.HandlerFunc：三步判定收口
│   └── gormhook.go             #   GORM Callback：改/删先判后执行（实体在手零额外查询）
└── goful/                      # 壳②：go-restful 用（BK-CMDB apiserver 风格）
    ├── filter.go               #   restful.FilterFunction：三步判定收口
    └── fetcher.go              #   取材器（借 CMDB 查询语义，见 3.2——不直摸存储）
```

**分层逻辑一句话**：判定"是什么"（core）与判定"挂在哪"（壳）彻底分开——core 管协议、取材归一化、路由匹配、fail-closed；壳只干两件事：**挂钩子 + 从业务数据通道取材**。所以 gin 和 go-restful 不是两个 SDK，是**同一个 SDK 的两件衣服**。

---

## 1. core 包（框架无关）

### 1.1 types.go —— 协议结构体

```go
package core

// CheckRequest 点判定请求——与 Agent 的 POST /v1/check 一一对应（JSON over HTTP，localhost）
type CheckRequest struct {
	User       string         `json:"user"`                  // 谁（网关注入的身份头解析而来）
	Action     string         `json:"action"`                // 动作码 cmdb:host:update
	Model      string         `json:"model"`                 // 数据模型 host
	InstanceID string         `json:"instance_id,omitempty"` // 哪一条
	Operation  string         `json:"operation,omitempty"`   // read/create/update/delete
	Attributes map[string]any `json:"attributes,omitempty"`  // ★ 判定材料：行属性（SDK 取材产出）
	Changes    map[string]any `json:"changes,omitempty"`     // 改时的新值（判"改成这样行不行"）
}

type CheckResponse struct {
	Decision string `json:"decision"`           // allow / deny
	Reason   string `json:"reason,omitempty"`   // no_matching_scope / data_missing / stale
}

// Material 判定材料归一化形状——各适配层把"自家的一行"转成这个（GORM 行 / Mongo 文档 / …）
type Material struct {
	ID         string         `json:"id"`
	Attributes map[string]any `json:"attributes"`
}

type FilterRequest struct {
	User   string     `json:"user"`
	Action string     `json:"action"`
	Model  string     `json:"model"`
	Rows   []Material `json:"rows"` // 列表候选行：交给 Agent 挑出有权限的
}

type FilterResponse struct {
	AllowedIDs []string `json:"allowed_ids"`
	Stale      bool     `json:"stale"` // 陈旧标注（降级续判语义，业务可自行决定提示）
}
```

### 1.2 client.go —— 判定客户端（fail-closed 的家在这里）

```go
package core

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// AgentClient 判定协议客户端——无状态、线程安全、纯 HTTP。
//
// ★ 失败语义（铁律，本文件是它唯一的实现处）：
//   任何通信/协议/超时错误 → 一律 (allow=false, err!=nil)——
//   fail-closed（失败关闭）：数据判定路径永不 fail-open（失败放行）。
type AgentClient struct {
	base string
	hc   *http.Client
}

func NewAgentClient(addr string) *AgentClient {
	return &AgentClient{
		base: addr,
		hc:   &http.Client{Timeout: 200 * time.Millisecond}, // localhost 判定，超时给极小值
	}
}

// Check 点判定：接口级与数据级合并判（带 Attributes 即数据级）
func (c *AgentClient) Check(ctx context.Context, req CheckRequest) (allow bool, reason string, err error) {
	var resp CheckResponse
	if err := c.post(ctx, "/v1/check", req, &resp); err != nil {
		return false, "agent_unreachable", err // ★ 错误=拒
	}
	return resp.Decision == "allow", resp.Reason, nil
}

// Filter 列表过滤：候选行进、有权限的行出
func (c *AgentClient) Filter(ctx context.Context, req FilterRequest) (FilterResponse, error) {
	var resp FilterResponse
	if err := c.post(ctx, "/v1/filter", req, &resp); err != nil {
		return FilterResponse{}, err // ★ 调用方见 err 必须拒（fail-closed）
	}
	return resp, nil
}

func (c *AgentClient) post(ctx context.Context, path string, in, out any) error {
	body, _ := json.Marshal(in)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.base+path, bytes.NewReader(body))
	if err != nil {
		return err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpResp, err := c.hc.Do(httpReq)
	if err != nil {
		return fmt.Errorf("agent %s: %w", path, err)
	}
	defer httpResp.Body.Close()
	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("agent %s: status %d", path, httpResp.StatusCode)
	}
	return json.NewDecoder(httpResp.Body).Decode(out)
}
```

### 1.3 router.go —— 路由映射（path 动词，兼容全 POST 风格）

```go
package core

import "regexp"

// Route 一条路由规则。关键设计：语义动词在**路径**上——
// 既覆盖 REST 风格（GET/PATCH/DELETE），也覆盖全 POST 风格（bk-cmdb 的
// /api/v3/find|create|update|delete/...，method 一律 POST，动词在 URL 里）。
type Route struct {
	Method  string         // "" = 不限 method（全 POST 系 API 用这个）
	Pattern *regexp.Regexp // 路径正则
	Action  string         // 动作码：cmdb:host:update
	Model   string         // 数据模型：host（数据级判定用）
	Verb    string         // read/create/update/delete（执行语义，决定判定材料怎么用）
}

type Router struct{ routes []Rule }

func NewRouter() *Router { return &Router{} }

// Add 示例（REST 风格）：  Add("PATCH", `^/api/hosts/(?P<id>\d+)$`, "cmdb:host:update", "host", "update")
// Add 示例（全 POST）：    Add("",     `^/api/v3/update/inst/host/(?P<id>\d+)/?$`, "cmdb:host:update", "host", "update")
func (r *Router) Add(method, pattern, action, model, verb string) *Router {
	r.routes = append(r.routes, Rule{
		Method: method, Pattern: regexp.MustCompile(pattern),
		Action: action, Model: model, Verb: verb,
	})
	return r
}

// Match 命中第一条；未命中 = 未分类路由 → 调用方按 deny-by-default（默认拒绝）拒绝
func (r *Router) Match(method, path string) (Rule, bool) {
	for _, rt := range r.routes {
		if rt.Method != "" && rt.Method != method {
			continue
		}
		if rt.Pattern.MatchString(path) {
			return rt, true
		}
	}
	return Rule{}, false
}
```

### 1.4 路由表从哪来（重要——不要手写逐条登记）

**这张表是翻译表，不是权限规则**：判定的单位是**动作码**（`cmdb:host:read`，策略围绕动作码组织），而请求只有 URL——表干的唯一一件事是 **HTTP 请求 → 动作码** 翻译。数据级判定不走它（走取材+范围比对）。手写逐条正则只是示例/兜底形态，**登记动作按三级来源自动化**：

| 级 | 来源 | 地位 |
|---|---|---|
| ① **OpenAPI 自动生成** | 能力包发布本就携带 OpenAPI——动作码与路由映射**同源生成**，零手写 | **常态（首选）** |
| ② 框架路由扫描 + 约定推导 | 启动导出框架路由表（gin 有 `r.Routes()`）按 REST 约定推导：`GET /hosts/:id` → `host:read`、`POST /hosts` → `host:create` | 无 OpenAPI 时主路 |
| ③ 手写规则 | **前缀/通配批量**登记（`AddPrefix("/api/v3/", "cmdb:")`），不逐条正则 | 老系统兜底 |

```go
// ① 从能力包的 OpenAPI 生成（常态）——与发布方注册能力包时用同一份 OpenAPI
router, err := core.BuildRouterFromOpenAPI(openapiSpec, appCode) // 动作码/路由映射同源
// ② 从框架路由表推导
router = core.BuildRouterFromGin(r, appCode, overrides) // 约定推导 + 少量人工覆盖
```

**"未登记 → 403"是刻意设计**（路由三分类：没分类的默认要鉴权，防新接口悄悄裸奔）——登记自动化之后这道防线才真正站得住。示例中的 `/api/hosts` 是占位业务路径，实际为接入方自己的 API 路径。

---

## 2. 壳①：icguard-gin（咱自己的 Go 后端）

### 2.1 middleware.go —— 三步判定收口

```go
package icguardgin

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"your.corp/icguard/core"
)

// Fetcher 取材函数由接入方给出（走自己的数据通道）——SDK 不猜你的存储
type Fetcher func(c *gin.Context, rt core.Route) ([]core.Material, error)

type Config struct {
	Client *core.AgentClient
	Router *core.Router
	Fetch  Fetcher // 读/列表取材（改/删的取材走 GORM 钩子，见 gormhook.go）
	Exempt []string
}

// Middleware 挂进 Gin：请求最前面完成 接口级 → 取材 → 数据级
func Middleware(cfg Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		if exempt(cfg.Exempt, c.Request.URL.Path) {
			c.Next()
			return
		}
		rt, ok := cfg.Router.Match(c.Request.Method, c.Request.URL.Path)
		if !ok {
			// 未分类路由 → 拒（deny-by-default 的落点）
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "route not registered"})
			return
		}
		user := currentUser(c) // 网关注入的身份头（X-Auth-*）

		// ① 接口级（包内存比对，µs 级）
		if allow, reason, err := cfg.Client.Check(c.Request.Context(), core.CheckRequest{
			User: user, Action: rt.Action, Model: rt.Model, Operation: rt.Verb,
		}); err != nil || !allow {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden", "reason": reasonOr(reason, err)})
			return
		}

		// 增：请求参数即"未来的行"，接口级+模型级已覆盖，直接放行
		if rt.Verb == "create" {
			c.Next()
			return
		}

		// ② 取材（读/列表：候选行）——取不到=接入问题=报错拒绝（取材铁律）
		rows, err := cfg.Fetch(c, rt)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusNotFound, gin.H{"error": "material fetch failed", "detail": err.Error()})
			return
		}

		// ③ 数据级
		if isList(c, rt) {
			// 列表：候选行交给 Agent 挑
			resp, err := cfg.Client.Filter(c.Request.Context(), core.FilterRequest{
				User: user, Action: rt.Action, Model: rt.Model, Rows: rows,
			})
			if err != nil {
				c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "judgment failed (fail-closed)"})
				return
			}
			c.Set("icguard_allowed_ids", resp.AllowedIDs) // 业务层据此过滤展示
			c.Set("icguard_stale", resp.Stale)
		} else {
			// 点：取回的那一行就是判定材料
			allow, reason, err := cfg.Client.Check(c.Request.Context(), core.CheckRequest{
				User: user, Action: rt.Action, Model: rt.Model, InstanceID: rows[0].ID,
				Operation: rt.Verb, Attributes: rows[0].Attributes,
			})
			if err != nil || !allow {
				c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden", "reason": reasonOr(reason, err)})
				return
			}
		}
		c.Next() // 全过才进业务 handler
	}
}
```

### 2.2 gormhook.go —— 改/删的"先判后执行"（实体在手，零额外查询）

```go
package icguardgin

import (
	"context"
	"errors"

	"gorm.io/gorm"
	"your.corp/icguard/core"
)

// ErrDenied 判不过的哨兵错误：GORM 回调注入后事务不提交 → 零副作用
var ErrDenied = errors.New("icguard: denied")

const ctxUserKey = "icguard.user"

// RegisterGORMHooks 把写判定挂进 GORM 生命周期：
//   Update 前 / Delete 前判一次——实体已经在 Statement 里（业务刚 First 出来的），
//   取材=顺手归一化，**零额外查询**；判不过 → AddError(ErrDenied) → 事务回滚，落库不发生。
func RegisterGORMHooks(db *gorm.DB, client *core.AgentClient, actionFor func(model, verb string) string) {
	check := func(tx *gorm.DB, verb string) {
		user, _ := tx.Statement.Context.Value(ctxUserKey).(string)
		if user == "" {
			_ = tx.AddError(ErrDenied) // 没有身份进来写 = 拒（deny-by-default）
			return
		}
		model := tx.Statement.Schema.Name // Host / Instance ...
		attrs := rowAttrs(tx)             // 归一化实体 → map[string]any（判定材料）
		changes := changeAttrs(tx)        // 改时的新值（update 的 Dest）
		allow, _, err := client.Check(tx.Statement.Context, core.CheckRequest{
			User: user, Action: actionFor(model, verb), Model: model,
			Operation: verb, Attributes: attrs, Changes: changes,
		})
		if err != nil || !allow {
			_ = tx.AddError(ErrDenied) // ★ 判不过 → 事务不提交，零副作用
		}
	}
	_ = db.Callback().Update().Before("gorm:update").Register("icguard:check", func(tx *gorm.DB) { check(tx, "update") })
	_ = db.Callback().Delete().Before("gorm:delete").Register("icguard:check", func(tx *gorm.DB) { check(tx, "delete") })
}
```

> 说明：`db.Delete(&h)`（实体在手）零额外查询；`db.Delete(&Host{}, id)`（只给 ID）时回调内补一次按 ID 点查即可（一次索引命中）。业务习惯"先查后改/删"的话永远走前者。

### 2.3 业务项目接入（Gin，配置一次 + 业务代码零权限）

```go
// main.go —— 一次接入，全接口覆盖
// ★ Agent 地址从配置/环境变量读，不写死 IP：
//   sidecar 同 Pod（推荐）= http://127.0.0.1:9090（回环即通信，刻意为之）
//   独立部署            = http://iam-agent:9090（compose/K8s 服务名，DNS 解析）
agent := core.NewAgentClient(cfg.GetString("ICGUARD_AGENT_URL"))

// 路由表：常态由 OpenAPI/框架路由自动生成（见 §1.4）——手写仅为示意/兜底
router := core.NewRouter().
	Add("GET",    `^/api/hosts/(?P<id>\d+)$`, "cmdb:host:read",   "host", "read").
	Add("POST",   `^/api/hosts$`,            "cmdb:host:create", "host", "create").
	Add("PATCH",  `^/api/hosts/(?P<id>\d+)$`, "cmdb:host:update", "host", "update").
	Add("DELETE", `^/api/hosts/(?P<id>\d+)$`, "cmdb:host:delete", "host", "delete")

r := gin.New()
r.Use(icguardgin.Middleware(icguardgin.Config{
	Client: agent,
	Router: router,
	Fetch:  fetchFromDB, // 你的 DAO 取行：db.Where("id = ?", id).First(...)
	Exempt: []string{"/healthz"},
}))
icguardgin.RegisterGORMHooks(db, agent, defaultActionFor)

// 业务 handler —— 一个权限字都没有
func updateHost(c *gin.Context) {
	var h Host
	db.First(&h, c.Param("id"))  // 取材顺手（中间件已判"能不能读"，钩子将判"能不能改"）
	h.Name = c.PostForm("name")
	db.Save(&h)                   // GORM 钩子已判：判不过 ErrDenied → 事务不提交
	c.JSON(200, h)
}
```

---

## 3. 壳②：icguard-goful（BK-CMDB 的 go-restful 接入）

### 3.1 filter.go —— restful.FilterFunction

```go
package icguardgoful

import (
	"net/http"

	restful "github.com/emicklei/go-restful/v3"
	"your.corp/icguard/core"
)

type Fetcher func(req *restful.Request, rt core.Route) ([]core.Material, error)

type Config struct {
	Client *core.AgentClient
	Router *core.Router
	Fetch  Fetcher
	Exempt []string
}

// Filter 挂进 go-restful Container（bk-cmdb apiserver 风格）：
// 与 gin 壳同款三步，只是挂钩点从 gin.HandlerFunc 换成 restful.FilterFunction
func Filter(cfg Config) restful.FilterFunction {
	return func(req *restful.Request, resp *restful.Response, chain *restful.FilterChain) {
		path := req.Request.URL.Path
		if exempt(cfg.Exempt, path) {
			chain.ProcessFilter(req, resp)
			return
		}
		rt, ok := cfg.Router.Match(req.Request.Method, path)
		if !ok {
			resp.WriteErrorString(http.StatusForbidden, "route not registered (deny-by-default)")
			return
		}
		user := req.HeaderParameter("X-Bk-Username") // 蓝鲸风格用户头（或统一 X-Auth-*）

		if allow, reason, err := cfg.Client.Check(req.Request.Context(), core.CheckRequest{
			User: user, Action: rt.Action, Model: rt.Model, Operation: rt.Verb,
		}); err != nil || !allow {
			resp.WriteErrorString(http.StatusForbidden, "forbidden: "+reasonOr(reason, err))
			return
		}
		if rt.Verb == "create" {
			chain.ProcessFilter(req, resp)
			return
		}
		rows, err := cfg.Fetch(req, rt) // ★ 取材：借 CMDB 自己的查询语义（3.2），不直摸存储
		if err != nil {
			resp.WriteErrorString(http.StatusNotFound, "material fetch failed")
			return
		}
		if rt.Verb == "read" && isListRoute(path) {
			fresp, err := cfg.Client.Filter(req.Request.Context(), core.FilterRequest{
				User: user, Action: rt.Action, Model: rt.Model, Rows: rows,
			})
			if err != nil {
				resp.WriteErrorString(http.StatusInternalServerError, "judgment failed (fail-closed)")
				return
			}
			req.SetAttribute("icguard_allowed_ids", fresp.AllowedIDs)
		} else {
			allow, reason, err := cfg.Client.Check(req.Request.Context(), core.CheckRequest{
				User: user, Action: rt.Action, Model: rt.Model,
				InstanceID: rows[0].ID, Operation: rt.Verb, Attributes: rows[0].Attributes,
			})
			if err != nil || !allow {
				resp.WriteErrorString(http.StatusForbidden, "forbidden: "+reasonOr(reason, err))
				return
			}
		}
		chain.ProcessFilter(req, resp) // 全过才进原 handler（CMDB 的业务逻辑一行不动）
	}
}
```

### 3.2 fetcher.go —— 取材器（借 CMDB 自己的查询语义，不是直摸存储）

```go
package icguardgoful

import (
	restful "github.com/emicklei/go-restful/v3"
	"your.corp/icguard/core"
)

// ★ 取材原则（铁律）：取材走数据持有方自己的查询语义，SDK 不重新理解它的数据模型。
// bk-cmdb 三维度（模型元数据 / 实例 / 实例关联）的查询语义都在它自己的服务层——
// 直接摸 Mongo = 重新实现一份对它内部 schema 的理解（集合布局/拓扑层级/字段类型系统
// 都是实现细节不是契约，版本升级或二开演进即碎）→ 反模式，禁止。
//
// 形态 A（首选，二开同仓）：进程内调它自己的查询函数（与 find handler 同一条代码路径）
// 形态 B（跨进程）：调它自己的通用查询接口（POST /api/v3/find/...）
// 两者都只借语义；SDK 唯一的工作 = 从返回结果挑判定字段归一化成 Material。

// CmdbQuerier CMDB 查询语义的窄接口（形态 A）——由二开代码给出实现，绑到 coreservice
type CmdbQuerier interface {
	FindInstance(ctx context.Context, model, id string) (map[string]any, error) // 实例维度
	FindInstAsst(ctx context.Context, model, id string) ([]map[string]any, error) // 关联维度（按需）
}

// FetchByCmdbQuery 进程内取材：调 CMDB 自己的查询语义取行（零网络、语义与业务查询一致）
func FetchByCmdbQuery(q CmdbQuerier, param string) Fetcher {
	return func(req *restful.Request, rt core.Route) ([]core.Material, error) {
		id := req.PathParameter(param) // 例：/api/v3/update/inst/host/{bk_host_id}
		inst, err := q.FindInstance(req.Request.Context(), rt.Model, id)
		if err != nil {
			return nil, err // ★ 取不到=报错拒绝（取材铁律：绝不"取不到就放行"）
		}
		return []core.Material{{ID: id, Attributes: pickJudgmentFields(inst)}}, nil
	}
}

// pickJudgmentFields 从查询结果挑判定字段（account/owner/env…）——能力包数据契约声明的字段清单
func pickJudgmentFields(inst map[string]any) map[string]any { /* ... */ return nil }
```

> **为什么不让 SDK 直查 Mongo**（反模式警示）：实例按模型分集合、关联独立成表、模型属性本身是元数据——SDK 直查就得重新理解这三维度的全部布局与语义，**查不全且必碎**；借查询语义则三维度（模型/实例/关联）天然完整，升级不动 SDK。"取材走业务原生通道"的本义就是这个。

### 3.3 apiserver 接入（全 POST 路由表 + 一个 Filter，业务零改动）

```go
// apiserver/main.go（二开落点——就加两段）
container := restful.NewContainer()

// ★ 全 POST 风格：method 留空（或断言 "POST"），语义动词全在路径上
//   （本表为示意；常态由 OpenAPI/路径前缀规则批量生成，见 §1.4）
router := core.NewRouter().
	Add("", `^/api/v3/find/hosts/?$`,                  "cmdb:host:read",   "host", "read").
	Add("", `^/api/v3/create/inst/host/?$`,            "cmdb:host:create", "host", "create").
	Add("", `^/api/v3/update/inst/host/(?P<id>\d+)/?$`, "cmdb:host:update", "host", "update").
	Add("", `^/api/v3/delete/inst/host/(?P<id>\d+)/?$`, "cmdb:host:delete", "host", "delete")

container.Filter(icguardgoful.Filter(icguardgoful.Config{
	Client: core.NewAgentClient(cfg.GetString("ICGUARD_AGENT_URL")), // 配置读取：sidecar=127.0.0.1 / 独立=iam-agent 服务名
	Router: router,
	Fetch:  icguardgoful.FetchByCmdbQuery(cmbdQuerier, "id"), // ★ 取材借 CMDB 查询语义（§3.2），不直摸存储
	Exempt: []string{"/healthz", "/api/v3/find/hosts/biz/.*"}, // 内部取数路由豁免
}))
// 其余 apiserver 路由、coreservice 调用、Mongo 会话——全部不动
```

---

## 4. 两个壳的差异总结（core 一字不改）

| | 壳① icguard-gin | 壳② icguard-goful |
|---|---|---|
| 挂钩点 | `gin.HandlerFunc` 中间件 | `restful.FilterFunction`（Container.Filter） |
| 改/删取材位置 | **GORM Callback**（实体在手，零额外查询） | **Filter 内借 CMDB 查询语义取行**（进程内调用零网络） |
| 读/列表取材 | 业务 DAO（fetcher 函数注入） | CMDB 查询语义（coreservice 函数 / 通用查询接口） |
| 身份头 | `X-Auth-*` | `X-Bk-Username`（蓝鲸风格，可配） |
| 路由风格 | REST（method+path） | **全 POST（path 动词，method 留空）** |
| 业务代码改动 | 零 | 零（一个 Filter + 一段路由表） |

**新增一个框架 = 写一个壳（~100 行）+ 过契约测试**；core、协议、fail-closed 语义零重复。

---

## 5. fail-closed 落点清单（"永不放行"都在哪）

| 位置 | 触发 | 行为 |
|---|---|---|
| `client.go` Check/Filter | Agent 不可达/超时/非 200/解码失败 | `allow=false + err`，调用方拒 |
| middleware / filter ① | 接口级 deny | 403，业务不执行 |
| middleware / filter ②取材 | 取不到判定材料 | 报错拒绝（404/500），**不静默放行** |
| gormhook | 判不过 / 无身份写库 | `ErrDenied` → **事务不提交，零副作用** |
| 未分类路由 | 路由表没登记 | 403（deny-by-default） |
| Agent 自身 | 无 bundle / 包过期 | 拒（Agent 侧 last-known-good 后仍 fail-closed，见接入手册 §2.4） |

---

## 附：契约测试（每个壳发布前必过，见接入手册 §3.5）

1. 无权限调接口 → 403 且业务未执行；2. 范围外改/删 → 403 且**库里零变化**；3. 列表只回范围内行；
4. 取材失败 → 报错拒绝；5. 停 Agent → fail-closed；6. 全 POST 路由表按 path 动词命中正确动作码。
