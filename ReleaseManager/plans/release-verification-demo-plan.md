# 发布自动验证 + 面试演示 实施计划

> 状态：待执行
> 日期：2026-08-02
> 目标：发布成功后自动执行一套「验证 + 演示」流程，结构化结果展示在发布详情页底部，减少面试场景手动操作
> 架构决策：**项目自带声明式验证脚本（verify.yaml）+ executor 统一执行引擎（Python）**，沿用现有 `deployment.yaml` 模式

---

## 1. 背景与目标

面试场景下，发布完成后需要人工查看 Pod、访问域名验证、逐步演示，耗时且依赖操作熟练度。目标：

1. 发布成功后**自动**执行一套验证/演示流程（也可在详情页手动重新运行）
2. 每个检查项产出**结构化结果**（名称、✅/❌、实际证据、耗时）
3. 结果**持久化**并展示在发布详情页底部新板块，面试官 10 秒扫完
4. **策略感知**：rolling / blue_green / canary 的验证点不同（滚动验主入口、蓝绿验 selector 切换、灰度验 canary 独立入口）

## 2. 架构总览（三层）

```
项目脚本（声明式）        执行引擎（Python）         存储 + 展示
┌──────────────────┐   ┌──────────────────┐   ┌─────────────────────┐
│ verify.yaml      │→  │ executor         │→  │ backend             │
│ (每应用×环境)     │   │ op=verify        │   │ ReleaseVerification │
│ 描述验什么/期望值  │   │ 读取+过滤+执行    │   │ 模型 + API          │
└──────────────────┘   │ kubectl/curl 跑  │   │ 前端详情页板块        │
                       │ 产出结构化JSON    │   └─────────────────────┘
                       └──────────────────┘
```

- **项目脚本**：`demo-apps/config/{app}/{env}/verify.yaml`，只声明"用哪些检查原语、验什么、期望值"，零代码
- **执行引擎**：executor 新增 `op=verify`（Python），内置通用检查原语（k8s 状态 / HTTP / JSON 断言 / Service selector），执行并收集结果
- **存储与展示**：backend 新增 `ReleaseVerification` 模型 + API；前端发布详情页底部加「🔍 发布验证」板块

---

## 3. 详细设计

### 3.1 verify.yaml 格式（项目脚本）

位置：`demo-apps/config/{app}/{env}/verify.yaml`（与 `deployment.yaml` 同级，按应用×环境隔离）

```yaml
# demo-apps/config/python-app/dev/verify.yaml
checks:
  - name: 部署状态
    type: k8s_deploy_ready        # 内置检查原语
    # 应用/环境/namespace 自动从上下文注入，无需填写

  - name: 健康检查
    type: http
    path: /health
    expect_contains: '"status":"ok"'

  - name: 版本验证
    type: http_json
    path: /
    jsonpath: version
    expect_equal: "{version}"     # 模板变量：发布单版本，引擎注入

  - name: 蓝绿流量切换
    type: k8s_service_selector
    strategy: blue_green          # 仅 blue_green 发布时执行
    expect_track: blue

  - name: 灰度独立入口
    type: http_json
    strategy: canary              # 仅 canary 发布时执行
    service: "{app}-canary"       # 模板变量：金丝雀独立 Service
    path: /
    jsonpath: version
    expect_equal: "{version}"
```

**模板变量**（引擎注入）：`{app}`（应用 code）、`{version}`（发布单版本）、`{env}`（环境 code）、`{ns}`（集群 namespace）

**策略过滤**：`strategy` 字段可省略（所有发布都跑）或指定 `rolling` / `blue_green` / `canary`（仅该策略发布时执行）

### 3.2 内置检查原语（executor 引擎只写一次）

| type | 做什么 | 判定 |
|------|--------|------|
| `k8s_deploy_ready` | `kubectl get deploy {app} -n {ns}` 检查 READY 数 | ready == 期望副本（或 >=1） |
| `k8s_service_selector` | `kubectl get svc {app} -n {ns}` 读 selector | selector 含 `expect_track` |
| `http` | curl `{base}/{path}` | 状态码 2xx + body 含 `expect_contains` |
| `http_json` | curl 后 JSON 解析，取 `jsonpath`（点路径如 `version`） | 取值 == `expect_equal`（支持模板变量） |
| `k8s_pods` | `kubectl get pods -l app={app}` 摘要 | 全部 Running/Ready |

