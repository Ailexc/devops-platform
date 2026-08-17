# 权限中心整改计划（以我为中心 · 能力声明 · 双向账本）

> **实施状态（2026-08-04 全部阶段完成 + 系统观测显性化）**：阶段 1–10 全部落地；另新增"系统观测"板块（鉴权链路追踪/PEP解析工作台/身份解析PIP/Agent/分发/同步），把后台黑盒显性化。见文末《实施记录》与 §14《系统观测》。
> **版本**：v0.2（2026-08-04，两轮评审定稿，可开工）
> **来源**：本文整合 `plans/capability-manifest.md`（接口↔数据能力桥）与 `docs/requirements-user-centric.md`（以我为中心产品需求），经两轮评审（第二轮与实施代码逐条核对）修正后合并为**单一整改计划**，替代上述两份文档（原文件保留备查）。
> **v0.2 变更**：① 组织权限执行层确认已现成（Casbin 组层级传递），仅需管理面收紧；② 板块模板 `permission_templates` 退役，合并进能力声明；③ 数据接入规范简化为"注册契约 + 按需查询"；④ 通用接口（参数化路由）分级方案；⑤ 依赖与估时按代码现状修正（约 13–18 人天）。
> **与 `plans/refactor-plan.md` 的关系**：refactor-plan 是去中心化 IAM 的整体改造蓝图（模型收敛、治理、审批）；本文聚焦**产品需求 + 能力声明落地 + 前端以我为中心重构**，两文档的阶段互相引用，不重复。

---

## 0. 评审结论摘要

两份文档互补：capability-manifest 回答了"权限市场卖什么、申请时怎么选、我的权限怎么反查"；requirements 回答了"导航和页面怎么组织、谁看到什么、怎么点"。评审发现以下问题，已在本文中修正：

| # | 问题 | 出处 | 修正 |
|---|---|---|---|
| 1 | `data_scope: none` 语义歧义（"无限制" vs "无数据"） | capability §2.1 | 枚举重命名为 `all / owner / dimension / instance / n/a` |
| 2 | 示例与自动推断规则矛盾（read: none vs owner；update: owner vs instance） | capability §2.1 vs §5 | 统一推断初值表（§5.3），声明为准、owner 发布前必须确认 |
| 3 | 能力声明无版本、状态、审计；管理 API 无 owner 权限校验 | capability §2.3 / §4.1 | 增加 `version`/`status` + 管理面 PEP；变更仅审计、首次发布需确认 |
| 4 | 只定义了"能力长什么样"，未接上"谁被授权、有效期、来源、回收" | capability 全文 | 建立四层模型：能力声明 → 授权 → 模板 → 执行（§2.1） |
| 5 | 缺双向账本（谁访问了我的应用） | capability 全文 | 并入 FR-7 权限管理 + 新增 API（§7） |
| 6 | 组织权限继承规则未定 | requirements §7 | **已拍板**：仅末级配置、向下生效、父组织只读不具备（§2.2） |
| 7 | 访问者术语"程序"表述不佳 | requirements FR-7 | 统一为**下游应用**（技术模型复用 client/service） |
| 8 | 权限申请对象缺"下游应用" | requirements FR-3 | 申请主体扩展为：我 / 组织 / 自建组 / 下游应用 |
| 9 | 智能申请表单缺申请对象与 TTL | capability §3.2 | 申请单扩展：申请主体 + 数据范围 + TTL + 风险（FR-3） |

**v0.2 第二轮评审（2026-08-04，结合代码现状）结论**：

| # | 讨论点 | 结论 |
|---|---|---|
| 1 | 组织"向下生效"实现方式 | **执行层已现成**：`policy_builder.go` 组层级 `g(g:child,g:parent)` + `model.conf.go` 的 `g=_,_` 传递，任意层级配置已向下生效、父组织成员不拥有子组织权限。无需执行层改造，仅需**管理面收紧**（叶子 org 才可配置） |
| 2 | 板块模板 `permission_templates` 与能力声明重叠 | **板块模板退役**，合并进能力声明（能力 = 动作分组 + 数据语义；无数据模型 = 纯接口能力） |
| 3 | 数据接入规范 | 简化为**注册时契约测试 + 按需查询**，无常驻同步管道；`owner` 不做字段映射，走动态判定 / 应用自管关系（§6.1） |
| 4 | 通用接口（`/api/v1/{model}`） | PEP 路径模板解析（字面优先、模板兜底）；写操作必须落到具体资源类型，否则拒绝（§6.2） |
| 5 | custom 组与 org 关系 | custom 组**独立且平级**（不能挂 org、custom 间不嵌套）；org 树父子仅限 org 节点 |
| 6 | 能力声明生成方式 | `action` ← OpenAPI paths（已有）；`data_model` ← OpenAPI `components.schemas`（新增提取）；owner 手写兜底（§5.0） |

---

## 1. 目标与非目标

**目标**

- 以"我"为中心重构前端：工作台所有模块可点击跳转、导航按场景分组、上下文过滤代替角色切换。
- 以能力声明为桥，打通"接口权限 ↔ 数据权限"，让权限市场、权限申请、我的权限自助且可理解。
- 建立双向账本：我的应用被谁访问（资源方视角）+ 我的应用申请了谁（下游视角）。
- 组织权限遵循"仅末级配置、向下生效、向上只读"。

**非目标**

- 不做传统全局管理员控制台；全局只读合规入口另行评估（§10.5）。
- 能力声明自动化是半自动（推断初值 + owner 确认），不做全自动生成。
- 审批规则引擎本体在 refactor-plan 阶段 2，本文只定义申请单、状态与衔接。

---

## 2. 核心概念与术语

