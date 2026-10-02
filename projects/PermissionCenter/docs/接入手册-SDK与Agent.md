# 权限中心接入手册：SDK 与 Agent（标准接入契约）

> **版本**：v1.0（2026-10-02 设计定稿）｜ **读者**：要接入权限中心的业务系统开发者
> **状态定位（如实）**：本手册是**接入契约与 SDK 设计定稿**——REST 判定端点与 Agent 部署为**现状可做**；SDK 本体为**演进项（P2）**，设计先行、按接入方数量排期开发。未装 SDK 前按 §5 REST 直调接入，契约完全一致。

---

## 0. 一分钟看懂

接入 = **三件套**，缺一不可：

| 件 | 是什么 | 归谁 |
|---|---|---|
| **Agent**（判定器） | 旁挂的轻量容器，拉取策略包本地判定，毫秒级 | 权限中心提供，你部署 |
| **SDK**（收口层） | 装进业务框架的中间件，全接口自动判定，业务代码零权限逻辑 | 权限中心提供，你安装 |
| **能力包契约**（声明） | 数据契约声明标准查询接口（L1 义务），SDK/Agent 据此取判定材料 | 发布能力包时登记 |

```
请求 ──▶ [网关（如在链路上）：只做用户认证（JWT 校验）+ 注入身份头 —— 不做鉴权判定]
       ──▶ [SDK 中间件（业务后端入口，一次接入全接口覆盖）]
           │ ① 接口级：查本地 Agent 的策略包（内存比对，µs 级）
           │ ② 取判定材料：SDK 走你原生数据通道取那一行（查不到=接入问题=报错，不做兜底）
           │ ③ 数据级：清单/条件/变量比对（内存，µs 级）
           ▼
         全过 → 执行业务逻辑（此刻才落库）；任一不过 → 拒，零副作用

Agent（旁挂容器，随业务部署）：轮询拉 bundle ──策略+范围声明──▶ 权限中心（低 QPS）
```

**核心设计一句话**：网关只认证（判断是不是合法用户），鉴权统一收口在业务侧 SDK+Agent——**接入网关与不接网关是同一套逻辑**（鉴权都在你业务侧，再分两层没有意义）；逻辑前置（判定在请求最前面）、物理旁挂（Agent 是独立容器）、取材走原生（数据查询用你自己的数据通道，不透传、不过权限中心）。

### 0.5 设计背景（为什么是这套——三步演进）

1. **第一版（高度集成时代）的痛**：权限判定集中且实时直查上游，体验差、性能瓶颈全压在权限中心、过度依赖 CMDB 数据——"感觉像给 CMDB 做了一套前置校验"；
2. **调研**：OPA（分发强没治理）、Google Zanzibar（数据自治没生命周期）、Spring Security（拦截强没数据级）、XACML（属性供给标准但重）——各有半边，拼不齐；
3. **目标架构（本文）**：判定下沉到业务侧（SDK+Agent），中心只管**策略生命周期**（申请/审批/版本/到期/审计）——"判定跟着数据走"；**企业内部实践定制**：统一契约可强制、SDK 可要求、语言栈收敛（Django/Gin/Spring）、私有仓库分发——市面开源产品做不了的恰是这些，这也是本方案成立的前提。

**与既有接入的兼容（迁移路径）**：已按旧两层（网关判定接口级）接入的应用可平移——路由→动作映射同款，网关判定退场为纯认证后身份头不变，业务侧逐步挂 SDK 即可，不用推倒重来。

---

## 1. 接入清单（照着打勾）

| # | 动作 | 产出/验证 |
|---|---|---|
| 1 | **注册应用**：提交 OpenAPI → 成为应用 owner | 拿到 `app_id` + `app_secret`（Agent 拉包凭证） |
| 2 | **部署 Agent**：compose/k8s 加一个容器（§2） | `GET :9090/healthz` = ok；日志出现 `bundle rev=N activated` |
| 3 | **安装 SDK**：按语言取包（§3.3 分发） | import 成功 |
| 4 | **配置**：中心地址/凭证/路由映射/取材模式（§3.2） | 启动日志 `iam-guard: routes loaded=12` |
| 5 | **发布能力包方**：数据契约声明查询接口（§4） | 数据契约注册校验通过 |
| 6 | **验收**：跑 §7 自测清单 | 5 条全绿 |

