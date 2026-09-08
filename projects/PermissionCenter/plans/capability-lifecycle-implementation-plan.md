# 能力包全生命周期 · 实施计划（定版 v10）

> 版本：v1.0（待评审）
> 日期：2026-08-05
> 前置文档：
> - `docs/architecture.md`（总体架构）
> - `plans/implementation-plan.md`（项目级实施计划，本计划为其能力包专项细化）
> - `plans/capability-lifecycle-design-discussion.md`（六问设计讨论逐轮记录，含 Round 1–6）
> - `docs/capability-apply-demo-v10.html`（**定版交互原型**，本计划的验收基准）
> - `docs/style-demos/demo-a-cloud-blue.html`（方案 A 视觉基准）
>
> 本文档定位：**能力包全生命周期改造的完整实施计划**——背景 → 问题 → 定论 → 方向 → 目标架构 → 分阶段任务 → 验收标准 → 决策点，供审查后开工。

---

## 0. 文档说明

### 0.1 目的

- 沉淀六问（Q1–Q6）从讨论到**定版**的全部结论，形成可执行的改造蓝图；
- 每个阶段都有：目标 → 任务清单（可勾选）→ 验收标准 → 工作量估算；
- 明确区分「**v10 定版必做（P0）**」与「**后续演进（P1/P2）**」，防止范围膨胀；
- 明确列出需要你**拍板**的决策点（§10）。

### 0.2 如何使用

1. 先通读 §1–§4 了解背景与定论；
2. §5–§7 是目标架构（模型 / API / 前端），审查细节；
3. §8 是分阶段实施顺序，每阶段以「验收标准」自检；
4. §9 是全链路验证矩阵（demo.sh + 浏览器 e2e）；
5. §10 决策点逐条批注后即可开工；
6. §13 附录把 v10 demo 的每个功能点映射到实施任务，防止"demo 与系统两张皮"。

### 0.3 状态标记

| 标记 | 含义 |
|------|------|
| ✅ 已有 | 现有代码已实现，直接复用/微调 |
| 🆕 新增 | 本次改造新增 |
| 🔧 改造 | 现有功能扩展/重构 |
| 🧪 验证 | 需补测试/验证 |

---

## 1. 背景

### 1.1 项目背景

权限中心（IAM）demo：Go + Gin 后端，Casbin（动作级 RBAC/ABAC）+ OpenFGA（实例级 ReBAC）双引擎；Traefik 网关作 PEP（forwardAuth → `/v1/gateway/check`）；Vue3 + Element Plus 管理台。用于面试展示 + 回忆知识点，叙事主线是"重构后的现代化方案"。

**能力包（Capability）**是应用对外暴露能力、供下游申请的统一载体，已有一期实现（见 §1.2）。

### 1.2 当前能力包实现现状（已有什么）

| 模块 | 现状 | 位置 |
|------|------|------|
| 能力声明模型 | `CapabilityManifest`：app/name/data_model/description/version/status(draft·published·disabled)/model_fields/scope_definitions/presets/tags | `backend/internal/model/capability.go` |
| 能力动作 | `CapabilityAction`：action_id + data_operation + allowed_scopes(all/owner/dimension/instance/n-a) + default_scope | 同上 |
| 能力 CRUD | 创建/更新/删除/发布（仅 owner，mgScope 门禁） | `handler_capability.go` |
| OpenAPI 同步 | `POST /apps/:id/sync-capabilities` 由 OpenAPI 推断 action → 能力预填 | `handler_app.go` |
| 数据范围选项 | `GET /capabilities/:cid/scope-options`（静态选项 / instance 实例列表） | `handler_capability.go` |
| 权限市场 | `GET /marketplace/capabilities`（仅已发布能力包 + 搜索筛选 + presets 富化 action_ids/ops） | `handler_marketplace.go` |
| 申请 | `submitRequest` 支持 capability_id/preset_id/scope/scope_params → 风险组合 + `buildScopeExpression`（all/owner/dimension/account/tag/instance → Casbin/OpenFGA 表达式模板）落 `content.scope_expression` | `handler_governance.go` |
| 申请预览 | `POST /requests/preview`（风险 + 审批链 + 表达式，不落库） | 同上 |
| 前端市场 | Marketplace.vue：能力卡片 + 5 步向导（浏览→主体→组合→范围→确认）+ 动态范围表单（auto/select/expression/input/instance）+ 实时表达式 | `frontend/src/views/Marketplace.vue` |
| 前端应用详情 | AppDetail.vue：能力/模板/双向账本/回收；能力编辑对话框（基础字段，P2 未完成） | `frontend/src/views/AppDetail.vue` |
| 主题 | 黑白单色 BW 设计系统（radius:0、emoji 图标） | `frontend/src/styles/theme.css` |

### 1.3 痛点与改造动机

1. **能力包形态太"单薄"**：只能声明动作 + 静态数据范围，无法表达「谁能申请」「谁能看见」「数据级条件」等现代能力目录该有的策略维度；
2. **配置靠手写 JSON**：能力 owner 难以自助配置，缺少表单化 UX；
3. **上下架不闭环**：只有能力包整体 publish，无法做到**预设级**上架/下架（一个能力包内不同预设面向不同人群），也无审批留痕；
4. **数据级范围表达能力弱**：只有维度/实例，缺**条件表达式**（OpenFGA CEL），用户申请"只给某几个库"只能靠实例勾选；
5. **UI 与定版视觉不一致**：方案 A（云原生企业蓝）已定，真实系统仍是黑白风格；
6. **双主体缺失**：申请单只有一个申请人，无法表达"grantee=程序身份（应用）、applicant=人代理"的典型 M2M 场景。