| 术语 | 定义 |
|---|---|
| 我（当前用户） | 系统唯一的上下文中心 |
| 组织 | 同步自身份源的树形组织；仅末级（叶子）组织可配置权限 |
| 自建组 | 用户创建的组：人的集合 + 权限集合（组即角色），支持 TTL |
| 资源方应用 | 被申请、被访问的应用（我的应用被别人申请） |
| 下游应用 | 申请 / 消费我方能力的应用；技术模型复用 OAuth2 client / service（M2M） |
| 上游应用 | 我方作为下游去申请其能力的应用 |
| 能力（Capability） | 应用声明的可授权单元：接口动作 + 数据模型 + 数据操作 + 支持的数据范围 |
| 授权（Grant） | 主体 × 能力 × 数据范围 × 效果 × TTL × 来源 |
| 策略模板 | 可复用的授权形状，发布到权限市场供申请 |

### 2.1 四层授权模型（整合后）

```
L1 能力声明 Capability Manifest  应用声明"我能提供什么、需要什么"
    └─ 能力 = 接口权限点(actions) + 数据模型 + 数据操作 + 支持的数据范围
L2 授权 Policy/Grant             谁（人/组织/自建组/下游应用）能用哪个能力、
                                 什么范围、到什么时间、来源是什么
L3 策略模板 Policy Template      可复用的授权形状（预填 L2 的字段），发布到市场
L4 执行 Enforcement              Casbin（动作级）→ OpenFGA（数据级）→ AND 放行
```

### 2.2 组织权限规则（已确认 + 执行层核对）

**执行层结论（v0.2，已核对代码）**：Casbin 组层级传递（`policy_builder.go` 生成 `g(g:child,g:parent)` 与 `g(u,g)`，`model.conf.go` 中 `g=_,_`）**天然实现**"配置向下生效、父组织成员不拥有子组织权限"。执行层**无需改造**，全部工作落在管理面（PAP）与展示层。

1. **配置点**：仅末级（叶子）组织可配置权限；非末级组织不提供配置入口（PEP + 前端双重收紧）。
2. **向下生效**：叶子组织配置的权限对其子树全部成员生效（执行层已支持）。
3. **向上只读**：父组织成员可查看下属组织（子树）的权限账本与成员，**不拥有、不配置**这些权限。
4. **组织可见性（隐含规则，需显式实现）**：登录用户对其直接隶属的每个 org 节点，自动拥有该节点子树的**只读查看权**（权限账本 / 成员 / 下级组织）；叶子节点额外获得"配置权"。
5. **org / custom 边界**：custom 组**独立且平级**——不能挂到 org 节点下、custom 之间不允许嵌套（每个 custom 是独立集合）；org 树父子仅限 org 节点（`createGroup` 需校验 parent 类型）。
6. **个人权限中的"组织继承"维度** = 我所在叶子组织配置并下发给我的权限；父组织成员不因下属组织权限而获得权限。

> 成员多组织归属：一人可隶属多个 org 节点，"我的组织"页面**并列展示**所有直接隶属节点，各节点权限按各自叶子组织配置分别生效。

---

## 3. 信息架构（导航重组）

```
工作台（我的首页）— 所有卡片/条目可点击跳转
├─ 个人权限
│   ├─ 我的权限（聚合视图）
│   │   ├─ 组织权限（末级组织配置的权限：组内应用/组外应用；父组织只读看下属）
│   │   ├─ 个人权限（组织继承 + 个人直接授权 + 自建组 + 临时 TTL）
│   │   ├─ 自建组权限（我加入的组：成员 / 权限 / 我的身份）
│   │   └─ 我的身份（组 leader/成员、应用 owner、审批人）
│   ├─ 权限申请（为自己 / 我的组织 / 我的自建组 / 我的下游应用）
│   └─ 自建组管理（创建 / 申请加入 / 退出 / 成员与权限管理）
├─ 应用权限
│   ├─ 应用管理（注册 / 我的应用清单 / 应用详情，含能力声明管理）
│   ├─ 策略管理（策略配置 / 模板 / 绑定应用 / 发布记录）
│   └─ 权限管理（谁在访问我的应用：下游应用 / 人 / 组织 / 自建组；我的应用申请了谁）
└─ 审计中心
    ├─ 我的申请
    ├─ 我的发布
    └─ 我的审批
```

> 保留"全局入口（主体目录 / 全局审计）"为权限到位才可见的只读合规入口，不放入主导航。

---

## 4. 功能需求

### FR-1 工作台（我的首页）

- 身份卡：姓名、所属组织、组织内身份、自建组身份、应用 owner 身份。
- 权限概览：按维度汇总（组织 / 个人 / 自建组 / 临时权限数）。
- 待办：待我审批数、进行中的申请数。
- 快捷入口：我的应用、我的自建组、权限申请。
- **交互要求：所有卡片、列表条目均可点击跳转；数字即入口**（跳转映射见 §8.1）。

### FR-2 我的权限（聚合视图）

#### FR-2.1 组织权限

- 我的组织为**末级**：展示本组织配置的权限，按维度分组：
  - **组内应用**：本组织拥有 / 注册的应用的授权账本（谁在访问我们的应用）；
  - **组外应用**：本组织向外部应用申请 / 获得的权限（我们用了外部应用的什么能力）。
- 我的组织为**非末级**：只读查看下属组织的应用权限聚合，不提供配置入口，不拥有这些权限。
- 组织成员：查看我所在组织及下属组织成员（按可见性规则）。
- 交互：组织树 + 权限账本；末级节点显示"可配置"，父级节点显示"只读"标识。

#### FR-2.2 个人权限（聚合视图）

- 聚合维度：
  - 组织继承（我所在叶子组织配置下发的权限）；
  - 个人直接授权（我为自己申请并通过的权限）；
  - 自建组权限（我加入的自建组挂载的权限）；
  - 临时权限（TTL 临时授权，含到期时间）。
- 每条记录：权限 / 能力名称、动作、数据范围、来源（组织 / 组 / 申请单）、授予人、时间、有效期、状态。
- 交互：维度 Tab + 搜索筛选；点击记录 → 查看**授权链**（谁给的、哪张申请单、审批人）。

#### FR-2.3 自建组权限

- 我加入的自建组列表：组名、组长、成员数、我的身份。
- 组详情：成员列表、组权限、组有效期、我的身份（组长 / 成员）。
- 组长能力：成员管理、权限配置、转让 / 解散；成员能力：查看、退出。

#### FR-2.4 我的身份

