# 应用详情页右侧操作栏重构 + 运维操作统一为发布单 改造方案

> 状态：待评审
> 日期：2026-08-02
> 范围：前端 `frontend/src/pages/releases/app-detail.tsx`、`frontend/src/components/ScaleDrawer.tsx`、`frontend/src/pages/releases/create.tsx`；后端 `backend/apps/releases/`、`backend/apps/infrastructures/views.py`、`backend/apps/applications/urls.py`；执行端 `executor/app/runner.py`、`executor/app/k8s.py`；配置 `demo-apps/config/*/{env}/deployment.yaml`、`demo-apps/*/Dockerfile`；知识库 `backend/knowledge/docs/releases/articles/deploy-strategies.html`

---

## 1. 背景与目标

当前应用详情页右侧操作栏存在三类问题：

1. **概念错位**：蓝绿部署、灰度发布本质是部署**策略**（发布单的属性），却被当作独立**操作按钮**放在操作栏，点击后只是"预填策略跳转新建发布页"，语义冗余。
2. **分类维度不清晰**：现有分组按"真实能力 / 扩展能力"（是否 Spug 原生）划分，对用户使用没有指导意义。
3. **运维操作未统一留痕**：重启/停机/启动目前是**纯前端模拟**（`Modal.confirm` + `message.success`，不调后端），不产生发布单、不进审计。而实例伸缩（`scale_application`）已经走了"操作即发布单"的模式，两者不统一。

### 目标

1. 蓝绿/灰度从操作栏**移除**，由新建发布页的 `deploy_strategy` 选择承载（该能力已存在，仅需微调）。
2. 操作栏重组为两组：**创建发布**（产生"发新版本"类发布单）+ **运行管理**（产生"运维操作"类发布单）。
3. 所有运维操作（重启/停机/启动/伸缩/流量管理）统一**创建发布单**，走通用流程（审批判定、发布历史、审计、任务日志），逻辑与 `scale` 对齐。
4. 部署目标（`Environment.deploy_type`: k8s / ec2）在**环境选择器**中标注，不适用当前环境的操作**禁用 + tooltip 说明**（不隐藏）。
5. 蓝绿/灰度/流量管理从"日志模拟"升级为**真实执行**（蓝绿=真实建双环境并切换 Service selector；灰度=真实创建 canary 环境并验证；流量=真实摘/挂流），与新发布页的 `deploy_strategy` 打通。
6. 新建发布页选择蓝绿/灰度策略时提供**知识库文档跳转**，文档涵盖三块：**本 Demo 实现 / 真实环境实现 / EC2 实现**。

---

## 2. 设计共识（决策记录）

| # | 决策 | 理由 |
|---|------|------|
| D1 | 蓝绿/灰度不放在操作栏，作为新建发布的 `deploy_strategy` 选项 | 策略是发布单属性而非独立动作；创建页已有该下拉 |
| D2 | 操作栏分「创建发布」/「运行管理」两组 | 分类维度从"真实/扩展"改为"走流程 vs 运维"，更符合心智模型 |
| D3 | 所有运维操作统一创建发布单，走通用流程（不做特设免审批逻辑） | 统一留痕/审计/状态机；`scale_application` 已确立此范式，直接推广 |
| D4 | 部署目标不加新字段，复用 `Environment.deploy_type`（已有）；UI 上在环境选择器标注 K8s/EC2，不适用操作禁用而非隐藏 | 一个应用可有多个环境且类型不同；信息应出现在环境维度，而非按钮维度 |
| D5 | 重启/停机/启动/伸缩合并为「状态管理」单入口 | 三者都是运行时状态变更，减少按钮噪音 |
| D6 | 蓝绿/灰度/流量管理的真实执行**纳入本次改造**：蓝绿=真实建双环境+切 Service selector；灰度=真实建 canary+就绪验证+手动全量；流量=真实摘/挂流。灰度"真实权重路由"因 **OrbStack K8s 集群无 ingress controller**，标注为可选项（P5） | 演示价值高；蓝绿/流量改造量可控，灰度权重需集群内 ingress 组件故单列 |
| D7 | 红黑部署、影子部署列为**低成本可选项**（复用蓝绿/灰度已有能力），随 P5 一并评估；A/B 测试、真实权重分阶段因需 ingress/网关，不纳入 | 成本极低、丰富发布策略体系；高成本项收益有限 |

