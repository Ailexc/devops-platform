# 发布系统权限模型演进与架构升级方案

> 文档定位：本方案既是发布系统权限模块的本地开发指导，也是一份可用于架构评审、项目复盘和面试讲述的材料。
>
> 核心结论：保留 V1 `用户—应用—环境` 实例授权模型在早期快速交付阶段的合理性；随着应用、部署目标与组织协作规模增长，升级为以 **资源树（Resource Tree）** 为事实模型、以 **策略授权（Policy Based Authorization）** 为源数据、以 **有效权限缓存（Effective Permission Cache）** 为读模型的 DevOps IAM Lite。

---

## 1. 背景与目标

### 1.1 业务背景

发布系统负责管理应用发布、回滚、日志查看、审批等持续交付活动。业务中的“应用”是可独立交付和维护的业务系统或服务，例如一个 Django 服务、工作流应用或微服务。一个应用通常会配置多个可部署目标：测试、预发、生产等；每个目标又会关联 AWS 账号、Region、EC2 资源、Kubernetes 集群和 Namespace 等基础设施信息。

系统同时存在三类权限诉求：

1. **模块权限**：用户能否看见某个菜单、按钮或管理能力。
2. **数据/操作权限**：用户能否对某个应用的某个部署目标执行发布、回滚、查看日志等动作。
3. **责任与审批权限**：业务负责人、应用负责人对应用归属、权限申请、交接等流程承担何种职责。

规模预期并不极端：约千级应用、每个应用数十个部署目标、五百级用户。资源总量本身可控；真正需要解决的问题是用户、组织和资源之间大量重复的授权关系，以及未来接入更多 DevOps 基础设施时的可演进性。

### 1.2 本次升级目标

本方案目标不是建设一个通用、无限可配置的企业 IAM 平台，而是在发布系统范围内完成一次可落地的权限抽象升级：

- 从“给用户逐条分配 App + Env 实例”的模型，演进为“表达授权意图并匹配资源”的模型；
- 避免错误地将应用权限和环境权限拆为两个独立列表后做笛卡尔积；
- 支持用户、团队（Group）和轻量角色（Role）授权；
- 将实际发布对象抽象为 `Deployment Target`，使 EC2/K8s 等不同发布形态统一进入鉴权；
- 支持测试环境批量授权、生产环境精确授权、未来新增同类环境自动覆盖；
- 为高频鉴权提供简单稳定的读路径，并可追溯最终权限来源；
- 不过度引入通用策略语言、任意属性表达式或跨系统统一 IAM 的复杂度。

### 1.3 非目标

本期明确不做以下事情：

- 不直接替代公司未来的统一权限中心；
- 不提供任意脚本化策略语言；
- 不把 Pod、实例、发布版本等运行时对象纳入发布权限树；
- 不试图用一个层级同时表达业务资产、组织结构和云基础设施拓扑；
- 不将“不可见”作为唯一安全手段。列表可见性是体验层控制，服务端动作鉴权必须独立、强制执行。

---

## 2. V1：用户—应用—环境权限模型

### 2.1 V1 模型

V1 以应用和环境组合为最小授权单元：

```text
User ── Permission ── Application + Environment
```

典型表结构如下：

```sql
user_app_env_permission(
  user_id,
  app_id,
  env_id,
  permission_code
)
```

发布请求携带 `user_id + app_id + env_id + action`，后端判断是否存在对应记录。应用与环境的实际组合由 `app_env` 或类似关系表维护，并可关联集群、账号、Namespace、EC2 等目标信息。

### 2.2 V1 在当时为什么合理

V1 并不是“错误设计”。在系统早期，它具备明显工程价值：

- **实现快**：表结构、管理界面、查询逻辑都直观；
- **语义清楚**：一条记录就是“某人可在某应用某环境做某事”；
- **容易审计**：能直接回答“谁有 `app-x / prod` 权限”；
- **读路径短**：按联合索引查询即可完成鉴权；
- **适合规模较小时的快速迭代**：应用、环境和用户均较少时，管理成本可接受。

因此，复盘时应准确表述为：**V1 选择实例级授权来满足早期快速交付，而不是因为没有考虑权限问题。**

### 2.3 V1 的边界