- 身份维度汇总：组织身份（leader/成员）、自建组身份（组长/成员）、应用身份（owner/使用者）、审批人身份。
- 说明我的管理范围：我能管理哪些组织、哪些应用、哪些自建组。

### FR-3 权限申请

- **申请对象**（四选一）：我自己 / 我的组织 / 我的自建组 / 我的下游应用。
- 申请内容：能力 + 动作 + 数据范围 + TTL（从能力目录选择，见 §5）。
- **智能申请表单**：
  1. 浏览权限市场能力目录（仅展示已发布能力）；
  2. 预检前置接口权限（`prereqs`）；
  3. 缺失的接口权限自动联动勾选，一并提交；
  4. 选择数据范围（all / owner / dimension / instance，按能力声明限定可选值）；
  5. 填写有效期（TTL，可永久，按风险限制上限）。
- 申请单：风险等级、审批链、状态流转（草稿 / 待审批 / 通过 / 驳回 / 已回收）。
- 规则：申请人不进入自己的审批链；高风险自动追加审批节点；来源标记 `via_request`（个人 / 组织 / 自建组）或 `app_request`（下游应用间）。

### FR-4 自建组管理

- 创建自建组：组名、成员、挂权限、有效期（TTL）。
- 申请加入自建组：浏览可加入的组 → 申请 → 组长审批。
- 退出自建组：成员主动退出；组长转让或解散。
- 规则：创建 / 加成员 / 挂权限均走审批（对齐 refactor-plan §3.1）。

### FR-5 应用管理

- 应用注册：应用信息、能力声明入口、owner（建议 ≥2）。
- 我的应用清单：我注册 / 拥有的应用。
- **应用详情页**：
  - 全部权限（动作 + 数据）；
  - 能力声明清单（draft / published / disabled，版本与变更记录，owner 管理入口）；
  - 对外暴露的权限（市场可见的能力与模板）；
  - 策略清单（已配置的授权及绑定关系）；
  - 分发记录（策略分发、bundle 状态，对齐 OPA bundle 设计）；
  - 被申请记录（人 / 组织 / 自建组 / 下游应用）。

### FR-6 策略管理

- 策略（授权）配置：主体 + 能力 + 数据范围 + 效果（allow / deny）+ TTL + 来源。
- 绑定应用：策略与应用的关联；从应用视角看到"发布了哪些策略、决定哪些资源可做什么操作"。
- **策略模板**：可复用的授权形状 → 发布 → 他人可申请（模板化资产）。
- 发布记录：版本、发布人、时间、状态、被申请次数。
- 规则：策略变更走审批；版本可回滚（对齐 policy_versions）；deny 由 owner 直接配置，不走市场申请。

### FR-7 权限管理（双向账本）

- **资源方视角（我的应用被谁访问）**：访问者分类 = 下游应用 / 人 / 组织 / 自建组。
  - 每个访问者：授予的权限、来源（owner 发布 / 申请审批）、有效期、状态。
  - 管理操作：调整、回收（回收走审批）、查看访问记录。
- **下游视角（我的应用申请了谁）**：上游应用列表 + 授权状态 + 申请单关联。
- 技术说明：下游应用复用现有 OAuth2 client / service（M2M）模型，UI 呈现为"下游应用"。

### FR-8 审计中心

- **我的申请**：我发起的全部申请，状态、审批链、结果。
- **我的发布**：我发布的策略 / 模板 / 授权记录。
- **我的审批**：待我审批的 + 我审批过的；审批操作入口。

---

## 5. 能力声明（Capability Manifest，整合后）

### 5.0 来源与生成方式（v0.2：自动推断为主，非手工编写）

**能力声明不是手工 YAML**，而是 OpenAPI 同步的副产品 + owner 一次确认：

```
注册/更新应用 → 拉取 OpenAPI（一份文档，两部分自动提取）
  ├─ paths              → 权限点 action（已有 syncApp / openapi_parser）
  └─ components.schemas → data_model 候选（表 + 字段，新增提取，复用现有 parser）
owner 只做：确认 + 填 allowed_scopes（唯一需要人脑的语义部分）
```

- `data_model` **可空**：空 = 纯接口能力（大部分系统只有接口授权需求）；有数据授权需求才绑定模型。
- 应用 OpenAPI 无 `components.schemas` 时，允许 owner **手写** `data_model`（自动推断只是初值，手工编辑为兜底）。
- 板块模板 `permission_templates` **退役合并**：原"同步按 tag 分组的板块"即能力声明的初值形态；删除板块概念，避免"板块 / 能力 / 策略模板"三概念并存。现有模板数据迁移为 `capability_manifests`（`data_model` 为空）。

### 5.1 声明结构（修正后示例）

```yaml
app: cmdb
capabilities:
  - name: 主机管理
    data_model: host
    operations:
      - operation: list
        description: 查看主机列表
        required_action: cmdb:host:list
        allowed_scopes: [all]
      - operation: read
        description: 查看主机详情
        required_action: cmdb:host:read
        allowed_scopes: [all, dimension, instance]
        default_scope: all
      - operation: create
        description: 创建主机
        required_action: cmdb:host:create
        allowed_scopes: [n/a]
      - operation: update
        description: 更新主机配置
        required_action: cmdb:host:update
        allowed_scopes: [owner, instance]
        default_scope: owner
      - operation: delete
        description: 删除主机
        required_action: cmdb:host:delete
        allowed_scopes: [instance]
```

### 5.2 数据范围类型（修正枚举）

| 类型 | 含义 |
|---|---|
| `all` | 有接口权限即可，无数据限制 |
| `owner` | 仅数据属主（资源的负责人 / 创建人） |
| `dimension` | 按维度过滤（组织 / 标签等） |
| `instance` | 实例勾选 |
| `n/a` | 不适用（如 create 新建操作） |

### 5.3 自动推断（修正默认值表）