---

## 3. 现状盘点

### 3.1 数据模型（后端）

- `backend/apps/releases/models.py` — `Release`：
  - `release_mode` 已有枚举：`regular / incremental / compensation / quick / rollback / scale`
  - 已有伸缩专用字段：`current_replicas`、`target_replicas`（`release_mode='scale'` 时使用）
  - 已有 `deploy_strategy`（`rolling / blue_green / canary`）、`deploy_mode`（`k8s / ec2`，继承自应用）
- `backend/apps/infrastructures/models.py` — `Environment.deploy_type`（`k8s / ec2`）已存在。

### 3.2 后端 API（已有范式）

- `backend/apps/infrastructures/views.py` — `scale_application`（`POST /api/v1/apps/{id}/scale/`）：
  - **已经是"操作即发布单"的完整范式**：校验 → 审批判定（`ReleaseApprovalConfig.requires_approval`）→ 需要审批则建 `Approval` 单 / 否则创建 `Release`（`release_mode='scale'`）→ 提交 executor `scale` op
  - 已按 `deploy_type` 分发到 executor（`params['deploy_type']`）

### 3.3 执行端（executor）

- **部署环境**：executor 的 kubeconfig `current-context: orbstack`（server `host.docker.internal:26443`），实际部署在 **OrbStack K8s 集群**（节点名 `orbstack`，v1.34.8+orb1）；`k8s/` 目录下的 kind-config 为遗留配置，未实际使用。
- **集群网络**：demo 应用（python-app/go-app）在 `release-demo` namespace，Service 为 ClusterIP；**集群内无 ingress controller**。
- **宿主机网关**：`traefik-gateway` 为 Docker Provider 模式（`unix:///var/run/docker.sock` + `network: local-net`），通过容器 labels 路由 local-net 内的 docker 容器（release 前端/后端、cmdb、task、homepage 等），**不感知 K8s Service**，demo 应用 pod 不在 local-net 内。
- `executor/app/runner.py`：
  - `_do_scale` — **已支持 deploy_type 分发**：k8s 真实 `kubectl scale` / ec2 模拟日志
  - `_do_restart` — 已真实（调 `k8s.restart` → patch Deployment 注解触发 rollout restart）
  - `_do_canary` / `_do_blue_green` — 纯日志模拟
  - **无 traffic op**
- `executor/app/k8s.py`：`scale()`、`restart()` 真实执行；`canary_update()`、`blue_green_switch()` 模拟

### 3.4 前端

- `frontend/src/pages/releases/app-detail.tsx` 右侧操作栏：
  - 「真实能力」组：常规发布、增量发布、补偿发布、回滚、克隆、**重启**
  - 「扩展能力」组：**蓝绿部署、灰度发布、流量管理（纯说明弹窗）、停机、启动、实例伸缩**
  - `handleRestart` / `handleStop` / `handleStart`：**纯前端模拟**（不调后端）
  - `handleRollback` / 克隆等：跳转新建发布页并预填参数
  - 发布历史 `typeOptions` 含 `scale: 实例伸缩`
- `frontend/src/components/ScaleDrawer.tsx`：实例伸缩抽屉
  - **环境选择器已带部署类型 Tag（K8s/EC2）**，并按 deploy_type 显示不同文案
  - 已调用 `appApi.scale`（`POST /apps/{id}/scale/`）
  - 是「状态管理」入口的天然模板
- `frontend/src/pages/releases/create.tsx`：已有 `deploy_strategy` 下拉（rolling/blue_green/canary），支持 URL 参数预选应用/模式

---

## 4. 目标形态