V1 的边界在于，它把“授权意图”和“授权结果”混在了一张源数据表中。例如“支付研发组可发布支付应用的所有测试环境”这一意图，被展开成多名用户 × 多个测试目标的大量记录。资源或成员变化时，需要人工或程序逐条增删。

---

## 3. 随业务增长出现的问题

### 3.1 重复授权与组合膨胀

假设一个应用有 30 个测试部署目标，开发人员需要测试发布权限。V1 需要为每个用户写入 30 条记录；一个小组 20 人即 600 条。这里的数据不是数据库容量问题，而是授权表达不准确：真实意图是“该团队可以发布此应用的测试目标”，而不是 600 个彼此独立的例外。

### 3.2 容易误入错误笛卡尔积

若分别保存用户的“应用列表”和“环境列表”，并在运行时判断：

```text
app ∈ allowed_apps AND env ∈ allowed_envs
```

就会形成错误笛卡积。例如用户可在 `app-1` 的 test 环境发布、可在 `app-2` 的 prod 发布，上述判断会误授予 `app-1/prod`。正确的授权单位必须保留应用与实际部署目标之间的关联，不能将两个维度割裂。

### 3.3 缺少组织级授权

团队成员权限通常高度相似。若 Group 只能用于通讯录或列表过滤，而不能作为授权主体，成员入组、离组和团队整体授权都会退化为批量复制个人权限，维护风险高且难以解释权限来源。

### 3.4 动作粒度被固定

“能访问某个 App + Env”不等于“可以执行所有操作”。实际至少会出现：

- 开发：发布、查看日志；
- 发布管理员：发布、回滚、重启；
- 审计人员：只读查看记录；
- 负责人：审批、转交、管理授权。

没有 Action 维度时，后续只能继续添加特殊字段或分裂权限表。

### 3.5 对基础设施扩展不自然

`test`、`prod` 只是环境分类，真正执行发布时必须知道具体目标：AWS 账号、Region、EKS 集群、Namespace 或 EC2 编组。若权限模型的资源只停留在字符串化的环境名称，未来难以统一不同发布形态。

---

## 4. 架构升级目标与原则

### 4.1 核心转变：实例授权 → 资源策略授权

升级后的源数据不再直接描述每一条用户—部署目标授权结果，而描述可理解的授权意图：

```text
谁（Subject）可以做什么（Action），作用于哪些资源（Resource Selector），在何种条件下（Condition）。
```

例如：

```text
支付研发组 可以 deploy 支付应用下 env=TEST 的所有 Deployment Target
```

目标资源仍然存在且具有唯一 ID；策略只是不再要求管理员逐个选择每个测试目标。

### 4.2 设计原则

1. **资源事实与授权表达分离**：资源树反映真实业务和部署关系；策略表达授权范围。
2. **默认拒绝**：无 Allow 即拒绝；前端隐藏不能代替后端鉴权。
3. **显式拒绝优先**：如引入 Deny，`Explicit Deny > Allow > Default Deny`。
4. **Group 可授权，Role 不等于组织**：Group 表示“谁在一起”，Role 表示“能做什么”。
5. **写复杂、读简单**：策略、成员和资源变化时计算；请求时查询已展开的有效权限。
6. **有限条件而非通用 DSL**：先支持 `env_type`、`region`、`cluster` 等白名单条件。
7. **审批责任与执行权限分离**：Owner 是责任链和审批路由，不应隐式变成无限制管理员。

---

## 5. 新方案总体架构

```text
┌──────────────┐        ┌──────────────────────────┐
│ User / Group │───────▶│ Authorization Policy     │
│   Subject    │        │ subject + role + action  │
└──────┬───────┘        │ selector + condition     │
       │                └────────────┬─────────────┘
       │ Membership                   │ match / expand
       ▼                              ▼
┌──────────────┐             ┌──────────────────────┐
│ Subject Graph│             │ Business Resource    │
│ User→Group   │             │ Tree                 │
└──────────────┘             │ Domain→App→Target    │
                             └────────────┬─────────┘
                                          │
                                  ┌───────▼────────┐
                                  │ Effective      │
                                  │ Permission     │
                                  │ Cache / Read   │
                                  │ Model          │
                                  └───────┬────────┘
                                          │
                           Can(user, action, target)?
```