| HTTP | 推断操作 | 推断范围 | 说明 |
|---|---|---|---|
| GET 集合 | list | `all` | owner 确认 |
| GET 单项 | read | `all` 或 `owner` | 按路径语义推断初值 |
| POST | create | `n/a` | 新建无既有数据范围 |
| PUT / PATCH | update | `instance` 或 `owner` | 声明为准 |
| DELETE | delete | `instance` 或 `owner` | 声明为准 |

**规则：推断仅作初值，发布前 owner 必须逐项确认，杜绝示例与推断不一致。**

### 5.4 能力声明管理规则

- CRUD 仅应用 owner 可操作（管理面 PEP，对齐 refactor-plan 阶段 1）。
- 变更属**非授权性配置，仅审计**（对齐 refactor-plan §3.1）；**首次发布 / 对外暴露需 owner 显式确认**。
- 版本化 + 可回滚（与 policy_versions 一致）。
- 未声明能力的应用仍可正常工作，但不出现在权限市场（"可选但推荐"原则保留）。

---

## 6. 数据模型（整合）

```sql
-- L1 能力声明（新增表；data_model 可空=纯接口能力）
capability_manifests (
  id, app_id, name, data_model(可空), description,
  version, status(draft/published/disabled), created_by, updated_by, timestamps
)
capability_actions (
  capability_id, action_id, data_operation(list/read/create/update/delete),
  allowed_scopes(jsonb), default_scope, description,
  PRIMARY KEY(capability_id, action_id)
)

-- L2 授权 = 现有 Policy 表增强（不另起炉灶；板块模板 permission_templates 已退役）
policies (
  + expires_at,          -- 策略级 TTL（临时授权承载；组/成员级 TTL 已有）
  + capability_id,       -- 关联能力声明（能力维度反查）
  + data_scope 结构化,    -- resource_scope 内 {type: all/owner/dimension/instance, values}
  现有: subject_type(user/group/service), subject_id, app_id, action_ids,
        effect, source(owner_grant/via_request/app_request), request_id, version, status, created_by
)

-- L3 策略模板（新增表）
policy_templates (
  id, app_id, name, description, capability_id,
  default_scope, ttl_days, effect, version,
  status(draft/published/disabled), published_at, published_by, apply_count
)

-- 申请单扩展（现有 requests）
requests (
  + applicant_subject_type(user/group/org/app), applicant_subject_id,
  + items(jsonb): [{capability_id, action_ids, data_scope, ttl}],
  + prereq_actions(jsonb): 联动申请的接口权限点,
  risk_level, approver_chain, status
)

-- 已就绪（无需改动）：Group/UserGroup 组级+成员级 TTL、Policy.source/request_id、OAuth client
```

> 说明：`grants` = 现有 `Policy` 增强（补 `expires_at`、`capability_id`、`data_scope` 结构化）；能力声明与策略模板为新增表；`permission_templates` / `template_actions` 退役（数据迁移为 `capability_manifests`）。

## 6.1 数据接入规范（v0.2：注册契约 + 按需查询）

**核心原则：IAM 不持有应用业务数据、不做常驻同步管道。** 对齐业内（OData / Zanzibar / Cedar）思路：授权系统只消费"表 + 行 + 关系"三个抽象，不复制业务数据。

**接入 = 注册时契约测试 + 按需查询**：

```
注册/更新应用时（onboarding contract test）：
  ① OpenAPI 可拉取、可解析出权限点（已有 syncApp）
  ② 能力声明格式合法（动作、allowed_scopes 枚举合法）
  ③ 若声明了 data_model：GET /models/{code}/instances 可调用且响应符合约定
  验证通过 → 进权限市场；失败 → 注册被拒 / 能力标记"未验证"

按需查询（无同步）：
  instance 勾选时 → 调应用 GET 列表接口（即 OpenAPI 里的 list action，
      required_action 鉴权后返回行数据）→ 勾选即用，IAM 不落库
```

**数据范围类型 → 判定方式（owner 不做字段映射）**：

| allowed_scopes | 判定方式 | 说明 |
|---|---|---|
| `all` | 动作级（Casbin） | 无数据逻辑 |
| `instance` | OpenFGA tuple（现有） | IAM 勾选写关系；行数据按需查询 |
| `owner` | **动态判定**（请求带上下文）或 应用自管 relation | IAM 不持有 / 不强求 owner 字段（跨系统身份映射不可靠）；能力声明 `allowed_scopes:[owner]` 仅表示支持该语义 |
| `dimension` | 动态判定（Filter 输出维度条件，现有雏形） | 维度是属性语义，动态求值最自然 |

**实例引用兜底**：勾选时校验行存在 + 申请时重新校验引用（不做实时同步）；应用删除数据时可调"通知 IAM"接口（可选，非强依赖）。

## 6.2 通用接口（参数化路由）分级方案（v0.2）

现实应用存在 `GET /api/v1/{model}` 这类**一个 handler 处理多类资源**的通用接口；现状会因"字面 path 匹配 + 解析跳过参数段"被 403（deny-by-default）。分级方案：

| 场景 | 做法 |
|---|---|
| `/api/v1/{model}` 参数化 REST 路由 | **PEP 路径模板解析**：action 记录 path 模板 + 资源槽位，请求时提取实际值并归一化 → 拼出真实权限点（`cmdb:host:list`）查 PDP；匹配优先级**字面 > 模板** |
| `/api/v1/entities?type=x`、统一查询入口 | **`X-Resource-Type` 请求头**（网关可信边界注入 / 校验，防伪造） |
| GraphQL 单一入口 | 动作级粗放 + 数据层过滤（应用侧 GraphQL 中间件执行），**仅查询** |
| 写操作走通用接口 | **禁止**：写操作必须能落到具体资源类型，否则拒绝（数据层过滤挡不住写操作） |

> 通用接口与能力声明同源：`{model}` 槽位的资源类型枚举 = 能力声明的 `data_model` 列表；PEP 用请求参数匹配到具体类型再查对应权限点。

---

## 7. API 设计（整合）