---

## 2. Agent 部署（随业务系统一起）

### 2.1 形态与拓扑

- **独立容器**，与业务服务同机或同 Pod（K8s sidecar：同 Pod 双容器共享 localhost）；**不进业务容器、不拦流量**——它是纯判定器，业务调它的 localhost 接口。
- **Agent 的职责边界（铁律）**：只做内存/CPU 级判定运算（查包、比对、求值）——**不查数据、不发外呼、不做取材兜底**。判定材料由 SDK 负责取（见 §6）。
- **网关的职责边界**：只做用户认证（JWT 校验）+ 注入身份头，**不做鉴权判定**——网关内外同一套接入逻辑（都要装 SDK+Agent）。网关仍保留流量防护（防爆破/TLS，免鉴权≠免防护）。

### 2.2 部署样例（docker compose）

```yaml
  # 你的业务服务
  my-service:
    image: my-service:1.0
    depends_on: [iam-agent]

  # 权限中心 Agent（拿来即用，与网关侧同一镜像）
  iam-agent:
    image: iam-backend:latest
    command: ["iam-agent"]
    environment:
      CENTRAL_URL: "https://iam.example.internal"   # 权限中心地址
      APP_ID: "<注册拿到的>"
      APP_SECRET: "<注册拿到的>"                    # 拉策略包的应用凭证
      POLL_INTERVAL: "30s"                          # 策略包轮询周期（撤销传播窗口 ≈ 该值）
      AGENT_ADDR: ":9090"                           # 本地判定接口（勿映射公网端口）
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:9090/healthz"]
    restart: unless-stopped
```

### 2.3 环境变量表

| 变量 | 必填 | 说明 |
|---|---|---|
| `CENTRAL_URL` | ✅ | 权限中心地址 |
| `APP_ID` / `APP_SECRET` | ✅ | 应用凭证（拉包，app 维度切分——你只拿得到自己应用的策略） |
| `POLL_INTERVAL` | 默认 30s | 拉包周期；**策略变更/撤销的生效窗口 ≈ 该值**，高危应用可调短 |
| `AGENT_ADDR` | 默认 :9090 | 本地判定接口监听地址 |

（取材不归 Agent——`FETCH_MODE`/`QUERY_SECRET` 等取材类配置一律不存在：Agent 纯判定、取材归 SDK，见 §6）

### 2.4 运维要点

- **拉不到包/包过期**：保留 last-known-good（上次好的包继续判）；彻底无包 → fail-closed（失败关闭，拒绝）——数据判定路径永不 fail-open（失败放行）；
- **升级**：Agent 独立升级，不动业务；版本与中心兼容矩阵见发行说明；
- **观测**：`/healthz` 存活、日志含 bundle revision、激活时间；中心侧可看各 agent 拉包状态。

---

## 3. SDK 设计

### 3.1 分层形态：**协议统一，差异关进适配层**（这就是跨语言通用的全部秘密）

```
┌─────────────────────────────────────────────┐
│ 核心层 icguard-core（语言内共享，所有框架同款）        │
│   判定协议客户端：调 localhost Agent（/v1/check·filter·manifest）
│   取材器：行属性归一化（对象→{id, attrs}）           │
│   路由映射：method+path → 动作码                     │
├─────────────────────────────────────────────┤
│ 适配层（每框架一个薄壳，~100 行，只做"挂钩子"）          │
│   Django: Middleware + pre_save/pre_delete 信号（样板）│
│   FastAPI/Flask: ASGI/WSGI 中间件 + 依赖注入         │
│   Go/Gin: gin.HandlerFunc + GORM Callbacks         │
│   Spring: Filter + AOP 切面                        │
│   其他框架：按需扩（企业内部技术栈收敛，不追求大而全）      │
└─────────────────────────────────────────────┘
```

**语言栈范围（企业内部定制）**：三栈为主——**Python=Django**（内部 Python 项目统一样板；FastAPI/Flask 兼容支持，Demo 用 FastAPI 纯属开发快）、**Go=Gin**（后端框架就这一个）、**Java=Spring**——**公司用什么就做什么，不为通用而通用**；新增语言 = 新增一个适配层薄壳 + 过一遍契约测试套件（§3.5）。