模块权限可继续采用简单的 `role_level` 或模块能力映射；数据与操作权限由本方案的 Policy 模型承载。两者分开设计，避免用发布资源权限去表达菜单显示逻辑。

---

## 6. Resource Tree：业务资源树设计

### 6.1 三个关键概念

| 概念 | 定义 | 是否是核心资源 |
| --- | --- | --- |
| Business Domain | 业务线、业务域，是应用归属和业务负责人承载点 | 是 |
| Application | 可独立维护和交付的业务应用/服务 | 是 |
| Deployment Target | 一个应用实际可发布到的目标，原 `app + env` 关系的升级抽象 | 是，且通常为发布鉴权叶子 |
| Environment Type | TEST/PRE/PROD 等分类标签 | 否，是 Deployment Target 属性 |

### 6.2 推荐树形结构

```text
支付业务线（Business Domain）
└── payment-api（Application）
    ├── payment-test-01（Deployment Target, env_type=TEST）
    ├── payment-test-02（Deployment Target, env_type=TEST）
    └── payment-prod（Deployment Target, env_type=PROD）
```

`Deployment Target` 是发布系统真正需要鉴权的最小业务资源。发布接口不应只接收 `app + env_type`，而应接收解析后的 `target_id`；由目标记录确定究竟发布到哪个账号、集群或 Namespace。

### 6.3 Resource 基础字段

```sql
resource (
  id bigint primary key,
  resource_type varchar(32), -- BUSINESS_DOMAIN / APPLICATION / DEPLOYMENT_TARGET
  parent_id bigint null,
  name varchar(128),
  path varchar(1024),        -- 可选：物化路径，便于祖先/后代查询
  status varchar(32),
  attributes json,
  created_at datetime,
  updated_at datetime
)
```

建议在 `resource_type + parent_id + name` 上建立唯一约束。若需要频繁进行祖先、后代授权匹配，可补充 closure table 或物化路径索引；以当前规模，物化路径或递归 CTE 均可接受，优先选择团队熟悉的实现。

---

## 7. Environment：作为属性，而非核心资源

### 7.1 为什么不把 test/prod 本身当成树节点

`TEST`、`PRE`、`PROD` 描述的是部署目标的分类，不是一个能够独立操作、独立承担责任的业务对象。`payment-test` 与 `order-test` 并不共享同一个“test 资源”；将它们放在全局环境节点下会破坏应用与部署目标的真实归属关系。

### 7.2 属性设计的收益

Deployment Target 存储环境类型及部署元数据：

```json
{
  "env_type": "PROD",
  "deploy_type": "K8S",
  "cloud_provider": "AWS",
  "account_id": "123456789012",
  "region": "ap-east-1",
  "cluster_id": "eks-prod-a",
  "namespace": "payment"
}
```

这样，`env_type=TEST` 可用于策略条件和批量选择，而真实发布仍然精确落到 `target_id=payment-test-01`。

### 7.3 边界

环境类型不是权限的唯一判断依据。生产目标可能在不同账号、区域或集群；需要对某个具体生产目标例外授权时，策略必须可以精确指向该目标。属性用于选择，资源 ID 用于事实与最终执行。

---

## 8. Cluster、Namespace、AWS Account 等基础设施资源建模

### 8.1 本期策略：作为 Deployment Target 的绑定属性/关系

在发布系统中，Cluster、Namespace、AWS Account 的主要职责是描述“目标实际在哪里”，而不是发布用户直接管理的对象。因此本期不把它们强行放进业务资源树；它们通过 `deployment_target_infra_binding` 或目标属性关联：

```sql
deployment_target_infra_binding (
  deployment_target_id bigint,
  infra_type varchar(32), -- AWS_ACCOUNT / REGION / K8S_CLUSTER / K8S_NAMESPACE / EC2_GROUP
  infra_id varchar(128),
  metadata json
)
```

好处是：无论发布形态为 EC2、K8s 还是未来的其他执行器，发布权限都统一判断 `Can(user, action, deployment_target)`。

### 8.2 为什么不直接合成一棵“大树”

一个集群常被多个应用、多个业务线使用；一个 Namespace 也可能与应用树产生多对多关系。若硬塞成 `Application → Target → Cluster → Namespace`，会暗示集群只属于一个应用，并且造成“拥有集群权限是否拥有所有应用权限”的模糊继承。

### 8.3 后续需要基础设施管理时