---

## 2. 最初的问题（六问）

> 完整讨论记录见 `plans/capability-lifecycle-design-discussion.md`。这里只列问题本身。

| # | 问题 | 核心疑问 |
|---|------|----------|
| **Q1** | 能力包如何控制**申请主体类型**？ | 谁能申请？能否限制"仅程序 / 仅某组织"？粒度到哪（能力包级还是预设/动作级）？ |
| **Q2** | 能力声明如何**表单化配置**？ | 取代手写 JSON；表单 ↔ YAML 是否双向？向导步骤？OpenAPI 导入预填？ |
| **Q3** | 拦截器放哪、怎么认证、是否每次远程鉴权？ | 网关集中 vs 应用 SDK vs 边车；每请求转发 IAM 太重，如何治？身份载体选什么？ |
| **Q4** | 能力包**可见范围**如何控制？ | public / 仅组织 / 仅组 / 仅应用 / 隐身？owner 自主还是平台审批？ |
| **Q5** | 能力包是否携带**网络/开通信息**，审批阶段如何打通？ | 网络可达性检查？工单？授权与开通的关系？鉴权怎么保证？ |
| **Q6** | 应用接入能力被保护的范围如何界定？ | 必须入网关才能发布？未接入应用能否发布/申请？严格 vs 宽松？ |

---

## 3. 最终的定论（六问收敛结论）

> 以下为 Round 2–6 逐轮收敛的**最终结论**，v10 demo 已按此实现并验证。

### Q1 · 申请主体限制 → **双主体模型 + 预设级 grantee_types 自由配置**

- **双主体模型（关键定论）**：
  - `grantee`（**授权作用主体**）= 真正获得权限的一方。典型 = 程序身份 `client:xxx`（M2M 应用）或用户/组/组织；
  - `applicant`（**申请人**）= 发起申请的人。程序是死的，必须由**应用 owner（人）代理申请**；
  - 申请单必须区分这两个角色；审批链 SoD：申请人 ≠ 审批人。
- **粒度**：不止能力包级，应到**预设（preset）/ 动作级**：
  - 能力包级默认 `grantee_types` + 预设级可覆盖；
  - 例：`数据库管理` 能力含「DBA 管理」预设（`grantee_types:[user]` + `org_restrict:[DBA组]`）与「数据库查看」预设（全员可申请）。
- **自由可定制**：`grantee_types` 是 owner 在声明文件里**自由配置**的，默认宽松，无硬编码规则。
- **申请时**：非程序主体不可选择（预设仅限程序时，主体步只"下游应用"可选，并提示"程序无法自己操作，由 owner 人代理"）。

### Q2 · 表单化配置 → **表单 ↔ YAML 双向，YAML 为 canonical**

- 格式本身不重要（JSON/YAML 均可），核心是 **表单 ↔ 结构化配置（YAML/JSON）双向互转**；
- **YAML 作为人可编辑的规范格式（canonical）**，DB 仍存 JSONB；后端 `yaml.v3` ↔ JSON，前端 `js-yaml`；
- **向导步骤**（schema-driven）：① 基本信息 → ② 接口/动作选择 → ③ 数据模型字段 → ④ 数据范围定义 → ⑤ 权限组合预设 → ⑥ 申请策略（Q1/Q4/Q5 声明）→ ⑦ 预览 + 校验 + 发布；
- OpenAPI 导入作为起点预填（已有 `syncCapabilities`，增强）；
- 原始 YAML 视图保留（面向高级用户 / 非小白）。

### Q3 · 拦截器 / 认证 → **网关 PEP + JWT 身份 + 缓存/bundle + 高风险强制远程；双模式接入**

- **认证（你是谁）与鉴权（能不能）解耦**：
  - 认证：JWT 验签 = 无状态廉价操作，**每请求可接受**；
  - 鉴权：决策缓存 + 本地 bundle（agent 只做动作级），**仅高风险写操作强制远程**（现有 §5.7 已规划 force-remote）。
- **身份载体**：网关统一校验 JWT（验签 + aud + exp + 短 TTL），注入规范化身份头 `X-User`；能力级临时令牌（审批受限令牌）为演进方向。
- **双模式接入（对应 Q6）**：
  - **Tier 1 网关托管**（受保护应用入 Traefik 网关，零改造）→ 可发布能力；
  - **Tier 2 SDK 自接入**（不入网关，装 SDK 验签 + 调 PDP 或嵌 bundle）→ 可发布能力；
  - **发布能力的前提 = 至少有一条强制路径**（网关 or SDK），manifest 声明 `enforcement_mode`；未接入任何强制路径的应用只能申请（消费者）。

### Q4 · 可见性 → **默认全可见 + 预设级限制申请 + hidden 隐身**