### 3.2 业务侧长什么样（Django 示例——注意业务代码零权限逻辑）

```python
# settings.py —— 一次配置
INSTALLED_APPS = [..., "icguard"]
MIDDLEWARE = ["icguard.middleware.IAMGuardMiddleware"]
ICGUARD = {
    "agent": "http://127.0.0.1:9090",
    "fetch_mode": "orm",                      # 取材模式：orm（默认）| agent-query
    "routes": {                               # 路由→动作映射（也可由 OpenAPI 自动生成）
        ("GET",    r"^/api/hosts/(?P<id>\d+)$"): "cmdb:host:read",
        ("PATCH",  r"^/api/hosts/(?P<id>\d+)$"): "cmdb:host:update",
        ("DELETE", r"^/api/hosts/(?P<id>\d+)$"): "cmdb:host:delete",
        ("POST",   r"^/api/hosts$"):            "cmdb:host:create",
    },
    "exempt": [r"^/healthz$", r"^/pip/query/"],   # 豁免清单（PIP 内部通道必须豁免，防递归）
}
```

```python
# 业务代码 —— 一个权限字都没有
def host_detail(request, id):
    host = Host.objects.get(id=id)        # 中间件已判：这个人能不能读这台
    return JsonResponse(host.to_dict())

def host_update(request, id):
    host = Host.objects.get(id=id)
    host.name = request.POST["name"]
    host.save()                            # pre_save 信号已判：能不能改（旧属性+新值）
    return JsonResponse(...)

def host_list(request):
    qs = Host.objects.filter(cloud="aws")  # 中间件自动过滤：只留有权限的行
    return render(qs)
```

**中间件内部（业务看不见的三步）**：

```python
def middleware(request):
    action = match_route(request)                    # 路由→动作
    if not agent.check(action, user=who(request)):   # ① 接口级（内存，µs）
        return 403
    # ② 取判定材料（点操作）：ORM 取行 → 归一化成 {id, attrs}；列表：候选行交给 filter
    rows = fetch_material(request)                   #    取不到 → 报错拒绝（见 §6）
    verdict = agent.check_data(user, action, rows)   # ③ 数据级（内存，µs）
    if not verdict.allow:
        return 403
    return call_view(request)                        # 全过才进业务
# 增删改的钩子同理：pre_save / pre_delete / before_commit 挂同一判定，
# 判不过直接抛异常 → 事务不提交 → 零副作用（顺序铁律：备料→判→执行）
```

**Go/Gin 示例（重点语言）**：

```go
// main.go —— 一次接入
r := gin.New()
r.Use(icguard.Middleware(icguard.Config{
    Agent: "http://127.0.0.1:9090",
    Routes: map[icguard.Route]string{
        {Method: "GET",    Pattern: "/api/hosts/:id"}: "cmdb:host:read",
        {Method: "PATCH",  Pattern: "/api/hosts/:id"}: "cmdb:host:update",
        {Method: "DELETE", Pattern: "/api/hosts/:id"}: "cmdb:host:delete",
        {Method: "POST",   Pattern: "/api/hosts"}:     "cmdb:host:create",
    },
    Exempt: []string{"/healthz"},
}))

// 业务 handler —— 零权限逻辑（判定藏在中间件 + GORM Callback 里）
func updateHost(c *gin.Context) {
    var h Host
    db.First(&h, c.Param("id"))          // 中间件已判：能不能读/改这台（取材顺手）
    h.Name = c.PostForm("name")
    db.Save(&h)                           // GORM Callback 已判：改前判定，判不过事务不提交
    c.JSON(200, h)
}
```

**Java/Spring 示例**：

```java
// 配置一次（icguard 注册 Filter + AOP 切面）
@Configuration
class GuardConfig {
  @Bean IamGuard iamGuard() {
    return IamGuard.builder()
        .agent("http://127.0.0.1:9090")
        .route("GET",    "/api/hosts/{id}", "cmdb:host:read")
        .route("PATCH",  "/api/hosts/{id}", "cmdb:host:update")
        .route("DELETE", "/api/hosts/{id}", "cmdb:host:delete")
        .exempt("/healthz")
        .build();
  }
}

// 业务代码 —— 零权限逻辑（实体在手即判定材料）
@RestController
class HostController {
    @PatchMapping("/api/hosts/{id}")
    public Host update(@PathVariable long id, @RequestBody HostForm form) {
        Host h = repo.findById(id);        // 判定材料：实体在手
        h.setName(form.getName());
        return repo.save(h);               // 切面已判：判不过抛 403，事务回滚，零副作用
    }
}
```