当平台出现“创建 Namespace、扩缩容集群、管理云账号”等操作时，再建立独立的基础设施资源域：

```text
Cloud Account → Region → Cluster → Namespace
```

业务资源树和基础设施资源树由 Deployment Target 关联。两棵树的职责不同：前者服务发布授权，后者服务基础设施运维授权。

---

## 9. Subject 模型：User、Group、Role

### 9.1 概念边界

| 对象 | 回答的问题 | 示例 |
| --- | --- | --- |
| User | 谁在发起请求 | 张三 |
| Group | 谁属于同一组织/协作单元 | 支付研发组 |
| Role | 具备哪些操作能力模板 | Developer、ReleaseManager、Auditor |

Role 不能替代 Group。一个支付研发组中可能同时有开发、测试、发布管理员；同一个 Developer Role 也可能适用于多个小组。

### 9.2 Subject 与成员关系

可将 User、Group 统一为 Subject：

```sql
subject (
  id bigint primary key,
  subject_type varchar(16), -- USER / GROUP
  external_id varchar(128),
  name varchar(128),
  status varchar(16)
)

subject_membership (
  group_subject_id bigint,
  member_subject_id bigint,
  primary key(group_subject_id, member_subject_id)
)
```

本期建议只支持一层或有限层 Group 嵌套，并增加环检测。若未来存在复杂组织树，可维护 `subject_closure(ancestor_id, descendant_id, depth)` 作为成员展开读模型。

### 9.3 Role 的定位

Role 是可复用动作集合，不是全局权力等级。建议保留少量固定角色：

- `Developer`：部署到非生产、查看日志；
- `ReleaseManager`：部署、回滚、重启；
- `Auditor`：查看发布记录、日志和审计信息；
- `ApplicationOwner`：应用配置、权限审批等管理能力；
- `BusinessOwner`：业务线交接、业务范围管理与升级审批。

模块显示可使用 `role_level` 做快速控制，但执行鉴权仍以 Action + Policy 为准，避免“等级高就自动能做一切”。

---

## 10. Policy Based Authorization 模型

### 10.1 策略表达

一条策略表示：

```text
Subject + Role + Action Set + Resource Selector + Condition + Effect
```

示例：

```text
Subject: 支付研发组
Role: Developer
Actions: deploy, view_log
Selector: payment-api（包含其后代 Deployment Target）
Condition: env_type IN [TEST]
Effect: ALLOW
```

它表达的是稳定的业务意图；新增 `payment-test-03` 时，系统可自动将其纳入有效权限，无需人工逐个授权。

### 10.2 核心表

```sql
authorization_policy (
  id bigint primary key,
  subject_id bigint not null,
  role_id bigint null,
  selector_resource_id bigint not null,
  selector_mode varchar(32) not null, -- SELF / DESCENDANTS / TARGETS_BY_CONDITION
  condition_json json null,
  effect varchar(16) not null, -- ALLOW / DENY
  status varchar(16),
  valid_from datetime null,
  valid_to datetime null,
  created_by bigint,
  created_at datetime,
  updated_at datetime
)

policy_action (
  policy_id bigint,
  action_code varchar(64),
  primary key(policy_id, action_code)
)
```

策略应保留审批单号、来源类型（申请、负责人授予、系统默认、交接）与变更人，保证可追溯。

---

## 11. Action 设计

Action 是权限模型不可缺少的维度。建议使用稳定、业务化的枚举，而非 URL 或前端按钮名：

| 分类 | 建议 Action |
| --- | --- |
| 发布执行 | `deploy`、`rollback`、`restart`、`cancel_release` |
| 观察 | `view_application`、`view_release`、`view_log` |
| 应用管理 | `manage_application`、`manage_target` |
| 权限治理 | `request_access`、`grant_access`、`approve_access` |
| 归属治理 | `manage_owner`、`transfer_application` |
| 审计 | `view_audit`、`export_audit` |

Action 与资源类型要有合法组合校验。例如 `deploy` 只能作用于 Deployment Target，`transfer_application` 作用于 Application 或 Business Domain。不要仅因用户是 Owner 就绕过所有 Action 检查；Owner 可通过系统生成的责任角色策略获得明确能力。

---

## 12. Resource Selector 与 Condition

### 12.1 Selector：确定资源范围