- **默认「都能看见、限制申请」**：`visibility: public` 可见 + 预设级 `org_restrict` 限制可申请（两个独立维度）；
- 支持 `visibility: org_visible / hidden`：敏感能力仅白名单/直链可见；
- **被拒时**给友好提示 + 推荐可申请的替代预设；
- **完全 owner 控制**：管理员是程序员，无法判断业务应用权限逻辑，不搞平台审批发布。

### Q5 · 网络/开通 → **授权与开通分离；网络信息声明 + 用户自选工单**

- **不做网络可达性自动检查**（复杂度高，放弃自动判定）；
- **网络信息 → 应用元数据板块**（注册应用时填写）：云/账号/区域/VPC/子网/安全组/容器/健康检查接口（无鉴权只返回状态），在应用详情页展示，**从能力包中移除网络配置**；
- 能力包保留 `network_ticket: none | user_choice | always`（默认 `user_choice`）：申请时用户**自行评估**（看应用网络信息）是否勾选"网络打通工单"；
- **授权与开通分离**：IAM 只做"许可决策"；网络打通/安全组/凭证签发是"落地动作"，通过工单/自动化完成，完成后才激活授权；
- 审批通过后：内部审批链 → 生成工单（demo 模拟表）→ 工单办理 → 回调 → **激活授权**（建策略 + OpenFGA tuple）。

### Q6 · 保护边界 → **enrollment 状态机 + 双层接入（与 Q3 合并定论）**

- App 状态机：`registered（注册=可申请/消费者）→ onboarded（接入网关=被保护）→ active`；
- **只有 onboarded 的应用能发布能力**（在我的保护范围内，才能保证 API 被鉴权）；
- **未接入的应用只能申请能力**；
- 能力发布时声明"网关保护路由"（路径前缀/域名），系统校验/生成网关配置；保护范围显式化、可审计。

---

## 4. 整体方向

### 4.1 总体框架（四层）

```
┌─────────────────────────────────────────────────┐
│ ① 声明层 Manifest  — 能力包"是什么/谁能用/谁可见"      │
│    Q1 双主体+grantee_types · Q4 visibility ·       │
│    Q5 network_ticket · Q6 enforcement_mode         │
├─────────────────────────────────────────────────┤
│ ② 创作层 Authoring — 能力包"怎么写"                 │
│    Q2 表单↔YAML 双向 · 表达式构建器 + 手册            │
├─────────────────────────────────────────────────┤
│ ③ 执行层 Enforcement — 权限"怎么执行/怎么保护"         │
│    Q3 网关 PEP + JWT + bundle · Q6 双模式            │
├─────────────────────────────────────────────────┤
│ ④ 开通层 Provisioning — 审批通过后"怎么落地"           │
│    Q5 网络工单/凭证签发 → 激活授权                     │
└─────────────────────────────────────────────────┘
```

### 4.2 核心设计原则

1. **授权（Authorization）与开通（Provisioning）分离**——许可决策始终在 IAM 令牌体系闭环，网络/凭证是前置落地动作；
2. **预设是配置核心单元**——接口 + 主体（grantee_types）+ 可申请范围（org_restrict）+ 数据权限（scope）都在预设级配置；同一能力包多个预设覆盖不同人群；
3. **预设级生命周期**——每个预设独立 `status: published | draft`，独立上架/下架（走审批），市场只展示已上架预设；
4. **可申请性 ≠ 可见性**——两套独立策略，可组合；
5. **面向非小白**——允许手写表达式 + 提供 OpenFGA/CEL 参考手册 + 表达式构建器辅助；
6. **owner 自服务**——弱管理员哲学，owner 自主配置、自主上架。

### 4.3 关键概念定版（v10 demo 基准）

| 概念 | 定版说明 |
|------|----------|
| **查看 vs 编辑** | 查看 = 编辑器详情页**只读版**（完整信息：基本信息/接口树/数据模型/预设全配置+状态/声明 YAML，仅不可编辑）；编辑 = 真编辑器 |
| **授权管理统一** | 上架/下架统一收进「授权管理」页：预设列表含状态（已上架/草稿）、每预设上架/下架（走审批→工单）、🔑授权信息钻取（维度/主体/申请单）、批量上架草稿、下架整个能力包、授权概况四维统计表 |
| **表达式构建器** | 数据范围「条件表达式」选项：字段 select → 操作符 select（`== != in !in >= <=`）→ 值 input → **实时生成 CEL 表达式**；另允许**手写表达式** |
| **OpenFGA/CEL 手册** | 弹窗参考手册：`== != in` / 比较 / `&& || !` / 字符串方法 `startsWith contains` + 值类型规范 |
| **折叠卡片** | 编辑器绑定接口 / 数据模型 = 可折叠卡片（默认折叠，点击展开选接口 / 看字段） |
| **增强预览** | 申请第 4 步分区展示：申请主体（双主体）→ 能力基本信息 → 申请的预设（接口/主体类型/数据范围表达式）→ 权限表达式（Casbin + OpenFGA 条件）→ 网络开通勾选 + 审批流 |
| **市场过滤** | 市场只显示 `status === published` 的预设（草稿预设不可申请但已授权者仍生效） |

### 4.4 与现有架构的关系