**应用 owner 管理面（管理面 PEP）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST/PUT/DELETE | `/api/v1/apps/:id/capabilities` | 能力声明 CRUD（仅 owner） |
| POST | `/api/v1/apps/:id/capabilities/:cid/publish` | 发布 / 下架能力 |
| POST | `/api/v1/apps/:id/sync-capabilities` | OpenAPI 推断（paths→action、schemas→data_model）+ owner 确认 |
| POST | `/api/v1/apps/:id/validate` | 注册契约测试（OpenAPI + 能力声明 + 数据接口可调用） |
| GET/POST/PUT | `/api/v1/apps/:id/templates` | **策略模板** CRUD + publish（L3，区别于已退役的板块模板） |
| GET | `/api/v1/apps/:id/grants` | 策略清单（绑定关系） |

> 管理面 PEP 为白名单式（`mgScope`），新增路由逐一加规则；组织权限收紧：`setGroupPermissions` 仅允许**叶子 org / custom 组**（非叶子 org 403）。

**权限市场 / 申请**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/marketplace/capabilities` | 能力目录（仅 published） |
| GET | `/api/v1/marketplace/capabilities/:cid/prereqs` | 前置接口权限预检 |
| POST | `/api/v1/requests` | 发起申请（主体 + 能力项 + TTL） |

**我的视图**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/me/overview` | 工作台聚合 |
| GET | `/api/v1/me/permissions` | 我的权限聚合（四维度 + 授权链） |
| GET | `/api/v1/me/org/permissions` | 组织权限（末级可配置 / 父级只读） |
| GET | `/api/v1/me/groups` | 自建组 + 我的身份 |

**双向账本**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/apps/:id/accessors?type=app|user|group|org` | 谁访问了我的应用 |
| GET | `/api/v1/apps/:id/accessors/:sid/grants` | 访问者授权明细 |
| POST | `/api/v1/grants/:id/revoke` | 回收（走审批） |
| GET | `/api/v1/apps/:id/upstreams` | 我的应用申请了谁 |

**审计**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/audit/my-requests` | 我的申请 |
| GET | `/api/v1/audit/my-publishes` | 我的发布 |
| GET | `/api/v1/audit/my-approvals` | 我的审批 |

---

## 8. 前端交互

### 8.1 工作台跳转映射（本次改造的直接诉求）

| 工作台卡片 | 跳转 |
|---|---|
| 身份卡 | 我的身份（FR-2.4） |
| 权限概览 · 组织 | 组织权限（FR-2.1） |
| 权限概览 · 个人 / 自建组 / 临时 | 我的权限（FR-2.2 / 2.3） |
| 我的申请（进行中） | 审计 · 我的申请 |
| 待我审批 | 审计 · 我的审批 |
| 我的应用 | 应用管理（FR-5） |
| 我的自建组 | 自建组管理（FR-4） |
| 快捷入口 · 申请 | 权限申请（FR-3） |

### 8.2 关键页面

- **权限市场**：能力目录卡片（动作 + 数据 + 范围 + 申请按钮），仅展示已发布能力。
- **智能申请表单**：对象选择（我 / 组织 / 自建组 / 下游应用）→ 预检 → 联动申请接口权限 → 范围选择 → TTL → 风险提示。
- **我的权限**：四维度 Tab + 授权链抽屉（谁给的、哪张申请单、审批人）。
- **权限管理**：访问者 Tab（下游应用 / 人 / 组织 / 自建组）+ 回收操作（影响范围提示）。
- **组织权限**：组织树 + 权限账本；末级节点"可配置"，父级节点"只读"徽标。

### 8.3 统一交互规范

- 列表统一：点击行 → 详情页或抽屉；数字 / 徽标 → 过滤后的列表页。
- 空态、加载态、错误态完整。
- 权限类操作给出影响范围提示（授予 / 回收谁什么权限、影响哪些人 / 应用）。

---

## 9. 分阶段实施计划

| 阶段 | 内容 | 估时 | 依赖 |
|---|---|---|---|
| 1 | 工作台可点击 + 路由重排 + 导航分组（前端骨架；Layout 导航已分组，改造量较小） | 1.5–2 天 | 无 |
| 2 | 模型扩展：能力声明 2 表、Policy 补 expires_at/capability_id/data_scope、申请单扩展、板块模板迁移 | 1–1.5 天 | 无（source/TTL/审批 SoD 已就绪） |
| 3 | 我的权限聚合 API（me/overview、permissions、org、groups）+ 组织权限管理面收紧（叶子校验、组织可见性） | 1–1.5 天 | 阶段 2 |
| 4 | 能力声明管理 API + OpenAPI 推断（paths→action、schemas→data_model）+ 注册契约测试 | 1.5–2 天 | 阶段 2 |
| 5 | 权限市场 + 智能申请 + 申请单（对象 / TTL / 联动） | 1–1.5 天 | 阶段 4 |
| 6 | 双向账本 + 权限管理 + 回收审批流（revoke 状态机，需新增） | 1–1.5 天 | 阶段 4 + client 模型 |
| 7 | 策略模板（L3）+ 发布记录 + 审计三视图 | 1 天 | 阶段 4 |
| 8 | 前端各页面（我的权限 / 自建组 / 应用详情 / 策略 / 权限管理 / 市场 / 审计，独立工作包） | 5–7 天 | 阶段 3/5/6/7 的 API |
| 9 | 通用接口：PEP 路径模板解析（字面优先）+ X-Resource-Type 兜底 | 0.5–1 天 | 阶段 2 |
| 10 | seed（按叶子组织配置）+ demo 回归 + 验收 | 1 天 | 全部 |

**合计约 13–18 人天**（后端 6.5–9 + 前端 6.5–9 + 联调验收 1–2；前后端可并行，日历 8–12 天）。

> 相对 v0.1（6–7.5 天）的差异：v0.1 低估了前端页面量（阶段 8）、管理面 PEP 扩展、回收审批流、通用接口与契约测试，且误以为部分前置依赖（Policy source/TTL、审批 SoD）未就绪——这些经代码核对已确认就绪。

前端路由重排：现有 `frontend/src/router/index.ts` 8 个平铺页面 → 三大板块 + 应用详情 / 组详情 / 我的权限等子页面。

---