Selector 指向资源树中的一个节点，并声明匹配范围：

- `SELF`：仅该资源；
- `DESCENDANTS`：该资源及其后代；
- `TARGETS_BY_CONDITION`：在该资源子树中，只选中满足条件的 Deployment Target。

例如将 `payment-api` 作为 selector，配合 `DESCENDANTS + env_type=TEST`，即可选中其所有测试目标。

### 12.2 Condition：有限的白名单条件

条件不应成为自由表达式语言。首期仅允许白名单字段和操作符：

```json
{
  "all": [
    {"field": "env_type", "op": "IN", "values": ["TEST", "PRE"]},
    {"field": "deploy_type", "op": "EQ", "value": "K8S"}
  ]
}
```

推荐字段：`env_type`、`deploy_type`、`region`、`account_id`、`cluster_id`。每新增字段都要经过安全与性能评审，并提供索引/反向索引方案。

### 12.3 精确例外

条件不应替代精确授权。对单个生产目标、特殊区域或临时发布需求，可创建 `SELF` 策略并设置有效期。临时权限到期后自动失效。

---

## 13. Effective Permission Cache：有效权限读模型

### 13.1 为什么需要缓存/物化视图

请求时实时计算“用户所属 Group → Role → Policy → 资源树 → 条件 → Allow/Deny”会让鉴权路径复杂、难以稳定。发布鉴权是读多写少场景，适合将策略源数据异步或事务后展开为有效权限。

```sql
effective_permission (
  user_id bigint,
  target_resource_id bigint,
  action_code varchar(64),
  effect varchar(16),
  source_policy_id bigint,
  source_subject_id bigint,
  version bigint,
  updated_at datetime,
  primary key(user_id, target_resource_id, action_code, source_policy_id)
)
```

该表是可重建的读模型，而不是授权事实的唯一来源。它可以存于关系数据库、Redis Set/Hash 或二者组合中。

### 13.2 查询原则

发布 API 的最终判定应近似为：

```text
Can(userId, "deploy", targetId)
  = exists effective ALLOW
    AND not exists effective DENY
```

在 Redis 中可采用按用户、动作分桶的 Set，例如 `perm:{userId}:{action}`，成员为 `target_id`；数据库仍保留可审计的有效权限明细。

### 13.3 展开触发条件

以下变化必须触发增量重算：

- Policy 创建、修改、失效、审批通过或撤销；
- 用户加入/离开 Group；
- Group 嵌套关系变化；
- Role 的 Action 集合变化；
- Deployment Target 创建、删除、环境属性变化、父级资源变更；
- Owner 转交导致系统生成的责任策略变化。

为降低一致性窗口，敏感操作（生产发布、权限撤销）应同步失效相关缓存或走一次源策略兜底检查；普通列表展示可接受短暂最终一致。

---

## 14. Group 授权模型

### 14.1 Group 是一级授权主体

Group 不只是可见性标签。它可以直接持有 Policy：

```text
支付研发组 → Developer → deploy/view_log → 支付业务线后代目标，env_type=TEST
```

用户加入该组后获得相应有效权限；离组后失去该组来源的权限。这样用户权限由“直接例外 + 所在 Group 权限”组成。

### 14.2 推荐使用方式

- **常规权限授予 Group**：团队测试发布、日志查看等；
- **例外权限授予 User**：临时生产发布、个别应用支援；
- **Role 定义能力模板**：避免每条策略重复勾选动作；
- **直接拒绝谨慎使用**：Deny 的确可以解决例外排除，但会使解释与排障成本上升。首期建议仅由安全/平台管理员创建。

### 14.3 可见性与执行权限

列表可见范围可由 `view_application` / `view_release` 等 Action 推导，也可配置一个更宽的“发现范围”。无论哪种方式，执行发布必须再次检查 `deploy` 权限，绝不能仅依赖“用户看得到该应用”。

---

## 15. Owner 模型

Owner 表示责任归属、审批链和治理能力，不等同于一条万能权限。

### 15.1 Business Owner

绑定到 Business Domain，通常为业务线负责人，职责包括：

- 业务线下应用归属管理；
- 业务负责人交接发起/确认；
- 处理升级审批和例外治理；
- 对业务线范围的应用申请承担最终责任。

### 15.2 Application Owner