### 3.3 各语言 SDK 差异表（差异只在适配层）

| 语言/框架 | 集成点（挂哪） | 取材方式 | 备注 |
|---|---|---|---|
| Python · Django | Middleware + `pre_save`/`pre_delete` 信号 | ORM 行内取（对象已在手） | **内部样板**，最顺 |
| Python · FastAPI/Flask | ASGI/WSGI 中间件 + 依赖注入 | 请求上下文 + DAO 取行 | 与 Django 共用 core，兼容支持 |
| Go · Gin | `gin.HandlerFunc` 中间件 + GORM Callbacks | GORM 行 | 重点语言 |
| Java · Spring | Filter + AOP 切面 | JPA 实体 | 重点语言 |
| 其他框架 | 按需扩适配层 | 同款 | 技术栈收敛，不追求大而全 |

### 3.4 分发与引入（私有仓库——企业内部标配）

- **内网私有仓库**（企业标配，SDK/镜像都发这里）——常见选型：
  - **多格式制品库**：Nexus Repository（PyPI/npm/Maven/Go 一站）、JFrog Artifactory（企业级标准）、GitLab Package Registry；
  - **Docker 镜像仓**：Harbor（最常见自建）、GitLab Container Registry、阿里云 ACR；
  - **语言级小件**：Verdaccio（npm 私服）、devpi（PyPI 私服）、Athens（Go proxy）；
  - 典型组合：**Harbor（镜像）+ Nexus/Artifactory（语言包）**；
- **引入**：`pip install icguard-django -i https://pypi.internal` / `go get`（goproxy 内网缓存）/ Maven 坐标——与日常拉内部包无异，零额外流程；老项目无源管理走制品库附件 vendor；
- **版本策略**：core 与适配层同仓同版本；跟随中心发行说明的兼容矩阵。

### 3.5 通用性的验收标准（跨语言怎么保证"行为一致"）

**契约测试套件（conformance suite）**：一组固定用例（接口级拒/清单命中/条件命中/改删零副作用/列表过滤/豁免放行/agent 挂 fail-closed），每个语言 SDK 发布前必须全绿——**像 OAuth 生态的一致性测试**，协议对不对不靠嘴，靠跑套件。

---

## 4. 能力包契约要求（发布方视角）

| 义务 | 内容 | 用途 |
|---|---|---|
| **标准查询接口**（数据契约 L1，已有义务） | `GET /hosts/{id}` 带 ID 取单行，返回判定字段（account/owner/env…） | SDK 取材（声明驱动，见 §4.1）的取材来源 |
| **路由→动作映射** | 接口清单（OpenAPI 自动生成动作码） | SDK 的 ①路由匹配 |
| **数据范围声明** | 集合式/条件式/变量式（能力包范围选项） | SDK 的 ③数据级比对 |

### 4.1 发布门禁（声明不合格怎么办——发布方的代价，不是系统的漏洞）

**声明不是填表走形式，是发布门禁的机器校验输入**。"只填增删改接口"的包只有两种命运，**没有第三态**：

| 包的形态 | 命运 |
|---|---|
| 只填增删改、**不勾数据级**（纯动作级包，如"数据管理权限"） | ✅ 合法——SDK 不取材（取材只在数据级判定时发生） |
| 只填增删改、**却声称数据级**（勾了数据范围） | ❌ **发布门禁拒**："数据级包必须声明查询接口（取材来源）"——出场券没有，包发不出来 |

三道机器门（与数据契约"试算自检 + 失败二分"同款机制）：

| 门 | 校验 | 不过 |
|---|---|---|
| ① schema 完整性 | 查询声明 URL/Method/Payload/fields 齐不齐 | 直接拒发 |
| ② **试算自检** | 发布时**按声明真拼一次请求**取材——拿得到吗、格式对吗、字段挑得出吗 | 不可算 → 400 拒 + 出路（降接口级）；不可达 → 502 可重试 |
| ③ 语义档位 | 声称数据级但无查询声明 | 拒发或**降级为接口级包** |