- 复用：Casbin + OpenFGA 双引擎、`buildScopeExpression` 表达式模板、`submitRequest`/`previewRequest`、`capabilityScopeOptions`、mgScope 门禁、审批链（ApprovalTask）、审计；
- 增强：CapabilityManifest 加策略字段、CapabilityAction/Preset 加状态与主体限制、scope_definitions 支持 expression 类型、授权管理接口、表达式校验服务；
- 不变：PEP/PDP 分离、网关链路、决策缓存、bundle 分发。

---

## 5. 目标数据模型

### 5.1 `CapabilityManifest` 扩展（🔧）

```go
type CapabilityManifest struct {
    Base
    AppID       uint64
    Name        string
    DataModel   *string
    Description string
    Version     int
    Status      string   // draft | published | disabled   ✅已有

    // —— v10 定版新增 ——
    DataControl     bool         `json:"data_control"`      // 是否开启数据级控制（false=所选接口访问全部数据）
    Visibility      string       `json:"visibility"`        // public | org_visible | hidden（默认 public）
    GranteeTypes    StringArray  `json:"grantee_types"`     // 能力包级默认可申请主体 [user,org,group,app]
    NetworkTicket   string       `json:"network_ticket"`    // none | user_choice | always（默认 user_choice）
    EnforcementMode string       `json:"enforcement_mode"`  // gateway | sdk | both（Q6，Tier1/Tier2）
    // —— 复用已有 ——
    ModelFields      JSONAny     // 数据模型字段定义
    ScopeDefinitions JSONMap     // 数据范围表单模板（含 expression 类型）
    Presets          JSONAny     // 权限组合预设（结构见 5.2）
    Tags             StringArray
}
```

- `status` 语义明确：**能力包状态**（draft/published/disabled）≠ **预设状态**（见 5.2）；
- `data_control=false` 时：市场申请不展示数据范围步（接口权限 = 全量数据），大多数应用场景（如 ITSM 自身有 assignee 逻辑）。

### 5.2 Preset 结构（🔧 增字段）

```jsonc
// presets[] 内元素
{
  "id": "readonly",                 // ✅已有
  "name": "只读查看",                 // ✅已有
  "icon": "👁️",
  "desc": "…",
  "action_codes": ["cmdb:host:list","cmdb:host:read"],  // ✅已有
  "allowed_scopes": ["all","instance","expression"],    // ✅已有（申请端可选范围）

  // —— v10 定版新增 ——
  "status": "published",            // published | draft（市场只显示 published）
  "grantee_types": ["user","org","group","app"],  // 预设级覆盖能力包默认
  "org_restrict": ["DBA组"]          // 可申请的组织范围（空=全员可申请）
}
```

### 5.3 `ScopeDefinition` 结构（🔧 增 expression 类型）

```jsonc
// scope_definitions 内元素（现有 auto/select/instance，新增 expression）
"expression": {
  "label": "按库名条件",
  "type": "expression",             // 🆕
  "desc": "手写或使用构建器生成 OpenFGA/CEL 条件表达式",
  "model": "database",              // 绑定数据模型（决定可用字段）
  "fields": ["db_name","env","cluster"],   // 🆕 表达式构建器的字段下拉数据源
  "operators": ["==","!=","in","!in",">=","<="],  // 🆕 构建器操作符（对齐后端）
  "placeholder": "db_name == \"db-cmdb\"",
  "examples": ["db_name == \"db-cmdb\"", "env in [\"prod\",\"staging\"]"],
  "validation": { "pattern": "", "hint": "对照 OpenFGA 参考手册" }
}
```

- **字段来源**：`model_fields`（§5.1 已有）或 OpenAPI schema 推断；
- **与后端对齐**：操作符/函数集合以 OpenFGA 实际支持的 CEL 能力为准（§5.5）。

### 5.4 新增 / 扩展模型

| 模型 | 说明 | 类型 |
|------|------|------|
| `CapabilityPresetStatus`（或并入 presets JSON） | 预设 status 直接存于 presets JSON（简单）**或**拆独立表（可审计版本化，推荐） | 🆕 |
| `CapabilityPublishTask` | 上架/下架审批任务（复用 ApprovalTask + 工单字段），记录：能力包/预设列表/动作(publish/offline)/发起人/审批链/工单号 | 🆕 |
| `AccessRequest` 扩展 | 增 `grantee_type`/`grantee_name`（程序身份 `client:xxx`）+ `applicant_id`（人）——**双主体落库**；`scope_expression` 已有 | 🔧 |
| `Grant`（accessors） | 已支持按主体维度查询授权（user/org/group/app），供授权概况四维统计复用 | ✅ |

### 5.5 OpenFGA 条件表达式（CEL）映射（关键）

- OpenFGA 支持 **condition（CEL）** 挂载在 relation 上（`condition db_name == "db-cmdb"`）；
- 现有 `buildScopeExpression` 已生成「Casbin + OpenFGA 模板」文案（dimension/account/tag/instance 分支），**本次将其提升为可落库/可执行的 CEL 条件**：
  - 动作级：Casbin `p, {subj}, {app}, {action}, *, allow`（✅已有）；
  - 数据级：OpenFGA 关系 + **condition**：
    ```
    type database
      relations
        define reader: [user, group:*, client:*] with condition DbCond
    condition DbCond(db_name: string, env: string) {
      db_name == "db-cmdb" || env in ["prod"]
    }
    ```