绑定到 Application，可有多个，职责包括：

- 应用技术维护与部署目标配置；
- 常规权限申请审批；
- 应用层面的负责人维护；
- 对本应用发布风险承担技术责任。

### 15.3 Owner 解析（Ownership Resolution）

不要把 Owner 关系误做成不透明的权限继承。审批或责任查询从资源向上解析：

```text
Deployment Target
  → Target 级 Owner（若未来存在）
  → Application Owner
  → Business Owner
```

若目标没有专属 Owner，使用 Application Owner；需要升级或应用无负责人时再路由到 Business Owner。执行权限则由显式 Policy 控制，系统可根据 Owner 关系自动维护相应的治理策略，但必须可见、可审计。

```sql
resource_owner (
  resource_id bigint,
  user_id bigint,
  owner_type varchar(32), -- BUSINESS_OWNER / APPLICATION_OWNER
  status varchar(16),
  effective_from datetime,
  effective_to datetime null,
  primary key(resource_id, user_id, owner_type)
)
```

---

## 16. 应用交接与权限转移设计

### 16.1 交接对象

应用交接应转移的是**责任归属**，主要为 Application Owner 或 Business Owner，而不是盲目复制所有成员的发布权限。应用下 Deployment Target、历史发布记录和基础设施绑定保持不变。

### 16.2 流程

```text
选择应用/业务线范围
  → 指定新负责人
  → 发起审批
  → 审批通过
  → 原子更新 resource_owner
  → 生成/撤销负责人治理策略
  → 刷新 Effective Permission
  → 写入审计日志并通知
```

批量交接时，应以资源树根节点（业务线或应用集合）创建同一交接任务，审批通过后分批执行。若部分资源状态冲突，任务需要支持预检、失败明细与可重试，而不是静默部分成功。

### 16.3 负责人降级

当用户不再是任何业务线负责人时，系统只移除由 Business Owner 身份派生的治理角色；该用户仍可保留 Application Owner 或普通用户的其他 Group/Direct Policy。身份展示应由实际 owner 关系动态计算，不建议只写一个不可解释的全局等级字段。

---

## 17. 权限计算流程

### 17.1 发布鉴权主流程

```text
1. 发布请求传入 user_id、action=deploy、deployment_target_id
2. 校验 target 存在、状态可发布，且目标属于请求的 Application
3. 查询 effective_permission(user_id, target_id, deploy)
4. 若存在 Explicit Deny，拒绝；否则存在 Allow，放行；其余默认拒绝
5. 将 decision、policy 来源、request_id 写入审计日志
6. 放行后由 Deployment Target 的基础设施绑定解析实际执行位置
```

### 17.2 缓存未命中或重算期间

推荐做法：

- 常规操作：短时间重试或回源策略计算；
- 生产发布、撤权后操作：回源验证或同步版本校验，宁可拒绝并提示刷新，不允许使用过期 Allow；
- 在权限变更事件中携带 `permission_version`，网关/服务端以版本判断缓存是否过期。

### 17.3 授权解释接口

提供 `ExplainCan(user, action, target)`：返回 Allow/Deny、匹配到的 Group、Role、Policy、Condition 和资源路径。这是排障、审计和面试中体现系统可运营性的关键能力。

---

## 18. 核心数据库表汇总

| 表 | 作用 |
| --- | --- |
| `resource` | 业务资源树：业务线、应用、部署目标 |
| `deployment_target_infra_binding` | 目标与账号、区域、集群、Namespace 等实际基础设施关系 |
| `subject` | User / Group 主体 |
| `subject_membership` | 用户与小组、组嵌套关系 |
| `role` / `role_action` | 能力模板及其动作集合 |
| `authorization_policy` / `policy_action` | 授权源数据：主体、资源选择器、条件、动作、效果 |
| `resource_owner` | 业务和应用责任归属 |
| `effective_permission` | 可重建的用户—目标—动作有效权限读模型 |
| `permission_change_event` | 权限变更 Outbox/事件，驱动缓存刷新 |
| `permission_audit_log` | 授权变更和关键鉴权决策审计 |

关键索引建议：

- `effective_permission(user_id, target_resource_id, action_code, effect)`；
- `authorization_policy(subject_id, status, valid_to)`；
- `resource(parent_id, resource_type)` 与必要的属性索引；
- `subject_membership(member_subject_id)`；
- `resource_owner(resource_id, owner_type, status)`。