**运行期兜底**（漏网的）：取材失败 = 报错拒绝（fail-closed）——坏声明只弄坏发布方自己的功能，绝不变成权限漏洞；归因走发布方责任制（取材失败率/决策日志可查，通知 owner 修）。

---

## 5. 判定协议（REST 直调——不装 SDK 的兜底，也是 SDK 的底层）

```
POST http://127.0.0.1:9090/v1/check
{"user":"bob","action":"cmdb:host:update","model":"host","instance_id":"host-101",
 "operation":"update","attributes":{"account":"123","owner":"bob"},   ← 判定材料（SDK 取 or Agent 回查）
 "changes":{"name":"new-name"}}                                      ← 新值（改时给）
→ {"decision":"allow"}
→ {"decision":"deny","reason":"no_matching_scope" | "data_missing" | "stale"}

POST http://127.0.0.1:9090/v1/filter
{"user":"bob","action":"cmdb:host:read","model":"host","rows":[{"id":"host-101","attributes":{...}}]}
→ {"allowed_ids":["host-101"],"stale":false}

GET  http://127.0.0.1:9090/v1/manifest      ← 本应用生效的能力包声明（含查询接口）
```

| 错误码 | 含义 | SDK/业务怎么处理 |
|---|---|---|
| `no_matching_scope` | 不在授权范围 | 403 无权 |
| `data_missing` | 缺判定材料且判不了 | fail-closed 拒；自查取材链路 |
| `stale` | 数据陈旧降级标注 | 列表场景带 `stale=true` 交由调用方决定 |
| 5xx / 连接失败 | Agent 不可用 | **fail-closed**（数据判定路径永不 fail-open） |

---

## 6. 取材铁律：SDK 取材，Agent 纯判（不做回查兜底）

**分工一句话：Agent 只算不算数，SDK 只数不算**——判定材料的获取 100% 是 SDK 的职责，Agent 100% 是纯函数式判定器。

1. **Agent 纯判定**：只做内存/CPU 运算（查包、比对、求值），不查数据源、不发外呼、不持有任何数据凭证——职责纯化、故障域最小、部署最轻；
2. **SDK 取材**：走业务原生数据通道取行（ORM/DAO），取不到 → **按语义报错拒绝**（资源不存在=404；取材链路异常=系统错误）——**"取不到"= 接入问题，排查接入方取材链路**，绝不"取不到就放行"（fail-closed）；
3. **免掉两类坑**（这就是不回查的设计收益）：不存在"Agent 回查触发 SDK 判定"的递归豁免问题，也不存在"Agent 持有数据源凭证"的权限扩散问题。

---

## 7. 验收自测清单（上线前 5 条）

1. 接口级：无权限用户调接口 → 403，且业务视图未执行（看日志/计数）；
2. 数据级·点：对范围外资源改/删 → 403，**库里零变化**（零副作用验证）；
3. 数据级·列表：列表只返回范围内行；
4. 取材失败语义：SDK 取不到判定材料 → 报错拒绝（fail-closed），不静默放行（"取不到=接入问题"可查可定位）；
5. 故障：停掉 Agent → 请求 fail-closed 拒绝（不是放行），恢复后自动恢复。

---

## 8. 责任边界（把丑话说在前面）

- **强制执行无法完全中心化**（数据面在各业务手里），防线分三层：**统一 SDK 收口**（判定只写在一处）+ **决策日志审计**（每次判定留痕，异常模式可查）+ **定期审阅**（owner 复核谁在用什么权限）；
- 绕过 SDK 直连数据层 = 接入方主要责任，且会在决策日志与定期审阅中暴露异常（有判定无日志 = 一眼可见）；
- 重手段备用：数据层强制（数据库行级安全，SQL 自动注入过滤条件）——内部可要求接入，按需启用。

---

## 附：术语速查

SDK（软件开发工具包，本文指接入中间件包）· Agent（旁挂判定器）· M2M（程序对程序）·
bundle（策略包）· TTL（生存时间）· fail-closed（失败关闭，判不了就拒）· fail-open（失败放行，数据判定路径禁止）·
PIP（策略信息点，判定材料供给方——agent-query 模式即 PIP 形态）· 零副作用（判不过则业务动作完全不发生）