> 每个检查项输出 `{name, status: pass|fail, evidence, duration_ms}`。`evidence` 是实际输出（如 `{"version":"2.0.1"}`、`python-app 2/2 Ready`、`selector: {"app":"python-app","track":"blue"}`）。

### 3.3 executor `_do_verify`（runner.py）

新增 `op=verify`，注册进 `handlers`。逻辑：

1. **读取脚本**：`demo-apps/config/{app}/{env}/verify.yaml`（无该文件 → 返回"无验证脚本"状态，不失败）
2. **模板注入 + 策略过滤**：替换 `{app}/{version}/{env}/{ns}`；按发布 `deploy_strategy` 过滤 `strategy` 字段
3. **确定服务访问地址**（实施时先验证 executor 容器内可达性，候选按序）：
   - 方式 A：`curl http://{app}.{ns}.svc.cluster.local{path}`（OrbStack DNS 若在容器内生效）
   - 方式 B：`kubectl get svc {app} -n {ns} -o jsonpath={.spec.clusterIP}` 拿 ClusterIP → `curl http://{ip}:{port}{path}`
   - 方式 C（兜底）：`kubectl exec` 进 pod `curl localhost`（一定能通，最慢）
   - 推荐 B（不依赖 DNS）；实施第一步先实测 A/B 哪个可用
4. **逐项执行**：按 `type` 分发到原语函数（subprocess kubectl / requests curl），记录每项耗时与 evidence
5. **汇总**：`ex.finish("success", {checks: [...]})`，整体 status = 全 pass ? success : failed

> executor 已有 `kubectl`、`requests`、`yaml`、`_cluster_ns` 能力，直接复用。

### 3.4 后端

**新模型** `backend/apps/releases/models.py`：

```python
class ReleaseVerification(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="verifications")
    status = models.CharField(max_length=16, default='running')  # running/success/failed/skipped
    results = models.JSONField(default=list)   # [{name,status,evidence,duration_ms}, ...]
    summary = models.TextField(blank=True)     # 简短文案（如 "5/5 通过，耗时 8.4s"）
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "release_verification"
        ordering = ["-created_at"]
```

**API**（`backend/apps/releases/views.py` + urls.py）：

- `GET /releases/{id}/verifications/`：该发布单的验证记录列表（含 results）
- `POST /releases/{id}/verify/`：手动触发验证（创建 ReleaseVerification(running) → 提交 executor `op=verify`（params 带 release/app/env/strategy/version）→ 后台线程 `_watch_verification` 等 executor 完成 → 回写 status/results/summary）
- 返回新记录 id，前端轮询其状态

**自动触发**（在 `_watch_execution` 的 CD 成功分支，或 `execute_release` CD 触发后）：
- CD `task.status == 'success'` 且 `release.status == 'completed'` 时，自动调用验证流程（复用 POST /verify/ 的内部逻辑，不重复建 API 请求）
- 用 `threading.Thread` 异步，不阻塞发布主流程
- 注意：仅对 `release_mode == 'regular'` 的发布（蓝绿/灰度/滚动）自动验证；运维类（restart/stop/scale/traffic）不触发

**验证 executor 连接**：executor_client 现有签名逻辑复用（`submit('verify', params)`）。

### 3.5 前端（发布详情页 `frontend/src/pages/releases/detail.tsx`）

在「CD 部署面板」之后新增板块：

```
🔍 发布验证  [运行验证] [刷新]
┌─────────────────────────────────────────────┐
│ ✅ 部署状态     python-app 2/2 Ready     12ms │
│ ✅ 健康检查     HTTP 200, "status":"ok"  8ms  │
│ ✅ 版本验证     version=2.0.1 (期望 2.0.1)  15ms │
│ ✅ 蓝绿流量切换  selector → track:blue     5ms  │
│ 总耗时 8.4s · 5/5 通过                        │
└─────────────────────────────────────────────┘
```