## 10. 已确认决策（v0.2 全部拍板）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | "组外应用"范围 | = 本组织向外部应用申请 / 获得的权限（下游账本）+ 外部访问本组织应用的权限（上游账本），与"组内应用"构成组织级双向账本 |
| 2 | 个人权限的"个人"维度 | 含临时 TTL（临时权限独立维度展示） |
| 3 | 未声明能力的应用 | 隐藏于市场，保留申请入口提示"联系应用 owner" |
| 4 | 审批链规则 | 沿用 refactor-plan §3.1（申请人退出、双 owner 互批、自动路由）；核心已实现，仅扩展申请对象 / TTL |
| 5 | 全局只读合规入口 | 保留，权限到位才可见 |
| 6 | 成员多组织归属 | 并列展示所有直接隶属节点，各节点按各自叶子组织配置分别生效 |
| 7 | 组织"向下生效"实现 | 执行层已现成（Casbin 组层级传递），仅做管理面收紧（§2.2） |
| 8 | 板块模板 | 退役，合并进能力声明（§5.0） |
| 9 | 数据接入 | 注册契约 + 按需查询，无常驻同步；owner 动态判定 / 应用自管，不做字段映射（§6.1） |
| 10 | 通用接口 | PEP 模板解析 + X-Resource-Type 兜底；写操作必须落到具体资源类型（§6.2） |
| 11 | custom 组 | 独立平级，不能挂 org、custom 间不嵌套 |
| 12 | 能力声明生成 | action←OpenAPI paths（已有）、data_model←OpenAPI schemas（新增）、手写兜底（§5.0） |

---

## 11. 风险与注意点

1. **能力声明质量依赖 owner 确认**：自动推断仅作初值，发布前逐项确认（§5.4），否则市场目录失真。
2. **管理面 PEP 白名单式扩展易漏**：新增 20+ 路由需逐一加规则；组织权限收紧（叶子校验、组织可见性）需新域判断函数，建议集中成独立工作包。
3. **组织可见性是隐含权限**：须显式实现"隶属 org → 子树只读查看权"，否则下钻 API 无越权校验依据。
4. **回收审批流是新增状态机**：仅"申请→审批"方向已实现，revoke 需补审批链与执行，勿按"现成"估时。
5. **双向账本可见范围依赖 OpenFGA**：数据级过滤需 refactor-plan 阶段 5 支撑，前端先做结构、后接真实范围。
6. **owner / dimension 动态判定依赖应用配合**（请求带上下文）：需在 PEP 契约中明确约定，否则降级为动作级。
7. **前端改造量大**：估时已按页面清单上调（阶段 8）；建议先评审信息架构（§3、§8.1）再动手。
8. **术语统一**：UI 一律使用"下游应用 / 上游应用"，避免出现"程序 / service / client"等内部术语。

---

## 12. 实施记录（2026-08-04 第一轮）

**后端（阶段 2–9 全部落地，已编译 + e2e）**

| 交付 | 文件 |
|---|---|
| 模型：能力声明/能力动作/策略模板 + Policy 扩展（capability_id/data_scope_type/expires_at）+ 申请单扩展（subject 类型/TTL/items/prereq） | `model/capability.go`（新增）、`model/policy.go`、`model/governance.go` |
| Store：CapabilityRepo / PolicyTemplateRepo + AutoMigrate | `store/capability_repo.go`（新增）、`store/db.go` |
| 能力声明 CRUD/发布/OpenAPI 推断/契约校验 | `api/handler_capability.go`（新增）；`sync/openapi_parser.go` 增 `ExtractDataModels`；`sync/runner.go` 增 `FetchRaw` |
| 我的视图：overview/permissions/org/groups（授权链 + 组织可见性） | `api/handler_me.go`（新增） |
| 权限市场：能力目录/模板/预检 | `api/handler_marketplace.go`（新增） |
| 双向账本：accessors/grants/revoke/upstreams | `api/handler_accessors.go`（新增） |
| 策略模板 CRUD/发布（L3，板块模板退役） | `api/handler_template.go`（新增） |
| 审计三视图：my-requests/my-approvals/my-publishes | `api/handler_audit.go`（扩展） |
| 管理面 PEP：20+ 新路由规则 + 叶子 org 收紧 | `api/handler_mgmt.go`、`api/router.go` |
| seed：cmdb 能力声明（主机管理）+ 策略模板 + **幂等加固**（组织树查建/清理重复树/策略去重/身份源 upsert 收敛/组默认只读） | `cmd/iam-server/seed.go`、`sync/identity_connector.go`、`store/group_repo.go` |

**前端（阶段 1 + 阶段 8 核心页面）**

| 交付 | 文件 |
|---|---|
| 路由重排（/me/permissions、/me/groups、/apps/:id、/groups/:id、/audit?tab=） | `router/index.ts` |
| 导航按三大板块分组（个人权限/应用权限/审计中心） | `views/Layout.vue` |
| 工作台全可点击（身份卡/权限概览/待办/我的应用/自建组/快捷入口） | `views/Workbench.vue` |
| 我的权限（四维度 Tab + 组织树 + 授权链抽屉） | `views/MyPermissions.vue`（新增） |
| 我的自建组/身份 | `views/MyGroups.vue`（新增） |
| 应用详情（能力声明/模板/双向账本/回收） | `views/AppDetail.vue`（新增） |
| 组详情（成员/权限/身份） | `views/GroupDetail.vue`（新增） |
| 权限中心智能申请（对象/预检联动/数据范围/TTL/风险） | `views/Marketplace.vue` |
| 审计中心三视图 | `views/Audit.vue` |
| Apps/Groups 行点击跳详情 | `views/Apps.vue`、`views/Groups.vue` |

**验证结果**
- `go build ./...` + `go vet ./...` + `go test ./...` 全部通过；`npm run build` 通过。
- `scripts/demo.sh` 11 步全过（含网关 PEP：alice GET 200 / bob POST 403 / 无身份 403 / M2M GET 200）。
- 智能申请 e2e：bob 预检 → 申请能力（TTL 30 天）→ 自动审批 → 授权链（谁给/申请单/审批人）→ 回收后决策即时 deny。
- 组织树收敛为单一规范树（重复 seed 不再累积）；bob 组默认只读（写走申请审批）。