```
应用详情页右侧操作栏
├── 创建发布
│   ├── 常规发布
│   ├── 增量发布
│   ├── 补偿发布
│   ├── 回滚
│   └── 克隆
│       （蓝绿 / 灰度 → 在"新建发布"页通过 deploy_strategy 选择）
└── 运行管理
    ├── 状态管理        （重启 / 停机 / 启动 / 实例伸缩 → Drawer 内选环境 + 动作）
    └── 流量管理        （摘流 / 挂流 → Drawer 内选环境）
```

原则：

- **所有按钮点击后都产生一条发布单**（`release_mode` 区分类型），统一进发布历史、审计、任务日志。
- **环境选择器**（Drawer 内）标注每个环境的部署类型（`dev · K8s` / `prod · EC2`），沿用 `ScaleDrawer` 现有样式。
- 当前环境不适用的动作：**禁用 + tooltip**（如 EC2 环境的"实例伸缩"），不隐藏。

---

## 5. 详细改造方案

### 5.1 数据模型（`backend/apps/releases/models.py`）

`Release.release_mode` 枚举新增 4 个值：

```python
release_mode = models.CharField(max_length=16, default='regular', verbose_name="发布方式",
    choices=[
        ('regular', '常规发布'),
        ('incremental', '增量发布'),
        ('compensation', '补偿发布'),
        ('quick', '快速发布'),
        ('rollback', '回滚发布'),
        ('scale', '实例伸缩'),
        ('restart', '重启'),
        ('stop', '停机'),
        ('start', '启动'),
        ('traffic', '流量管理'),
    ],
    ...)
```

- `restart` / `stop` / `start` 复用现有 `current_replicas` / `target_replicas` 语义（`stop` = target 0，`start` = target 环境配置副本数）。
- `traffic` 新增字段 `traffic_action`（`take_out` 摘流 / `restore` 挂流）：

```python
traffic_action = models.CharField(max_length=16, blank=True, default='',
    verbose_name="流量操作",
    choices=[('take_out', '摘流'), ('restore', '挂流')],
    help_text="release_mode='traffic' 时使用")
```

> 说明：`Environment.deploy_type` 已存在，**不加新字段**（决策 D4）。

需要新增/修改 migration（`makemigrations releases`）。

### 5.2 后端 API

#### 5.2.1 泛化统一操作入口（推荐）

新增 `POST /api/v1/apps/{id}/operations/`（`backend/apps/infrastructures/views.py`），统一承载运维操作，内部按 `action` 分发：

```json
// 请求体
{
  "env_code": "dev",
  "action": "restart | stop | start | scale | traffic",
  "target_replicas": 5,          // scale 时必填
  "traffic_action": "take_out",  // traffic 时必填（take_out / restore）
  "reason": "可选说明"
}
```

逻辑（以 `scale_application` 为模板，抽公共函数）：

1. 校验：环境存在、应用在该环境有 `AppEnvConfig`、action 参数合法
2. `action` → `release_mode`、executor `op`、`params` 映射：

   | action | release_mode | executor op | 关键参数 |
   |--------|--------------|-------------|----------|
   | restart | `restart` | `restart` | `name, namespace, deploy_type` |
   | stop | `stop` | `scale` | `replicas=0` |
   | start | `start` | `scale` | `replicas=env_config.replicas` |
   | scale | `scale` | `scale` | `replicas=target_replicas`（校验 ≤ 配置上限） |
   | traffic | `traffic` | `traffic` | `traffic_action` |

3. 审批判定：复用现有 `ReleaseApprovalConfig.requires_approval` 逻辑（需要审批 → 建 `Approval` 单；否则 → 建 `Release` + 提交 executor），与 `scale_application` 一致
4. 创建 `Release`：`title` 按 action 生成（如 `重启: {app} ({env})`）、`release_mode` 对应、`deploy_mode=env.deploy_type`、`status='completed'`、`approval_status='not_needed'`、`need_approval=False`（走通用流程，不特设逻辑）
5. 提交 executor，返回发布单信息

> `scale_application` 保留（前端 `appApi.scale` 兼容），内部改为调用公共函数，避免重复。