- **表达式构建器产物 = CEL 表达式字符串**，提交时：
  1. 后端 `POST /requests/preview` 校验语法（新 `cel.Parse` 或轻量正则校验，P0 用轻量校验 + 文档兜底）；
  2. 落申请单 `content.scope_expression`（✅已有字段）；
  3. 授权生效时写入 OpenFGA condition（复用现有 Write 通道扩展）。

---

## 6. API 设计

> 现有路由：`backend/internal/api/router.go`（mg 组，mgScope 门禁）。

### 6.1 能力 CRUD 扩展（🔧）

| 方法 | 路径 | 说明 |
|------|------|------|
| PUT | `/apps/:id/capabilities/:cid` | 支持新字段（data_control/visibility/grantee_types/network_ticket/enforcement_mode/presets.status 等） |
| POST | `/apps/:id/capabilities/:cid/publish` | 语义扩展：body 支持 `{action: publish|offline, preset_ids?:[]}` —— **预设级上架/下架**（原仅能力包整体） |
| GET | `/apps/:id/capabilities/:cid/presets/status` | 预设状态一览（供授权管理页） |

### 6.2 授权管理（🆕）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/apps/:id/capabilities/:cid/authz` | 授权管理聚合：预设列表（含 status）+ 每预设授权信息（维度/主体/申请单/授权时间）+ 授权概况四维统计（user/org/group/app） |
| POST | `/apps/:id/capabilities/:cid/authz/publish` | 上架（单预设 / 批量 `preset_ids`），创建审批任务 |
| POST | `/apps/:id/capabilities/:cid/authz/offline` | 下架（单预设 / 整个能力包 `all:true`），需所有使用方通过（审批） |
| GET | `/apps/:id/capabilities/:cid/grants` | 预设维度授权主体列表（复用 accessors 查询） |

### 6.3 表达式（🆕）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/capabilities/:cid/scope/expr-validate` | 校验手写/构建的 CEL 表达式（语法 + 字段白名单），返回错误行 |
| GET | `/capabilities/:cid/scope/expr-fields` | 表达式可用字段/操作符元数据（供构建器与手册渲染，数据源 = model_fields） |
| GET | `/openfga/manual` | **OpenFGA/CEL 参考手册数据**（操作符/函数/示例 JSON，前端弹窗渲染；避免前端硬编码） |

### 6.4 市场 / 申请（🔧）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/marketplace/capabilities` | presets 富化时**过滤 status==published**（市场只显示已上架预设） |
| POST | `/requests/preview` | 增强：返回双主体信息 + 表达式 + 网络开通（已有基础） |
| POST | `/requests` | submitRequest 支持 `grantee_type/grantee_name`（双主体） |

---

## 7. 前端设计

### 7.1 路由

```
/apps/:id                     应用详情（接口树 + 数据模型 + 网络信息 + 能力包列表）   🔧
/apps/:id/capabilities/:cid   能力编辑器（?view=1 只读 / 编辑）                    🆕
/apps/:id/capabilities/:cid/authz   授权管理                                      🆕
/marketplace                  权限市场（应用 → 能力 → 申请向导）                    🔧
/requests/:id                 申请单详情（含表达式 + 双主体 + 预览）                 🔧
```

### 7.2 能力编辑器（🆕 核心）

- **查看模式**（`?view=1`）：只读渲染完整详情——基本信息 / 接口树（点击展开）/ 数据模型（折叠卡片）/ 预设（含状态徽标）/ 声明 YAML（只读）；
- **编辑模式**：可编辑表单 + 右下角「保存」；
- **绑定接口** = 折叠卡片（默认折叠，点击展开勾选）；
- **数据模型** = 折叠卡片（checkbox + 展开字段）；
- **数据范围选项**：默认「所有数据 + 具体实例」，可添加「条件表达式」；
- **表达式构建器**：字段 select → 操作符 select → 值 input → 实时生成表达式；另有「手写表达式」输入框 + 「📖 表达式参考手册」按钮；
- **声明 YAML**：js-yaml 双向（表单 ↔ YAML），保存时后端 yaml.v3 ↔ JSON 校验；
- **向导第 6 步「申请策略」**：grantee_types（能力包默认 + 预设覆盖）+ visibility + network_ticket + enforcement_mode。

### 7.3 授权管理页（🆕）

- 预设列表：状态徽标（已上架/草稿）+ 每预设「🚀 上架 / 📉 下架」+「🔑 授权信息」钻取（维度/主体/申请单/授权时间表）；
- 能力包整体操作：「🚀 上架全部草稿预设」「📉 下架整个能力包」；
- 上架/下架弹窗：审批链展示 → 工单号（如 WO-088）→ 生效；
- **授权概况表**：预设 × 状态 × 四维主体（用户/组织/自建组/程序）计数。

### 7.4 市场申请流（🔧 增强）

- 应用 → 能力 → 预设（**只显示已上架预设**，草稿不可申请）；
- 步骤条：① 选择预设 → ② 选择主体（**双主体**：grantee=程序/用户 + applicant=申请人；预设仅程序时主体步只"下游应用"可选）→ ③ 数据范围（含「条件表达式」选项 + 手册 + 手写）→ ④ **预览审批**（增强分区）；
- 预览增强分区：申请主体（双主体）/ 能力基本信息 / 申请的预设（接口/主体类型/数据范围）/ 权限表达式（Casbin + OpenFGA 条件）/ 网络开通勾选 + 审批流；
- 被拒友好提示 + 推荐替代预设（org_restrict 校验失败时）。