## 13. 实施记录 · 第二轮（2026-08-04，全部阶段完成）

**阶段 9：通用接口 PEP 路径模板解析 + X-Resource-Type 兜底**
- `model.Action` 增 `IsGeneric`/`ResourceSlot`；`openapi_parser.go` 识别通用路由（资源位置为槽位 `/api/v1/{model}` → `(model,collection)`、`/api/v1/{model}/{id}` → `(model,detail)`、统一查询入口 `/api/v1/entities` → `(header)`），GET 集合→list/详情→read 语义区分；code 用槽位名（`cmdb:model:list`）。
- `access_repo.go`：`ActionByRequest` 字面优先 → 模板解析（路径槽位提取 + 复数归一化 + `X-Resource-Type` 头兜底）→ 拼真实权限点（`cmdb:host:list`）查 PDP；写操作无法落具体资源 → deny。
- `handler_gateway.go` 传入 `X-Resource-Type`；`deploy/traefik/dynamic.yml` authRequestHeaders 放行 `X-Resource-Type`。
- mock-cmdb：新增 `/api/v1/entities` 统一查询 + OpenAPI 声明通用路径。
- 单测：`openapi_parser_test.go`（通用解析/槽位检测）+ `store/access_repo_test.go`（资源解析）。e2e：alice `/api/v1/entities`+`X-Resource-Type:host` 200 / `:disk` 403 / 无头 403；`/api/v1/host` 单数模板 200；写操作 `POST /api/v1/certs` 403。

**阶段 6：回收审批状态机（revoke）**
- `model.RevokeRequest`（pending/approved/rejected）+ AutoMigrate。
- `revokeGrant` 发起（仅 owner；审批链=其他 owner；唯一 owner 自动执行）→ `listRevokeRequests`（role=approver 待审批）→ `approveRevokeRequest`（SoD：申请人不得审批自己）→ `executeRevoke`（停用策略 + 撤销 OpenFGA + 缓存/bundle）。
- 前端：应用详情"回收审批（待我处理）"区 + 回收原因对话框（替代 window.prompt）。e2e：admin 发起→alice 待审批→通过→bob 决策即时 deny；SoD 拦截自审。

**阶段 8 完善**：应用详情能力/模板编辑对话框（名称/数据模型/描述/动作/TTL/默认范围，更新版本自增）。

**修复（第二轮）**：① runner.go 未拷贝 IsGeneric/ResourceSlot（通用 action 落库为字面）；② seed ensureOwner 幂等补双 owner（app_owners 缺 alice）；③ seed 数据策略 found 分支重发布 OpenFGA（回收后 seed 需重建关系）；④ Traefik 放行 X-Resource-Type；⑤ AppDetail 对话框补 v-model。

**验证**：`go build/vet/test` + `npm run build` 全过；demo.sh 11 步全过（含网关回归）。

**遗留（非本计划范围，见 refactor-plan）**：owner/dimension 数据范围动态判定需应用侧上下文约定（§6.1），demo 以动作级 + 实例勾选为主；revoke 审批为单级（应用 owner），多级审批链在 refactor-plan 阶段 2。

## 14. 系统观测（黑盒显性化，2026-08-04）

把后台黑盒能力在前台展示，新增"系统观测"导航板块（4 个页面 + 5 个后端端点）：

| 可视化 | 后端端点 | 前端页面 | 展示内容 |
|---|---|---|---|
| A 鉴权链路追踪 | `/decision-logs`（增强 TraceID/PEP + `?trace_id=` 展开） | `/observability/trace` | 一次请求从 网关PEP→action解析→Casbin动作级→OpenFGA数据级 的完整链路；PEP 解析步骤逐步展示 |
| B PEP 解析工作台 | `POST /debug/resolve`（步骤化） | `/observability/resolver` | 输入 method/path/身份 → 逐步展示 字面匹配→通用模板→X-Resource-Type→真实权限点 + 模拟决策 |
| C 身份解析（PIP） | `GET /debug/pip/:user` | `/observability/pip` | 主体→直接组/角色→祖先链→组权限→个人策略→OpenFGA 关系 |
| D Agent 工作台 | `GET /agents`（聚合中心 rev 对比） | `/observability/agents` | agent 在线状态/本地 vs 中心版本/决策量/命中率 |
| E 策略分发记录 | `GET /apps/:id/bundles` | 同上（tab） | bundle 版本历史（checksum/策略数/组规则数/发布人） |
| F 同步任务工作台 | `GET /sync-jobs` | 同上（tab） | OpenAPI/CMDB/Identity 同步历史（类型/状态/耗时/结果） |

**实现要点**：
- `DecisionLog` 增 `TraceID` + `PEP JSONMap`；`CheckRequest` 增 `TraceID`/`PEP`；网关生成 TraceID 并携带解析步骤落库；check-instance/filter 记录数据级链路（同 TraceID 多步）。
- store 层 `ResolveActionSteps` 步骤化解析（字面→模板→header），网关与 debug 端点复用。
- OpenFGA `ReadTuples` 需按对象类型逐个读（object 传 `"type:"` 通配），PIP 从 resource_models 取类型列表。
- 已验证：网关 3 请求产生带 PEP 信息的 trace；trace-demo-001 两步链路（动作级+数据级）；PEP 解析 4 种匹配场景；PIP bob 关系 `[(reader, host:host-3),(reader, host:host-4)]`；agent 36/36 已同步命中率 99%。

## 15. 授权即审批 + 数据丰富化（2026-08-04）

### 15.1 授权即审批（堵死 owner 直授后门）

**规则确认（项目基础逻辑）**：任何授权变更必须走申请单，无直授后门。owner 给别人授权也要走审批单，且**被授权方必须进入审批链确认**（"让他知道"），全部审批通过才生效（"留痕"）。SoD：申请人不审批自己的单子。

后端改动：