---

## 19. 性能、一致性与安全设计

### 19.1 性能

- 资源量为数万级，关系数据库足以管理资源事实；不要因数量焦虑提前引入图数据库。
- Policy 是低频写，Effective Permission 是高频读；采用物化读模型降低请求路径复杂度。
- 采用事件驱动增量展开，避免每次变化全量重算；按受影响的用户、Group、应用子树和动作更新。
- 对批量新增目标，按应用和环境类型选择匹配策略，再批量写有效权限。

### 19.2 一致性

权限变化与缓存刷新使用 Transactional Outbox：策略/成员/资源变化和 `permission_change_event` 同事务提交；消费者幂等地刷新读模型。事件包含聚合 ID、变更版本和幂等键。

对于“撤销生产发布权限”这类高风险变更，应在事务提交后立即删除相关 Redis 条目，并通过版本号阻断旧缓存；异步任务只负责补齐和审计，不成为安全边界。

### 19.3 审计与安全

- 所有授予、撤销、审批、交接、Owner 变更必须记录操作者、来源、前后差异、工单号与时间；
- 鉴权日志记录目标 ID、Action、决策、命中策略和请求链路 ID；
- 策略管理接口必须做权限校验与范围校验：应用负责人不能授予超出自己治理范围的生产权限；
- 临时授权必须有 `valid_to`，到期自动删除有效权限；
- Policy/Role 变更采用双人复核或审批流，尤其是生产发布和 Deny 策略。

---

## 20. V1 到 V2 迁移策略

### 20.1 原则：双写、比对、灰度，避免一次性切换

1. **资源归一**：将现有 `app_env` 记录映射为 `Deployment Target`；保留原主键与映射表，确保发布历史可追溯。
2. **构建业务树**：为每个应用挂接 Business Domain 和 Deployment Target；补齐 `env_type`、部署类型及基础设施绑定。
3. **导入主体和组织关系**：从现有用户/组织源同步 User、Group 与 Membership。
4. **迁移历史授权**：每条 V1 授权先转换为精确 `SELF` Policy，确保语义不丢失；再识别可合并的同类记录，逐步收敛为 Group + `env_type` 条件策略。
5. **双算比对**：一段时间内 V1、V2 对同一请求并行计算，记录差异；任何 V2 多放行必须阻断上线。
6. **灰度读取**：先用于权限中心展示和 Explain，随后切换非生产发布，最后切换生产发布。
7. **保留回退窗口**：V1 表在观察期只读保留，出现异常可切回 V1 判定；观察完成后再停止双写。

### 20.2 迁移注意事项

- 不要将原本的所有记录直接无脑展开为 V2 长期源策略，否则只是换表不换模型；
- 自动合并前必须确认原记录的 Action、有效期、审批来源一致；
- 生产环境授权先保持精确迁移，批量 `env_type=PROD` 策略须人工审核；
- 所有迁移任务应输出“V1 记录 → V2 Policy/Permission”的可审计对账报告。

---

## 21. 面试演讲版本：架构演进叙事

### 21.1 三分钟版本

我负责过一个发布系统，早期为了快速交付，采用了用户、应用、环境三元组的实例级授权模型。它的优点是实现和查询都很直接，早期规模下非常可靠。

随着应用和测试目标变多，问题不在于表记录是否能存下，而在于权限表达开始失真：团队“可以发布某应用所有测试环境”的一个业务意图，被展开成每个成员对每个目标的重复记录；同时，若将应用和环境分别授权，又会产生错误的笛卡尔积风险。

因此我没有否定 V1，而是把它演进为资源树加策略授权。我们把原有的 `app_env` 关系重新抽象为 Deployment Target：它是实际发布的最小资源，包含环境类型、账号、区域、集群和 Namespace 等事实信息。环境类型如 TEST/PROD 不再是孤立资源，而是目标属性，用于批量选择。

授权策略表达“哪个用户或团队，以什么角色，可以对哪些资源做哪些动作”。例如支付研发组能对 payment-api 下所有 `env_type=TEST` 的部署目标执行 deploy。系统异步将策略展开成用户—目标—动作的有效权限读模型，发布时只做快速、可审计的精确判断。这样既降低重复授权，又保留对单个生产目标精确授权的能力，并为未来 K8s/EC2 多发布形态扩展留出了边界。