### 7.5 方案 A 主题落地清单（🔧 P0）

以 `docs/style-demos/demo-a-cloud-blue.html` 为基准，重写 `frontend/src/styles/theme.css`：

```css
:root {
  --bg: #f5f7fa;            /* 亮灰蓝背景 */
  --bg-card: #ffffff;       /* 卡片白 */
  --bg-hover: #f0f4fb;
  --bg-inset: #f8fafc;
  --text: #1a2233;
  --text-secondary: #5b6472;
  --text-tertiary: #8b94a3;
  --border: #e3e8ef;
  --border-strong: #c9d2df;
  --accent: #2f6fed;        /* 品牌蓝 */
  --accent-hover: #2459d6;
  --accent-text: #ffffff;
  --success: #16a34a;  --success-bg: #e9f9ef;   /* 彩色语义标签 */
  --warning: #d97706;  --warning-bg: #fef4e6;
  --danger:  #dc2626;  --danger-bg:  #fdecec;
  --info:    #0891b2;  --info-bg:    #e6f7fb;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow-sm/md/lg: …;
  --font: -apple-system, …, 'Noto Sans SC', 'PingFang SC', sans-serif;
}
```

- 同步覆盖 Element Plus 变量（`--el-*` 全部映射到方案 A）；
- 保留 dark 模式（可选，或 v1 先只做亮色）；
- 页面 emoji 图标 → **SVG 图标**（如 `lucide`，或内联 SVG 组件库）；
- 全局边框圆角、阴影层级、hover 状态统一。

---

## 8. 分阶段实施计划

> 顺序原则：**视觉先行（独立低风险）→ 后端模型/接口（地基）→ 编辑器（创作层）→ 授权管理（生命周期）→ 市场申请（消费层）→ 表达式后端对齐 → 开通/审批闭环 → 验证**。
> 每阶段含验收标准；工作量以人日估算（单人，仅供参考）。

### Phase 0 · 方案 A 主题落地（🔧 P0，1–2 人日）

- 目标：真实前端视觉对齐定版方案 A，独立于功能改造。
- 任务：
  - [ ] 重写 `frontend/src/styles/theme.css` 为方案 A 变量（§7.5）；
  - [ ] 映射全部 Element Plus 组件变量；
  - [ ] 全页面 emoji → SVG 图标（先 Layout/导航/表格重点页面，其余滚动替换）；
  - [ ] 卡片圆角/阴影/hover 统一。
- 验收：`npm run build` 通过；浏览器逐页检查（登录/工作台/应用/市场/审计），视觉与 demo-a 一致，无黑白残留。
- 面试叙事：设计系统 token 化，可一键换肤。

### Phase 1 · 模型与后端扩展（🔧 P0，3–4 人日）

- 目标：数据模型与接口支持 v10 全部新字段，不动前端。
- 任务：
  - [ ] `CapabilityManifest` 加 `data_control/visibility/grantee_types/network_ticket/enforcement_mode`（AutoMigrate 自动加列）；
  - [ ] Preset 结构支持 `status/grantee_types/org_restrict`（JSON 内字段，写校验函数）；
  - [ ] `AccessRequest` 加 `grantee_type/grantee_name`（双主体）；
  - [ ] `publishCapability` 扩展预设级上架/下架（body 支持 preset_ids/all）；
  - [ ] 新增 `GET /authz` 聚合接口（预设状态 + 授权钻取 + 四维概况）；
  - [ ] 新增 `GET /expr-fields`、`POST /expr-validate`、`GET /openfga/manual`；
  - [ ] 新增 `CapabilityPublishTask`（上架/下架审批任务 + 工单）；
  - [ ] seed 数据：cmdb 能力包补全 v10 字段（预设 status 一上架一草稿、grantee_types、visibility、表达式 scope_definitions）；
  - [ ] mgScope 白名单补充新路由。
- 验收：`go build/test/vet` 通过；curl 验证 authz 聚合返回正确四维统计；预设上架/下架状态流转正确；市场过滤草稿预设。
- 面试叙事：预设级生命周期 = 能力包粒度化运营。

### Phase 2 · 能力编辑器前端（🆕 P0，4–5 人日）

- 目标：查看/编辑双模式、折叠卡片、表达式构建器、YAML 双向。
- 任务：
  - [ ] 路由 `/apps/:id/capabilities/:cid`（?view=1 只读）；
  - [ ] 查看模式只读渲染（接口树/模型/预设/YAML）；
  - [ ] 编辑模式表单 + 右下角保存；
  - [ ] 绑定接口 / 数据模型折叠卡片；
  - [ ] 数据范围：默认「所有+实例」+ 添加「条件表达式」；
  - [ ] 表达式构建器（字段→操作符→值→实时 CEL）+ 手写输入 + 手册弹窗（数据来自 `/openfga/manual`）；
  - [ ] js-yaml 双向（表单 ↔ YAML）；
  - [ ] 申请策略区（grantee_types/visibility/network_ticket/enforcement_mode）。
- 验收：浏览器 e2e——查看无任何可编辑控件；编辑可保存；构建器实时生成表达式；手册弹窗正常；YAML ↔ 表单双向一致。
- 面试叙事：声明式配置 + 双向视图，owner 自助。