#### 5.2.2 URL 注册

`backend/apps/applications/urls.py` 增加：

```python
path('apps/<int:app_id>/operations/', infra_views.application_operations, name='app-operations'),
```

### 5.3 执行端（executor）

#### 5.3.0 网络拓扑与流量控制边界（重要前提）

- **发布目标**：OrbStack K8s 集群（非 kind）。
- **流量控制分两层，明确边界**：
  - **Service 层**（本次核心）：蓝绿切换、摘/挂流，全部基于 Service selector 完成，**不需要任何 ingress / traefik**。
  - **Ingress 层**（仅灰度权重放量可选）：需要**集群内** ingress controller（集群内 traefik 或 ingress-nginx，只服务 `release-demo`），与宿主机 `traefik-gateway` 分离。
- **宿主机 `traefik-gateway` 不适合做本方案的路由控制**：它是 Docker Provider，只感知 docker 容器、不感知 K8s Service；且为全项目公共网关（homepage/cmdb/task/release 前端共用），不宜污染。
- **demo 应用对外入口（已实测可用）**：OrbStack 网络层支持从宿主机直接访问集群内 Service 的 DNS 域名 `<service>.<namespace>.svc.cluster.local`（实测 `http://go-app.release-demo.svc.cluster.local/health` 返回 HTTP 200）。因此：
  - 浏览器/宿主机 curl 可直接访问 demo 应用，**不需要 NodePort、不需要 ingress**；
  - 该域名走 Service 层（ClusterIP + selector），与 5.3.1 的 selector 方案完全咬合——蓝绿切换、摘/挂流效果可直接在浏览器/curl 验证；
  - 局限：仅 round-robin 到单个 Service 的 endpoints，**不支持权重**（灰度按比例放量仍需集群内 ingress，见 5.3.4）。

#### 5.3.1 label 约定（蓝绿/流量共同依赖）

当前 `demo-apps/config/*/{env}/deployment.yaml` 中 Service selector 为 `app: xxx`。为支持蓝绿切换与摘/挂流，约定：

- Service selector 升级为 **`app: xxx, track: <active>`**（`active` 指向当前承载流量的环境：`blue` / `green` / `stable`）。
- 蓝绿：`{app}-blue`（新版本）、`{app}-green`（旧版本）两个 Deployment 分别打 `track: blue` / `track: green`。
- 流量摘流：临时将 Service selector 改为 `app: xxx, track: <nonexistent>`（指向不存在的组合）→ 无 Endpoint，流量断开；挂流恢复 `track: <active>`。
- 灰度：`{app}-canary` Deployment 打 `track: canary`，并创建独立 Service `{app}-canary`（selector `app: xxx, track: canary`）作为金丝雀独立入口（见 5.3.4）。
- 需同步更新 `demo-apps/config/*/{env}/deployment.yaml` 基线（Service selector 加 track 维度），并重放一次。

#### 5.3.2 运维操作 op

- `_do_restart`：已真实，无需改（补 `deploy_type` 分发：k8s 走 `k8s.restart`，ec2 走模拟日志，参照 `_do_scale` 的写法）。
- `stop` / `start`：复用 `_do_scale`（传 `replicas=0` 或环境副本数），无需新增。
- 新增 `_do_traffic(ex, p)`（`runner.py` handlers 注册 `"traffic"`）：
  - **k8s 模式**：真实 patch Service selector（见 5.3.1 label 约定）。需要 `k8s.py` 新增 `patch_service_selector(namespace, service, selector)`（kubernetes API：`CoreV1Api.patch_namespaced_service`）
  - **ec2 模式**：模拟日志（对应 ALB Target Group deregister / register），参照 `_do_scale` 的 ec2 分支

#### 5.3.3 蓝绿真实执行（`_do_blue_green` 改造）

将 `_do_blue_green` 从日志模拟改为真实执行：

