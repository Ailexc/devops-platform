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
请求 ──▶ [SDK 中间件（业务后端入口，一次接入全接口覆盖）]
           │ ① 接口级：查本地 Agent 的策略包（内存比对，µs 级）
           │ ② 取判定材料：SDK 走你原生数据通道取那一行（默认）
           │               或 Agent 按能力包声明的查询接口回查（兜底）
           │ ③ 数据级：清单/条件/变量比对（内存，µs 级）
           ▼
         全过 → 执行业务逻辑（此刻才落库）；任一不过 → 拒，零副作用

Agent（旁挂容器，随业务部署）：轮询拉 bundle ──策略+范围声明+查询接口声明──▶ 权限中心（低 QPS）
```

**核心设计一句话**：逻辑前置（判定在请求最前面）、物理旁挂（Agent 是独立容器）、取材走原生（数据查询用你自己的数据通道，不透传、不过权限中心）。

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
- 网关场景同款：网关的 forwardAuth 回调也可以指向本地 Agent（与部署在网关旁的 agent 完全同构）。

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
| `FETCH_MODE` | 默认 `sdk` | 取材模式：`sdk`（SDK 取行）/ `agent-query`（Agent 按契约回查） |
| `QUERY_SECRET` | agent-query 时 | Agent 回查业务查询接口用的 M2M（程序对程序）凭证，最小只读权限 |

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
│   Django: Middleware + pre_save/pre_delete 信号     │
│   FastAPI/Flask: ASGI/WSGI 中间件 + 依赖注入         │
│   Go/Gin: gin.HandlerFunc + GORM Callbacks         │
│   Spring: Filter + AOP 切面                        │
│   Express: middleware + ORM hook                   │
└─────────────────────────────────────────────┘
```

**为什么 Python 系全能接**：Django/Flask/FastAPI 共用同一个 core（判定逻辑一模一样），只换"把判定挂在哪"（中间件/信号/依赖注入）——**框架差异只存在于适配层那一百行**，Go/Java 同理。

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
    rows = fetch_material(request)                   #    fetch_mode=agent-query 时由 Agent 回查
    verdict = agent.check_data(user, action, rows)   # ③ 数据级（内存，µs）
    if not verdict.allow:
        return 403
    return call_view(request)                        # 全过才进业务
# 增删改的钩子同理：pre_save / pre_delete / before_commit 挂同一判定，
# 判不过直接抛异常 → 事务不提交 → 零副作用（顺序铁律：备料→判→执行）
```

### 3.3 各语言 SDK 差异表（差异只在适配层）

| 语言/框架 | 集成点（挂哪） | 取材方式 | 备注 |
|---|---|---|---|
| Python · Django | Middleware + `pre_save`/`pre_delete` 信号 | ORM 行内取（对象已在手） | **样板实现**，最顺 |
| Python · FastAPI/Flask | ASGI/WSGI 中间件 + 依赖注入 | 请求上下文 + DAO 取行 | 与 Django 共用 core |
| Go · Gin | `gin.HandlerFunc` 中间件 + GORM Callbacks | GORM 行 | 语言无关协议直接调 |
| Java · Spring | Filter + AOP 切面（`@WithPermission` 风格） | JPA 实体 | |
| Node · Express | express middleware + ORM hook | ORM 行 | |

### 3.4 分发与引入（下载从哪来）

- **内网私有源**（企业标准做法）：PyPI（`pip install icguard-django -i https://pypi.internal`）/ npm（`@org/icguard-gin`）/ Maven / Go module（goproxy 内网缓存）——我们环境已有 npm 与 goproxy 本地缓存基建，直接挂；
- 备选：制品库附件下载 + 手动 vendor（老项目无源管理时）；
- **版本策略**：core 与适配层同仓同版本；跟随中心发行说明的兼容矩阵。

### 3.5 通用性的验收标准（跨语言怎么保证"行为一致"）

**契约测试套件（conformance suite）**：一组固定用例（接口级拒/清单命中/条件命中/改删零副作用/列表过滤/豁免放行/agent 挂 fail-closed），每个语言 SDK 发布前必须全绿——**像 OAuth 生态的一致性测试**，协议对不对不靠嘴，靠跑套件。

---

## 4. 能力包契约要求（发布方视角）

| 义务 | 内容 | 用途 |
|---|---|---|
| **标准查询接口**（数据契约 L1，已有义务） | `GET /hosts/{id}` 带 ID 取单行，返回判定字段（account/owner/env…） | `agent-query` 模式取判定材料 |
| **路由→动作映射** | 接口清单（OpenAPI 自动生成动作码） | SDK 的 ①路由匹配 |
| **数据范围声明** | 集合式/条件式/变量式（能力包范围选项） | SDK 的 ③数据级比对 |

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

## 6. Agent 回查模式（agent-query）与防递归

适用：数据层不便挂钩（老旧存储、异构数据源）。流程：SDK 只发 `{ID, changes}` → Agent 按 §4 声明的查询接口点查那行 → 比对判定。

**三条纪律**：
1. **豁免防递归**：查询路由（如 `/pip/query/`）必须登记进 SDK 豁免清单——否则 Agent 回查又触发判定 = 无限递归；
2. **凭证最小化**：`QUERY_SECRET` 只读、只按 ID、只限声明数据域；
3. **优先 SDK 取**（默认模式）：进程内取行零网络成本；agent-query 是不便挂钩时的兜底，不是默认。

---

## 7. 验收自测清单（上线前 5 条）

1. 接口级：无权限用户调接口 → 403，且业务视图未执行（看日志/计数）；
2. 数据级·点：对范围外资源改/删 → 403，**库里零变化**（零副作用验证）；
3. 数据级·列表：列表只返回范围内行；
4. 豁免：healthz/PIP 查询路由正常放行、无递归（agent-query 模式必测）；
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