| 改动 | 说明 |
|---|---|
| `model/governance.go` | `AccessRequest` 增 `RequestType`（1=自助申请 apply / 2=owner 授权 grant）+ `Reason`（"为什么给我授权"） |
| `handler_policy.go` `createPolicy` | 不再直接创建策略 → 生成 **grant 授权申请单**（被授权方确认 + 应用其他 owner 复核 + 高风险 admin），返回 `approval_chain`；mgScope 保留 owner 校验（中间件读 body 须恢复） |
| `handler_governance.go` `buildApprovalChain` | grant 方向：被授权方确认（`granteeConfirm`：user→本人 / group,org→组长 / app→对方 primary owner）+ 其他 owner 复核（排除发起人）+ 高风险 admin |
| `handler_governance.go` `approveRequest` | **多级审批状态机**：回存 ApprovalTask 后检查链上所有审批人是否全部通过；未全过返回 `partially_approved`（含 remaining），**最后一人通过才 grantFromRequest 生效**。grant 方向无条件强制 inChain |
| `grantFromRequest` | Source 按方向（grant=SourceOwnerGrant / apply=SourceViaRequest），都关联 `RequestID` |

### 15.2 seed 数据丰富化（演示可用性）

| 维度 | 内容 |
|---|---|
| 组织树（9 节点） | 总公司 → 研发中心[研发一部/研发二部] + 运维中心[平台运维部/应用运维部] + 职能中心[安全合规部] |
| 用户（7 个） | alice(研发一部组长)/bob(成员)/carol(研发二部组长)/dave(成员)/erin(平台运维组长)/frank(应用运维组长)/grace(安全合规组长)，密码统一 `pass123`（seed 幂等重置），组长=组 admin |
| 应用（3 个） | cmdb(admin+alice) / monitor(erin+frank) / itsm(carol+dave)，各应用独立权限点集（`{app}:host:*`）与能力声明 |
| 授权 | **全部走 `grantViaRequest`**：建 grant 申请单（已通过）+ 审批任务留痕（被授权方确认 + 其他 owner 复核）+ 策略 + 关联 RequestID + 发布 OpenFGA |

**seed 幂等迁移**：`seedUser` 对已存在用户从旧 org 组迁出到目标组（历史组织树变更），保证"研发一部"有成员、旧"研发部"被清理。

### 15.3 我的权限可读化（me/permissions DTO）

- 去掉独立 `temporary` 维度 → 三维度 `organization/personal/custom_group`，TTL 并入 `expires_at` 属性。
- `decoratePolicies` 补 `app_code/app_name`、`reason`（从申请单）、`data_scope`（`decorateDataScope` 解析 `instance_ids` → 实例名）。
- `permissionCounts` 三维度；工作台第四卡片改"负责应用"。

### 15.4 前端改造

| 页面 | 改动 |
|---|---|
| `MyPermissions.vue` | Tab 命名（个人权限/自建组权限）；表格列：权限/应用/接口/数据实例/理由/有效期/来源；授权链抽屉显示理由 |
| `Policies.vue` | "发起授权"表单：被授权主体/接口/数据模型/实例/TTL/理由（必填）→ 提交后提示"待审批" |
| `Requests.vue` / `Audit.vue` | 审批待办加"方向"列（授权确认/申请）+ 理由；部分批准提示"尚待 N 位审批人" |

### 15.5 验证

- `demo.sh` 11 步全过（步骤 10 改为授权审批流：发起申请单 → bob 确认 `partially_approved` → alice 复核 `approved` → allow）。
- carol 授权 e2e：待办显示"授权确认"单（含理由）→ 确认 → 复核 → 生效；`me/permissions` 显示 reason + 双审批人链。
- 坑：① mgScope 白名单补 `/api/v1/audit/my-*`（我的三视图任何登录用户，否则被授权确认人看不到待办）；② zsh 脚本中 `UID` 为只读变量。

## 16. 组织展示清晰化（2026-08-04）

用户反馈：组织身份"研发部、研发一部"并存不知自己是领导还是成员；`/1/2/3/` 物化路径暴露；权限只显示 `cmdb:host:list` 映射看不到具体接口。

| 问题 | 根因 | 修复 |
|---|---|---|
| 双重组织身份 | seedUser 里 `Groups.RemoveMember(ug.GroupID, u.ID)` **参数传反**（签名 `(userID, groupID)`）→ 旧"研发部"成员迁不出去；cleanupOrphanOrgs 因有成员而保留 | 参数换序；cleanup 移到 seedUser 之后；删组前先删 `group_permissions` 残留（`cleaned 2 orphan org groups`） |
| `/1/2/3/` 路径暴露 | 前端直接渲染物化路径 | 后端 `orgPathNames`：`/1/2/53/` → `["总公司","研发中心","研发一部"]`，前端渲染树形 |
| 权限不按应用展示 | 组织权限是 action 平铺列表 | `groupActionsByApp`：actionIDs → `[{app_id, app_code, app_name, actions}]`，前端按应用分组 |
| 看不到具体接口 | 展示底层映射 code `cmdb:host:list` | action 自带 `method`/`path`（OpenAPI 解析）；前端 `actionText(a)` 显示 `GET /api/v1/hosts` |
| 成员无处可看 | 组织卡片只显示人数 | 成员抽屉：点"成员 N 人" → el-drawer 显示成员（头像/姓名/组长或成员标签，带 role） |

**后端**：`meOverview` identity.orgs 增 `path_names` + `my_role`；`meOrgPermissions` orgView 增 `path_names`/`permission_apps`/`members`(带 role)；`mePermissions` organization 维度同。
**前端**：MyPermissions 组织 tab（树形路径 + 按应用分组接口 + 成员抽屉）、MyGroups 组织身份（`总公司 → 研发中心 → 研发一部` [组长]）、Workbench 摘要。

**坑**：前端容器 `docker compose up -d` 不拉新镜像（tag 相同）→ 需 `--force-recreate`。
**验证**：alice 唯一身份"总公司→研发中心→研发一部"组长、组织权限按应用分组显示 `GET /api/v1/hosts`、成员抽屉（爱丽丝组长/鲍勃成员）；dave/erin/grace 各组织路径正确；demo.sh 11 步仍全过。