1. 基于主 Deployment 的 YAML 生成 `{app}-blue` Deployment（新镜像，`track: blue`，replicas 与主一致），`kubectl apply` 或 `k8s.create_or_update_deployment`
2. `_wait_rollout` 等待就绪
3. `patch_service_selector` 将 Service 切到 `track: blue`
4. 旧 `{app}-green` 保留（回滚窗口），日志注明"保留旧环境用于回滚"

#### 5.3.4 灰度真实执行（`_do_canary` 改造）

将 `_do_canary` 从日志模拟改为真实执行（本次做到"真实 canary 部署 + 就绪验证 + 手动全量"）：

1. 创建 `{app}-canary` Deployment（新镜像，`track: canary`，1 副本），apply 并等就绪
2. 创建独立 Service `{app}-canary`（selector `app: xxx, track: canary`），作为金丝雀独立入口
3. 日志展示"canary 就绪，等待人工确认全量"
4. 全量：`kubectl set image` 主 Deployment 到新版本（或提升 canary 为 stable），随后清理 canary Deployment 与 `{app}-canary` Service

**演示玩法（配合 5.3.0 的 svc.cluster.local 域名）**：

- 主入口 `{app}.release-demo.svc.cluster.local` → 旧版本（100% 稳定流量）
- 灰度入口 `{app}-canary.release-demo.svc.cluster.local` → 新版本（金丝雀，真实可访问、可验证）
- 观众实际访问新版本验证 → 点"确认全量" → 主入口切换为新版本 → 清理金丝雀

> 这样既保留"先验证再全量"的灰度流程教学价值，又有可操作的演示点（观众能真实访问到新版本），成本仅为多创建一个 `{app}-canary` Service。

> **真实权重路由（按比例放量）为可选项**：OrbStack K8s 集群当前无 ingress controller，无法用 `canary-weight` 类注解实现按比例放量。若要做，需在**集群内**部署 ingress controller（集群内 traefik 或 ingress-nginx，仅服务 `release-demo`），改造量明显增大，列为 P5 子任务（见 7 风险 6）。**不要使用宿主机 `traefik-gateway`**（Docker Provider 模式，不感知 K8s Service，见 5.3.0）。

#### 5.3.5 多版本模拟（方案 A：镜像 tag + APP_VERSION）

demo-app 无真实 git 仓库/分支，多版本通过**镜像 tag + 运行时版本标识**模拟（demo-app 响应已带 `version` 字段，见 `demo-apps/python-app/main.py` / `demo-apps/go-app/main.go`）：

1. 每个 demo-app 的 Dockerfile 加两行（ARG + ENV）：
   ```dockerfile
   ARG APP_VERSION=1.0.0
   ENV APP_VERSION=$APP_VERSION
   ```
2. `_do_build` 的 docker build 命令加 `--build-arg APP_VERSION={version}`：
   ```python
   ["docker", "build", "--build-arg", f"APP_VERSION={version}", "-t", image, app_dir]
   ```

效果：
- 发布 v2.0.0 → 真实构建 `{app}:2.0.0`（镜像内 APP_VERSION=2.0.0）
- 蓝绿/灰度部署新版本环境 → 响应 `"version":"2.0.0"`
- 演示时刷新主域名 / canary 入口 → 直观看到 v1/v2 版本号区分（新旧交替）

> 说明：代码仅一份（`demo-apps` 目录即"代码仓库"），版本差异由 build arg 注入，符合真实 CI/CD 语义（代码一份、tag 区分），无需本地 git 仓库。

#### 5.3.6 扩展策略（低成本可选项：红黑部署 / 影子部署）

两者均基于 5.3.3/5.3.4 已有的"建新环境 + 独立入口"能力，成本极低，列为 P5 可选项，不阻塞主流程。若实现，`STRATEGIES` 枚举相应增加 `red_black` / `shadow`。

**红黑部署（Red/Black）** —— 蓝绿的资源优化变体：