### Phase 3 · 授权管理前端（🆕 P0，2–3 人日）

- 目标：上架/下架统一入口 + 授权信息钻取 + 概况。
- 任务：
  - [ ] `/apps/:id/capabilities/:cid/authz` 页：预设列表（状态徽标 + 上架/下架按钮）；
  - [ ] 授权信息钻取（维度/主体/申请单/授权时间）；
  - [ ] 批量上架草稿、下架整个能力包；
  - [ ] 上架/下架弹窗（审批链 + 工单号 + 生效反馈）；
  - [ ] 授权概况四维统计表。
- 验收：与 v10 demo 授权管理页逐项对照通过；上架走审批→工单→生效；下架需使用方通过。
- 面试叙事：能力运营（上架/下架/授权审计）一体化。

### Phase 4 · 市场申请流增强（🔧 P0，3–4 人日）

- 目标：双主体、预设过滤、表达式范围、增强预览。
- 任务：
  - [ ] 市场预设过滤 `status==published`；
  - [ ] 主体步双主体（grantee + applicant；程序代理场景）；
  - [ ] 数据范围步支持「条件表达式」选项 + 手册 + 手写；
  - [ ] 第 4 步增强预览（申请主体/能力信息/预设/权限表达式/网络开通）+ 审批流；
  - [ ] 被拒友好提示 + 推荐替代预设；
  - [ ] 提交携带 grantee 双主体 + scope_expression。
- 验收：与 v10 demo 申请流对照通过；双主体落库正确；表达式提交可预览可留痕。
- 面试叙事：面向程序身份的代理申请模式。

### Phase 5 · OpenFGA 表达式后端能力对齐（🆕 P1，2–3 人日）

- 目标：构建器/手写表达式与 OpenFGA CEL 真正对齐（非仅文案）。
- 任务：
  - [ ] 评估 OpenFGA condition 语法（`with condition`、CEL 类型约束）；
  - [ ] `expr-validate` 用真实 CEL 解析器校验（`github.com/google/cel-go`）或轻量白名单；
  - [ ] `buildScopeExpression` 的 expression 分支产出可落 OpenFGA 的 condition 文本；
  - [ ] 授权生效时把 condition 写入 OpenFGA（Write 通道扩展）；
  - [ ] 手册数据与后端能力一致（只列出真实支持的操作符/函数）。
- 验收：手写表达式语法错误被拦截；合法表达式授权后 OpenFGA check 带条件生效。
- 面试叙事：数据级条件 = OpenFGA CEL（Zanzibar 条件授权）。

### Phase 6 · 审批 / 工单 / 开通闭环（🔧 P1，2–3 人日）

- 目标：上架/下架审批链 + 网络工单 + 激活授权的完整闭环。
- 任务：
  - [ ] `CapabilityPublishTask` 审批流（Owner 确认 → 安全复核 → 工单）；
  - [ ] 网络工单（user_choice 勾选时生成，模拟表 + 预留 webhook 回调）；
  - [ ] 工单 done → 激活授权（建策略 + OpenFGA tuple + 必要时签发能力级临时令牌）；
  - [ ] 申请单详情页展示表达式 + 双主体 + 工单状态。
- 验收：demo.sh 全链路——申请 → 审批 → 网络工单 → 开通 → 网关放行/拒绝符合预期。
- 面试叙事：授权与开通分离，许可决策闭环在 IAM。

### Phase 7 · 种子数据 + demo.sh + 验证矩阵（🔧 P0，1–2 人日）

- 任务：
  - [ ] seed 补齐 v10 场景（cmdb 3 预设含草稿、itsm 只读、cloudportal 表达式范围、ops-tool 网络信息）；
  - [ ] demo.sh 新增能力包步骤（编辑 → 上架审批 → 市场申请 → 表达式 → 生效）；
  - [ ] 按 §9 验证矩阵跑全链路。
- 验收：`bash scripts/demo.sh` 全过；浏览器 e2e 与 v10 demo 逐项一致。

### Phase 8 · 双模式接入（Tier 2 SDK）与 enrollment（🆕 P2，后续）

- 目标：Q3/Q6 的 SDK 通道与 App 状态机落地（能力包定版范围外的大工程）。
- 任务（预研）：
  - [ ] 薄 SDK（验签 + 调 PDP 或嵌 bundle）；
  - [ ] App enrollment 状态机（registered/onboarded/active）+ 发布能力前置校验；
  - [ ] 能力级临时令牌（审批受限令牌落地）。
- 说明：不影响 v10 定版验收；单独排期。

---

## 9. 验证计划（全链路验证矩阵）

| # | 场景 | 期望 | 阶段 |
|---|------|------|------|
| 1 | 方案 A 主题 | 全页面无黑白残留、卡片圆角/彩色标签/SVG 图标 | Phase 0 |
| 2 | 查看 vs 编辑 | 查看零编辑控件；编辑可保存 | Phase 2 |
| 3 | 表达式构建器 | 字段→操作符→值 实时生成 CEL；手册弹窗正常 | Phase 2 |
| 4 | 预设状态 | 市场只显示已上架预设；草稿预设已授权者仍生效 | Phase 4 |
| 5 | 授权管理 | 上架/下架走审批→工单→生效；批量；四维概况 | Phase 3 |
| 6 | 双主体申请 | 程序预设仅"下游应用"可选；grantee/applicant 落库 | Phase 4 |
| 7 | 表达式校验 | 非法表达式被拦截；合法表达式授权生效（带条件） | Phase 5 |
| 8 | 网络工单 | user_choice 勾选生成工单；done 后激活授权 | Phase 6 |
| 9 | 回归 | demo.sh 全过；网关 PEP 链路（alice 200/bob 403）不回归 | Phase 7 |