### 21.2 十分钟讲述结构

1. **背景（1 分钟）**：发布系统有应用、部署环境、团队和审批协作；早期 V1 选择简单三元组授权。
2. **承认 V1 合理性（1 分钟）**：早期快速、明确、可审计，问题不是“写得差”，而是业务规模和资源模型变化。
3. **问题分析（2 分钟）**：重复记录、Group 无法授权、Action 缺失、App/Env 拆分导致笛卡尔积、基础设施难接入。
4. **核心抽象（2 分钟）**：将 `app_env` 解释为 Deployment Target；树是 Domain → Application → Target；TEST/PROD 是 Target 属性。
5. **方案（2 分钟）**：Subject（User/Group）+ Role + Action + Resource Selector + Condition；策略是源数据，有效权限是读模型。
6. **工程落地（1 分钟）**：事件驱动增量刷新、撤权强一致、Explain 接口、审计、双算灰度迁移。
7. **边界与未来（1 分钟）**：不做万能 IAM；基础设施运维权限未来采用独立资源域，与业务树通过 Target 关联。

### 21.3 面试中的关键表达

- 不说“旧方案很 low”，而说“V1 是早期业务阶段的实例授权选择，V2 是随着资源和组织复杂度增长的架构演进”。
- 不夸大为“建设统一 IAM”，而说“为发布系统设计 DevOps IAM Lite，并保留未来与统一权限中心对接的边界”。
- 强调最关键的取舍：**策略不等于最终权限；策略用于表达意图，有效权限用于稳定高频鉴权。**
- 主动说明风险控制：资源迁移、双算比对、生产权限精确迁移、可回退。

---

## 22. 后续演进方向

### 22.1 近期可做

- 丰富 Action 和 Role 模板；
- 引入临时权限与自动过期；
- 提供权限解释、差异对账、策略模拟；
- 将审批单、授权来源、审计记录串联；
- 为 Group 嵌套维护 closure read model。

### 22.2 平台化阶段

- 建立独立的基础设施资源域（账号、集群、Namespace），支持平台管理员操作；
- 对接公司统一组织、SSO 和未来统一权限中心；
- 将 Policy 事件标准化，向审计、CMDB、流水线等系统输出；
- 视真实需求引入更丰富的 Condition，但坚持字段白名单与可解释性。

### 22.3 不建议过早做的能力

- 自研复杂策略 DSL；
- 全资源图数据库化；
- 在没有明确运维资源操作需求时，把 Cluster/Namespace 强塞进发布业务树；
- 使用模糊的全局管理员等级绕过 Action 和资源范围校验。

---

## 附录 A：关键决策速查

| 决策 | 结论 | 原因 |
| --- | --- | --- |
| 最小发布资源 | Deployment Target | 对应实际可执行的 `app + env` 组合，并能绑定基础设施 |
| TEST/PROD | Target 属性 | 用于批量选择，不破坏资源事实关系 |
| Cluster/Namespace | 本期为 Target 基础设施绑定 | 避免把业务树和基础设施拓扑混在一起 |
| Group | 可授权 Subject | 消除团队权限的重复复制 |
| Role | Action 能力模板 | 与组织关系解耦 |
| Policy | 授权源数据 | 表达“谁能对什么做什么”的意图 |
| Effective Permission | 可重建读模型 | 支撑高频、稳定、快速鉴权 |
| Owner | 责任与审批解析 | 不作为隐式万能权限 |

## 附录 B：最终权限判定伪代码

```python
def can(user_id: int, action: str, target_id: int) -> bool:
    # 目标必须是有效的 Deployment Target；资源归属校验不可省略。
    target = deployment_target_repository.get_active(target_id)
    if target is None:
        return False

    permissions = effective_permission_repository.find(
        user_id=user_id,
        target_id=target_id,
        action=action,
    )

    if any(p.effect == "DENY" for p in permissions):
        return False
    return any(p.effect == "ALLOW" for p in permissions)
```

发布执行器在鉴权通过后，才读取 `Deployment Target` 的基础设施绑定并执行实际发布；执行器不得接受客户端直接传入的账号、集群或 Namespace 作为可信目标。