- 与蓝绿同构，差异仅在切换后**立即回收旧环境**（`kubectl delete deploy {app}-green`），不保留回滚窗口
- 实现：`_do_blue_green` 加参数 `retain_old: bool`（蓝绿=true 保留回滚窗口 / 红黑=false 立即回收），复用 5.3.3 能力
- 演示价值：Netflix 经典案例，与蓝绿对比可讲清"资源成本减半 vs 秒级回滚"的取舍

**影子部署（Shadow / 流量镜像）** —— 零风险验证：

- 新版本部署为 `{app}-shadow` Deployment（`track: shadow`）+ 独立 Service 入口，**不切任何主流量**，仅通过独立入口验证
- 本质 = 5.3.4 canary 独立入口玩法的前半段（无"确认全量"步骤）
- 实现：复用 5.3.4 能力（建新环境 + 独立 Service），无全量/清理步骤
- 演示价值：真实系统用 Istio Mirror 实现，这里用独立入口模拟，讲"零风险验证"概念

> 明确不纳入：A/B 测试（用户分桶）需要 ingress 的 header/cookie 路由，当前环境做不了；真实权重分阶段即 P5 灰度权重。

### 5.4 前端

#### 5.4.1 操作栏重组（`frontend/src/pages/releases/app-detail.tsx`）

- 删除「蓝绿部署」「灰度发布」两个按钮。
- 分组改为：
  - **「🚀 创建发布」**：常规发布、增量发布、补偿发布、回滚、克隆
  - **「🛠 运行管理」**：状态管理（新）、流量管理（改造）
- 删除 `handleRestart` / `handleStop` / `handleStart` 纯前端模拟逻辑。
- 「状态管理」按钮 → 打开新 Drawer（见 5.4.2）。
- 「流量管理」按钮 → 打开新 Drawer（见 5.4.3），替换现有纯说明 Modal。
- 发布历史 `typeOptions` 增加 `restart / stop / start / traffic`，`RELEASE_TYPE_LABELS` 同步补映射；版本列对非版本类发布单展示对应摘要（如 `restart` 显示"滚动重启"、`traffic` 显示"摘流/挂流"），参照现有 `scale` 的 `current → target` 渲染。

#### 5.4.2 状态管理 Drawer（新建 `frontend/src/components/StateManageDrawer.tsx`，以 `ScaleDrawer` 为模板）

- 选环境：环境选项带部署类型 Tag（复用 `ScaleDrawer` 的 `envOptions` 写法，`cfg.environment_deploy_type`）
- 根据所选环境 `deploy_type` 展示可用动作：
  - **k8s**：重启 / 停机 / 启动 / 实例伸缩（滑块 + 目标副本数）
  - **ec2**：重启 / 停机 / 启动（**伸缩禁用 + tooltip**："EC2 场景一般全量发布，手动调副本不适用"）
- 动作选择 + 可选原因 → 提交 `appApi.operations(appId, { env_code, action, ... })`
- 返回 `requires_approval` 时提示"已提交审批"，否则提示"发布单已创建"
- 新增 API 封装 `frontend/src/api/index.ts`：`operations: (appId, data) => client.post(\`/apps/${appId}/operations/\`, data)`

#### 5.4.3 流量管理 Drawer（新建 `frontend/src/components/TrafficManageDrawer.tsx`）

- 选环境（带部署类型 Tag）
- 动作：摘流（take_out）/ 挂流（restore）
- 展示说明：k8s = 修改 Service Selector；ec2 = ALB Target Group deregister/register（保留现有 Modal 文案，作为说明区）
- 提交 `appApi.operations(appId, { env_code, action: 'traffic', traffic_action, reason })`

#### 5.4.4 新建发布页（`frontend/src/pages/releases/create.tsx`）

- `deploy_strategy` 选项保留（蓝绿/灰度已在其中）。
- 选中 `blue_green` / `canary` 时，展示**策略说明链接**（新标签打开知识库文档对应锚点），弥补操作栏移除后的发现性损失：
  - 蓝绿 → 知识库 `deploy-strategies.html#s3`（蓝绿部署）
  - 灰度 → 知识库 `deploy-strategies.html#s4`（灰度发布）