---

## 10. 开放决策点（需拍板）

| # | 决策点 | 选项 | 建议 |
|---|--------|------|------|
| D1 | 预设 status 存 JSON 还是独立表 | A 存 presets JSON（简单）/ B 独立 `CapabilityPreset` 表（版本化审计） | B（上架/下架是运营动作，需留痕） |
| D2 | 表达式校验强度（Phase 5） | A 引入 cel-go 真解析 / B 轻量白名单 + 文档兜底 | 先 B 快速闭环，D2 记录为 P1 升级 |
| D3 | 网络工单对接 | A demo 模拟表 / B 预留 webhook 接口 | A（demo），接口预留 |
| D4 | 方案 A 是否保留 dark 模式 | A 仅亮色 / B 亮暗双主题 | B（现已有 dark 基础，成本低） |
| D5 | 能力级临时令牌（Phase 8） | A 本次不做 / B 预留接口 | A（记录） |
| D6 | `org_visible` 可见性在 demo 中是否要 UI 演示 | A 只做 public+hidden / B 三态全做 | B（实现成本低，展示完整） |

---

## 11. 风险与注意事项

1. **presets JSON 无 schema 约束**：写入前必须有结构校验函数（status 枚举/grantee_types 合法/org_restrict 引用有效组织），防止脏数据；
2. **OpenFGA condition 能力版本依赖**：需确认所用 OpenFGA 版本支持 condition（v1.x 部分支持），Phase 5 先做能力探测；
3. **表达式手写安全**：CEL 只读属性校验（禁副作用），防止注入式条件；
4. **市场过滤破坏现有申请**：草稿预设历史授权仍生效——查询授权时不受 status 过滤，仅市场目录过滤；
5. **YAML 双向漂移**：表单↔YAML 双向以"规范字段集"为准，未知字段保留（forward compat）；
6. **emoji → SVG 工作量**：按页面分批替换，先核心页面；
7. **mgScope 门禁**：新增接口全部补白名单 + owner 校验，防止越权。

---

## 12. 面试叙事素材对照表（随进度填充）

| 素材 | 对应实现 |
|------|----------|
| 外部化授权四组件 | PEP 网关 / PDP iam-server / PAP 管理面 / PIP 数据源（已有） |
| 预设级生命周期 | Phase 1/3 授权管理（上架/下架/批量/概况） |
| 双主体代理申请 | Phase 4（grantee=程序 + applicant=人） |
| 声明式配置 + 双向视图 | Phase 2（表单↔YAML） |
| 数据级条件授权 | Phase 5（OpenFGA CEL condition） |
| 授权与开通分离 | Phase 6（审批→工单→激活） |
| 双模式接入 | Phase 8（Tier1 网关 / Tier2 SDK） |
| 设计系统 token 化 | Phase 0（方案 A 主题变量） |

---

## 13. 附录：v10 demo 功能点 → 实施任务映射（验收基准）

> 逐条对照 `docs/capability-apply-demo-v10.html`，确保 demo 每个交互在真实系统有对应。

| v10 demo 功能 | 实施落点 | 阶段 |
|---------------|----------|------|
| 查看 = 编辑器只读版 | 能力编辑器 ?view=1 只读渲染 | Phase 2 |
| 编辑 = 真编辑器 + 右下保存 | 编辑器编辑模式 | Phase 2 |
| 授权管理：预设状态/上架/下架/钻取/批量/概况 | 授权管理页 + Phase 1 接口 | Phase 1/3 |
| 上架/下架走审批→工单 | CapabilityPublishTask + 工单 | Phase 3/6 |
| 表达式构建器（字段→操作符→值→实时 CEL） | 编辑器 + expr-fields 接口 | Phase 2 |
| OpenFGA/CEL 参考手册弹窗 | /openfga/manual + 弹窗 | Phase 2 |
| 手写表达式 | 编辑器 + expr-validate | Phase 2/5 |
| 绑定接口/数据模型折叠卡片 | 编辑器组件 | Phase 2 |
| 数据范围「所有+实例+表达式」 | scope_definitions expression 类型 | Phase 1/2 |
| 市场只显示已上架预设 | marketplace 富化过滤 status | Phase 4 |
| 申请 4 步（预设→主体→范围→预览） | Marketplace.vue 向导增强 | Phase 4 |
| 双主体（grantee/applicant） | AccessRequest 扩展 + 主体步 | Phase 1/4 |
| 增强预览（5 分区 + 审批流） | 申请第 4 步 | Phase 4 |
| 网络开通勾选（user_choice） | 预览步 + 工单 | Phase 4/6 |
| 方案 A 明亮蓝视觉 | theme.css 重写 | Phase 0 |

---

*（完）——审查后按 §10 拍板，从 Phase 0 顺序开工。*