- 每次验证记录一张卡片（最新在前），含时间戳 + 摘要
- 每项：✅/❌ Tag + name + evidence（等宽小字）+ duration
- 「运行验证」按钮：调 `releaseApi.verify(id)`，轮询 `verifications` 直到 running 结束
- 运行中：Spin + 实时进度（轮询 2s）
- 空态：无验证记录时显示"发布成功后自动验证 / 可手动运行"
- API 封装：`frontend/src/api/index.ts` 加 `verifications: (id) => client.get(...)`、`verify: (id) => client.post(...)`

---

## 4. 分阶段实施

| 阶段 | 内容 | 涉及 | 验收 |
|------|------|------|------|
| **V1 执行引擎** | executor 新增 `op=verify` + 原语函数（k8s_deploy_ready / k8s_service_selector / http / http_json）+ 读取 verify.yaml + 模板注入 + 策略过滤；先实测 executor 容器访问 svc 的方式（A/B/C） | `executor/app/runner.py`、`executor/app/k8s.py`(如需)、重建容器 | 直接调 executor `op=verify` 返回结构化 checks |
| **V2 项目脚本** | 为 python-app/go-app/node-app 的 dev 环境写 verify.yaml（含 rolling/blue_green/canary 三策略检查项） | `demo-apps/config/*/dev/verify.yaml` | 各策略下验证结果正确（蓝绿查 selector、灰度查 canary 入口） |
| **V3 后端存储 + API** | `ReleaseVerification` 模型 + migration；`GET/POST verifications` API；`_watch_verification` 回写；CD 成功后自动触发 | `models.py`、`views.py`、`urls.py`、migration | 发布完成自动生成验证记录；手动 POST 可重跑 |
| **V4 前端板块** | detail.tsx 底部加验证板块（卡片列表 + 运行按钮 + 轮询 + 空态）；api 封装 | `detail.tsx`、`api/index.ts`、重建前端 | 发布详情页展示验证结果，可手动运行 |
| **V5 打磨** | 失败项红色高亮、summary 文案、知识库补充「自动验证」说明 | 前端、知识库 | 面试演示体验完整 |

## 5. 风险与注意点

1. **executor 容器访问服务地址**：首要验证点。容器在 docker local-net，集群 ClusterIP/svc.cluster.local 可达性未知。实施 V1 第一步先实测（方式 A/B），不可用则落 C（kubectl exec curl）。这决定 http 原语的实现方式。
2. **蓝绿/灰度验证时机**：验证在发布 CD 成功后立即跑，此时 blue/canary 环境刚就绪，selector 已切，正是验证"发布效果"的最佳时机。若验证前环境被清理，会失败——属预期（提示"环境已不存在"）。
3. **自动触发的并发**：CD 成功自动触发验证用独立线程；同一发布单重复触发（手动+自动）用 `created_at` 最新一条为准，不做并发锁（demo 可接受）。
4. **verify.yaml 缺失**：应用没有验证脚本时，自动触发记录 `status=skipped`（不报错、不打扰），详情页显示"该项目未配置验证脚本"。
5. **`k8s_service_selector` 的 namespace**：用 `_cluster_ns()` 解析（DB namespace 名是模拟名，勿直接使用）。
6. **http_json 的 jsonpath**：仅支持简单点路径（`version`、`data.version`），不做复杂 JSONPath，够用即可。
7. **权限**：验证 API 走现有发布权限模型（能看发布单的人能看/触发验证）。

## 6. 验收标准

- [ ] executor `op=verify` 返回结构化 checks（每项 name/status/evidence/duration_ms）
- [ ] rolling 发布：主入口版本验证通过、selector 为 stable
- [ ] blue_green 发布：`k8s_service_selector` 验证 selector 切到 blue + 主入口新版本
- [ ] canary 发布：主入口旧版本 + `{app}-canary` 独立入口新版本（两条检查）
- [ ] 发布 CD 成功后自动生成验证记录（详情页可见）
- [ ] 详情页「运行验证」按钮可手动重跑，运行中有进度
- [ ] 无 verify.yaml 的应用显示"未配置验证脚本"（skipped）
- [ ] 失败项红显 + 证据可读（面试演示体验）