### 5.5 知识库文档补充（`backend/knowledge/docs/releases/articles/deploy-strategies.html`）

`deploy-strategies.html` 已覆盖**理论 + 真实环境实现 + EC2 vs K8s 实现对比**，但缺少**本 Demo 系统的实现方式**。在每节（滚动/蓝绿/灰度）末尾补充"本 Demo 实现"，形成三块结构：**概念与原理 → 本 Demo 实现 → 真实生产/EC2 实现**。

| 策略 | 本 Demo 实现 |
|------|-------------|
| 滚动更新 | 真实：`kubectl apply` / `set image` + `rollout status` |
| 蓝绿部署 | 真实：创建 `{app}-blue` Deployment → 就绪 → 切换 Service selector（track label）；保留旧环境回滚 |
| 灰度发布 | 真实：创建 `{app}-canary` Deployment + 独立 Service 入口 → 就绪验证 → 手动确认全量 → 清理；权重放量为可选项（需集群内 ingress） |
| 流量管理 | 真实：patch Service selector 摘/挂流（EC2 为 ALB Target Group 模拟） |
| 红黑部署（可选） | 真实：复用蓝绿建新环境，切换后立即回收旧环境（无回滚窗口） |
| 影子部署（可选） | 真实：创建 `{app}-shadow` + 独立入口，仅验证不切主流量 |

> 该文档兼作演示讲解与面试复习材料，同时承载新建发布页策略选项的跳转目标（5.4.4）。

---

## 6. 分阶段实施计划

| 阶段 | 内容 | 涉及 | 验收 |
|------|------|------|------|
| **P1 操作栏重组（纯前端 UI）** | 删除蓝绿/灰度按钮；分组改「创建发布 / 运行管理」；状态管理、流量管理入口接入新 Drawer（先用模拟提交） | `app-detail.tsx`、新建 2 个 Drawer 组件 | 操作栏只剩 7 个入口，分组清晰 |
| **P2 后端 + 执行端真实化** | `release_mode` 枚举 + migration；`application_operations` 接口；公共函数抽取；executor 注册 `traffic` op + `k8s.patch_service_selector`；**`_do_blue_green` / `_do_canary` 改造为真实执行**（含 canary 独立 Service 入口）；CD 阶段按 `deploy_strategy` 分发（blue_green/canary → 对应 op）；`demo-apps` Service 基线加 track 维度并重放；**多版本模拟**（demo-app Dockerfile 加 ARG APP_VERSION + `_do_build` 传 `--build-arg`） | `models.py`、`views.py`、`urls.py`、`runner.py`、`k8s.py`、`demo-apps/config`、`demo-apps/*/Dockerfile` | 运维操作发布单进历史/审计；蓝绿/灰度发布真实建环境并切换；新版本镜像带正确版本号 |
| **P3 前端接通真实提交** | 状态管理/流量管理 Drawer 调 `operations` API；发布历史类型映射补全；`create.tsx` 策略说明链接；蓝绿/灰度发布单走真实 CD | `StateManageDrawer`、`TrafficManageDrawer`、`api/index.ts`、`app-detail.tsx`、`create.tsx` | 运维操作真实产生发布单，蓝绿/灰度发布真实执行，日志回流 |
| **P4 部署类型差异化** | EC2 环境禁用伸缩；环境选择器标注完善；tooltip 文案 | Drawer 组件 | EC2 环境正确禁用，K8s 环境完整 |
| **P5 知识库补充 + 可选增强** | `deploy-strategies.html` 补"本 Demo 实现"章节；**可选 1**：红黑部署 + 影子部署（复用蓝绿/灰度能力，低成本，见 5.3.6）；**可选 2**：集群内部署 ingress controller（集群内 traefik 或 ingress-nginx，仅服务 `release-demo`），实现灰度真实按比例放量 | 知识库文档、（可选）executor、（可选）集群内 ingress 部署 | 文档三块结构完整；扩展策略/灰度权重可演示（可选） |

> 蓝绿/灰度执行层（真实切换 Service / 权重路由）**不在本期**，单独排期（见 `plans/` 待补：deploy-strategy-execution-plan）。

---

## 7. 风险与注意点

1. **`scale_application` 兼容**：P2 抽取公共函数时，保持 `POST /apps/{id}/scale/` 响应结构不变（`appApi.scale` 前端依赖 `requires_approval` / `message` 字段），避免回归。
2. **ops 发布单的 CI/CD 任务**：现有 `_create_release_tasks` 会为每个发布单建 CI+CD 两个 `ReleaseTask`。运维类发布单（restart/stop/start/traffic）没有 CI 阶段，执行时**跳过 CI**、直接跑 CD（executor op 为 restart/scale/traffic）。需在 `execute_release` / `_watch_execution` 中对非 `regular` 类发布单做分支处理（参照 `scale` 当前如何绕过——确认 `scale` 发布单执行路径，保持一致）。
3. **Service selector 约定（蓝绿/流量共用）**：见 5.3.1，需更新 `demo-apps/config/*/{env}/deployment.yaml` 基线（Service selector 加 `track` 维度）并重放一次，保证集群状态与基线一致。
4. **权限**：运维操作走发布单后，应受现有发布权限模型约束（`get_user_accessible_app_ids`），确保无权限用户不能对任意应用执行重启/停机。
5. **`restart` 对 EC2 的语义**：EC2 无 Deployment 概念，`_do_restart` 的 ec2 分支需定义为"SSH 重启服务进程"（模拟日志即可），tooltip 说明与 k8s 差异。
6. **灰度权重路由依赖集群内 ingress**：真实按比例放量需要集群内有 ingress controller（当前 OrbStack K8s 集群无，宿主机 traefik-gateway 为 Docker Provider 不适用，见 5.3.0）。本次灰度做到"真实 canary 部署 + 手动全量"；权重放量列为可选项（P5），避免本次改造膨胀。
7. **demo 应用对外入口（已解决）**：已实测 OrbStack 支持宿主机直接访问 `<service>.<namespace>.svc.cluster.local`（HTTP 200），无需 NodePort/ingress，浏览器/curl 可直接验证蓝绿/灰度/流量效果（见 5.3.0）。注意该域名仅 round-robin 单 Service，不支持权重。

---

## 8. 验收标准（汇总）

- [ ] 操作栏仅含「创建发布」5 项 + 「运行管理」2 项，无蓝绿/灰度按钮
- [ ] 从操作栏任意入口发起操作，都能在发布历史看到对应类型（restart/stop/start/scale/traffic）的发布单
- [ ] 运维发布单有审批分支（需审批环境走 Approval）、有审计日志、有 executor 日志回流
- [ ] EC2 环境不适用操作（伸缩）被禁用并有 tooltip 说明
- [ ] 蓝绿/灰度通过新建发布页 `deploy_strategy` 正常创建，且策略选项旁有知识库文档跳转链接
- [ ] 蓝绿发布真实创建 `{app}-blue` 环境、切换 Service selector、保留旧环境（executor 内 `kubectl get deploy/svc` 可验证）
- [ ] 灰度发布真实创建 `{app}-canary` Deployment + 独立 Service 入口、就绪验证、手动全量后清理；灰度入口 `http://{app}-canary.release-demo.svc.cluster.local` 可访问新版本
- [ ] 流量管理真实摘/挂流（摘流后 `curl http://{app}.release-demo.svc.cluster.local` 失败/无响应，挂流后恢复）
- [ ] 多版本模拟：发布 v2 后，新环境响应 `"version":"2.0.0"`，主入口/灰度入口版本号可区分（`curl .../` 可见 `version` 字段）
- [ ]（可选）红黑部署：切换后旧环境立即回收（`kubectl get deploy` 无旧环境）
- [ ]（可选）影子部署：`{app}-shadow` 独立入口可访问新版本，主流量不受影响
- [ ] `deploy-strategies.html` 每节含"本 Demo 实现"，三块结构完整
- [ ] `POST /apps/{id}/scale/` 兼容无回归
