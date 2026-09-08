# 权限模块重构方案 v2

> 版本：v2.1  
> 状态：待审阅  
> 目标：在尽量还原真实项目实现方式的基础上，修复原权限模型中应用与环境分离计算导致的笛卡尔积误授权问题，并提升权限查询、展示、排错和高频鉴权的稳定性。

---

## 1. 设计背景

发布系统的组织、人员、应用和环境数据来自 CMDB 同步。CMDB 中已经维护了：

- 组织架构：部门、小组、人员；
- 应用归属：每个应用归属于一个最小承接组；
- 环境信息：应用下有哪些可发布环境；
- 默认权限：组对其名下应用默认具备基础发布权限。

本次重构不是从零设计一个通用 IAM 或企业权限中心，而是在原有“Role 承载功能权限和数据权限”的真实实现基础上做工程优化。

核心目标：

- 保留“每个组、每个用户都有专属 Role”的实现方式；
- 修复旧模型中 `app_ids * env_ids` 导致的笛卡尔积误授权；
- 明确区分功能权限和数据权限职责；
- 数据权限以应用为原子授权单元，表达清晰、可排查；
- 高频鉴权不依赖数据库 JSON 查询；
- 支持组默认权限、用户个人申请、跨组协作、明确拒绝、临时授权。

---

## 2. 核心设计结论

### 2.1 权限主体

只有两类主体可以绑定 Role：

| 主体 | 说明 |
|---|---|
| 最小一级组织组 | 应用的承接单位，如“运维开发小组”“电商支付组” |
| 用户 | 个人独立权限、临时权限、明确拒绝的承载主体 |

上级组织，如“运维部”“电商事业部”，只用于组织树展示、筛选和管理，不直接绑定 Role，也不直接承接应用权限。

### 2.2 专属 Role

初始化同步时，为每个组和用户创建专属 Role：

```text
- 电商支付组          -> 电商支付组_role
- 运维开发小组        -> 运维开发小组_role
- 张三 zhangsan       -> zhangsan_role
```

Group Role：

- 由 CMDB 初始化和同步维护；
- 绑定基础功能权限模板；
- 写入该组名下应用的默认数据权限；
- 默认开通该组应用的 dev 环境发布权限。

User Role：

- 用户创建时自动生成；
- 默认权限为空；
- 用于承载用户个人申请、跨组协作授权、临时授权、组长设置的明确拒绝；
- 用户最终权限以 User Role 中的规则优先。

### 2.3 功能权限与数据权限职责

权限判断拆成两段：

```text
can(user, action, target)
  = has_function_permission(user, action)
    AND has_data_permission(user, target)
```

功能权限决定“能做什么”：

- 发布；
- 回滚；
- 查看日志；
- 审批；
- 管理应用；
- 查看菜单或按钮。

数据权限决定“能操作哪些应用和环境”：

- 哪个应用；
- 哪类环境；
- 哪些具体环境实例；
- 是否为跨组协作；
- 是否临时授权；
- 是否明确拒绝。

本方案不在数据权限规则中存储 action，避免职责混乱。业务上不存在“某个应用能 rollback，另一个应用不能 rollback”的场景，动作能力由功能权限统一控制。

---

## 3. 数据权限设计

### 3.1 旧模型问题

旧模型倾向分别维护：

```text
app_ids = [app-1, app-2]
env_ids = [dev, prod]
```

运行时如果判断：

```text
app_id in app_ids AND env_id in env_ids
```

就会产生笛卡尔积误授权。

例如用户实际拥有：

```text
app-1 / dev
app-2 / prod
```

但分离计算后会错误得到：

```text
app-1 / prod
app-2 / dev
```

这是本次数据权限重构必须修复的核心问题。

### 3.2 新模型：以应用为原子授权单元

数据权限不再保存分离的应用集合和环境集合，而是保存一条条应用环境权限规则：

```text
一条规则 = 一个应用 + 一个环境类型 + 该类型下的授权范围
```

规则示例：

```json
{
  "app_id": 101,
  "env_type": "test",
  "is_all_envs": false,
  "allow_env_ids": [1001, 1002, 1003, 1004],
  "deny_env_ids": [],
  "grant_scope": "cross_group",
  "valid_from": "2026-07-23T00:00:00+08:00",
  "valid_to": "2026-08-23T00:00:00+08:00"
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `app_id` | 授权所属应用 |
| `env_type` | 环境类型，如 `dev`、`test`、`staging`、`prod` |
| `is_all_envs` | 是否授权该应用下该环境类型的全部环境 |
| `allow_env_ids` | 当 `is_all_envs=false` 时，明确允许的具体环境 ID |
| `deny_env_ids` | 明确拒绝的具体环境 ID，优先级高于允许 |
| `grant_scope` | 授权范围来源：本组权限或跨组协作权限 |
| `valid_from` | 生效时间，可为空 |
| `valid_to` | 过期时间，可为空 |

重要约束：

- `env_type` 不是全局环境权限；
- `env_type` 必须和 `app_id` 一起使用；
- 真实鉴权对象始终是应用下的具体环境实例；
- 不允许只凭 `env_type=dev` 判断用户拥有所有 dev 权限。

### 3.3 为什么不继续抽象 resource_type

本方案只保留应用维度，不引入 `business_line`、`owner_group`、`deployment_target` 等泛化资源类型。

原因：

- 应用在 CMDB 中已经归属于最小承接组；
- 上级组织不绑定 Role，也不直接承接应用；
- 跨组需求通过协作成员或用户专属 Role 显式授权；
- 以应用为规则锚点最容易展示、查询和排错；
- 每个组拥有的应用数量可控，规则数量膨胀可以接受。

当一个组拥有 10 个应用时，初始化会生成 10 条应用级数据权限规则。相比用一个上级资源规则隐式覆盖，应用级规则更清晰、更安全。

---

## 4. 数据权限示例

### 4.1 组默认 dev 权限

电商支付组拥有 `pay-api` 的所有 dev 环境权限：

```json
{
  "app_id": 101,
  "env_type": "dev",
  "is_all_envs": true,
  "allow_env_ids": [],
  "deny_env_ids": [],
  "grant_scope": "own_group",
  "valid_from": null,
  "valid_to": null
}
```

含义：

```text
允许该组成员操作 pay-api 下所有 env_type=dev 的环境实例。
```

### 4.2 用户申请部分 test 环境

`pay-api` 有 20 个测试环境，但用户只申请 `test1-test4`：

```json
{
  "app_id": 101,
  "env_type": "test",
  "is_all_envs": false,
  "allow_env_ids": [201, 202, 203, 204],
  "deny_env_ids": [],
  "grant_scope": "own_group",
  "valid_from": null,
  "valid_to": null
}
```

含义：

```text
只允许该用户操作 pay-api 的 test1-test4，不会自动获得 test5-test20。
```

### 4.3 跨组协作临时授权

运维开发用户临时协作电商支付组应用，授权 1 个月：

```json
{
  "app_id": 101,
  "env_type": "test",
  "is_all_envs": false,
  "allow_env_ids": [201, 202],
  "deny_env_ids": [],
  "grant_scope": "cross_group",
  "valid_from": "2026-07-23T00:00:00+08:00",
  "valid_to": "2026-08-23T00:00:00+08:00"
}
```

### 4.4 明确拒绝

组长明确禁止某用户操作 `test3`：

```json
{
  "app_id": 101,
  "env_type": "test",
  "is_all_envs": false,
  "allow_env_ids": [],
  "deny_env_ids": [203],
  "grant_scope": "own_group",
  "valid_from": null,
  "valid_to": null
}
```

---

## 5. 权限优先级

用户自动继承所在组的权限，但冲突时以用户自己的 Role 为准。

优先级：

```text
User Deny > User Allow > Group Deny > Group Allow > Default Deny
```

说明：

- 个人明确拒绝优先级最高；
- 个人申请通过的权限高于组默认权限；
- 组内默认权限来自 CMDB；
- 没有任何规则命中时默认拒绝。

### 5.1 组变更场景下的权限继承

当用户从一个组调整到另一个组时：

| 权限来源 | 说明 | 组变更后 |
|---|---|---|
| **原组 Group Role**（own_group 权限） | 通过组归属继承的组默认权限 | ❌ 自动清理——用户不再关联原组 |
| **新组 Group Role**（own_group 权限） | 通过新组归属继承 | ✅ 自动获得 |
| **User Role**（cross_group 协作权限） | 存储在用户专属 Role 中，`grant_scope=cross_group`，不依赖组归属 | ✅ **保留**——协作权限授予的是**用户个人**，不因组变更而撤销 |
| **User Role**（个人申请、deny） | 存储在用户专属 Role 中 | ✅ **保留** |

关键设计保障：

- **跨组协作权限解耦于组归属**：协作权限写入的是用户的 **User RoleDataRule**，不是 Group RoleDataRule。用户离组只切断与 Group Role 的关联，User Role 不受影响。
- 因此，小明从 A 组调到 B 组后，A 组的 own_group 权限自动清除，但之前授予的 C 组协作权限继续有效——**不需要额外逻辑处理**。

```text
用户入组/离组重算只需要：
  1. 重新计算该用户的 EffectivePermissionCache
  2. 展开时：Group Role 来自新组，User Role 保持不变
  3. 计算逻辑（§7.3）天然保证了这一点
```

---

## 6. 后端数据模型

### 6.1 Role

Role 仍然是权限承载对象，保存功能权限集合。

```python
class Role(models.Model):
    ROLE_OWNER_TYPES = [
        ("group", "组角色"),
        ("user", "用户角色"),
    ]

    name = models.CharField(max_length=64, verbose_name="角色名称")
    owner_type = models.CharField(max_length=16, choices=ROLE_OWNER_TYPES)
    permission_codes = models.JSONField(default=list, verbose_name="功能权限编码列表")
    is_system = models.BooleanField(default=False, verbose_name="系统内置")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role"
```

可以通过 `Group.role_id`、`User.role_id` 显式关联 Role。这样比 `owner_type + owner_id` 更直观，也更符合当前项目实现。

### 6.2 Group

```python
class Group(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=32, unique=True)
    business_line = models.ForeignKey(BusinessLine, on_delete=models.CASCADE)
    parent_group = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    role = models.ForeignKey("authz.Role", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, default="active")
```

约束：

- 只有最小承接组才应该绑定 Role；
- 上级组织节点不直接绑定 Role；
- 应用只能归属到最小承接组。

### 6.3 User

用户增加专属 Role 关联：

```python
class User(models.Model):
    username = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=64)
    role = models.ForeignKey("authz.Role", null=True, blank=True, on_delete=models.SET_NULL)
```

用户创建或 CMDB 同步时自动创建空白 User Role。

### 6.4 RoleDataRule

数据权限使用独立表，不再直接塞进 `Role.data_rules` JSON。

```python
class RoleDataRule(models.Model):
    GRANT_SCOPES = [
        ("own_group", "本组权限"),
        ("cross_group", "跨组协作"),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="data_rules")

    business_line_id = models.BigIntegerField(verbose_name="业务线 ID")
    owner_group_id = models.BigIntegerField(verbose_name="应用承接组 ID")
    app_id = models.BigIntegerField(verbose_name="应用 ID")

    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    is_all_envs = models.BooleanField(default=False, verbose_name="是否授权该类型下全部环境")

    allow_env_ids = models.JSONField(default=list, verbose_name="允许环境 ID 列表")
    deny_env_ids = models.JSONField(default=list, verbose_name="拒绝环境 ID 列表")

    grant_scope = models.CharField(max_length=16, choices=GRANT_SCOPES, default="own_group")
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role_data_rule"
        indexes = [
            models.Index(fields=["role", "app_id", "env_type"]),
            models.Index(fields=["app_id", "env_type"]),
            models.Index(fields=["grant_scope", "valid_to"]),
        ]
```

`business_line_id` 和 `owner_group_id` 是冗余上下文字段，主要用于展示、查询和排错。核心鉴权仍以 `app_id + env_id` 为准。

### 6.5 EffectivePermissionCache

高频鉴权使用展开后的读模型。

```python
class EffectivePermissionCache(models.Model):
    EFFECTS = [
        ("allow", "允许"),
        ("deny", "拒绝"),
    ]

    user_id = models.BigIntegerField()
    app_id = models.BigIntegerField()
    env_id = models.BigIntegerField()
    effect = models.CharField(max_length=8, choices=EFFECTS)

    source_role_id = models.BigIntegerField()
    source_rule_id = models.BigIntegerField()
    valid_to = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "effective_permission_cache"
        indexes = [
            models.Index(fields=["user_id", "app_id", "env_id"]),
            models.Index(fields=["user_id", "env_id"]),
            models.Index(fields=["app_id", "env_id"]),
            models.Index(fields=["valid_to"]),
        ]
```

该表是可重建的读模型，不是权限源数据。

---

## 7. 权限计算逻辑

### 7.1 功能权限

用户功能权限：

```text
用户功能权限 = Group.role.permission_codes + User.role.permission_codes
```

如果后续需要功能权限 Deny，可单独扩展。目前按照真实系统经验，功能权限由基础模板和用户额外功能权限合并即可。

### 7.2 数据权限规则匹配

单条 RoleDataRule 匹配目标环境：

```text
1. target.app_id == rule.app_id
2. target.env_type == rule.env_type
3. 当前时间在 valid_from / valid_to 范围内
4. 如果 target.env_id in rule.deny_env_ids，则命中 deny
5. 如果 rule.is_all_envs = true，则命中 allow
6. 如果 target.env_id in rule.allow_env_ids，则命中 allow
7. 否则不命中
```

### 7.3 用户数据权限判定

```python
def has_data_permission(user, target) -> bool:
    user_rules = load_user_role_rules(user)
    group_rules = load_group_role_rules(user)

    if match_deny(user_rules, target):
        return False

    if match_allow(user_rules, target):
        return True

    if match_deny(group_rules, target):
        return False

    if match_allow(group_rules, target):
        return True

    return False
```

### 7.4 最终鉴权

```python
def can(user, action, env_id) -> bool:
    target = load_app_environment(env_id)

    if not has_function_permission(user, action):
        return False

    if not has_data_permission(user, target):
        return False

    return True
```

安全原则：

- 不信任前端传入的 `app_id`、`env_type`；
- 后端必须根据 `env_id` 查询真实应用、环境类型、集群、账号等信息；
- 所有发布、回滚、查看日志、审批操作都必须后端强制鉴权；
- 默认拒绝；
- 过期权限不参与计算。

---

## 8. 高频鉴权与性能

### 8.1 数据规模估算

当前系统规模：

```text
应用：约 1000 个
环境：约 50 个，增长缓慢
用户：约 500 个，增长缓慢
应用增长：每天 5 个以内
```

RoleDataRule 源数据估算：

```text
1000 应用 * 4 类环境 = 4000 条基础规则
加上个人申请、跨组协作、deny 例外，预计 1 万 - 2 万条
```

即使按具体环境粒度拆分：

```text
1000 应用 * 50 环境 = 5 万条
```

该数据量对关系型数据库非常可控。

EffectivePermissionCache 常态估算：

```text
每用户平均 30 个应用 * 5-10 个环境 = 150-300 个 target
500 用户 * 300 target = 15 万条左右
```

即使平均到每人 1000 个 target：

```text
500 用户 * 1000 target = 50 万条
```

仍然属于普通关系型数据库可轻松承载的规模。

### 8.2 查询策略

RoleDataRule 是权限源数据，用于：

- CMDB 同步写入；
- 权限申请通过后写入；
- 页面展示；
- 排错查询；
- 生成 EffectivePermissionCache。

RoleDataRule 面向“权限管理、展示、维护和解释来源”。只要问题是“某个组有哪些权限”“某个用户为什么有这个应用环境权限”“审批通过后应该写入什么权限”，都应该使用 RoleDataRule。

EffectivePermissionCache 是由 RoleDataRule、用户组关系和用户专属 Role 展开得到的鉴权读模型，用于业务接口的高频权限判断。

运行时鉴权不做 JSON 条件查询，也不每次扫描 RoleDataRule。

最终高频鉴权路径：

```text
1. 检查功能权限缓存或会话中的 permission_codes
2. 查询 EffectivePermissionCache:
   user_id + app_id + env_id
3. deny 命中则拒绝
4. allow 命中则允许
5. 默认拒绝
```

### 8.3 EffectivePermissionCache 生成时机

EffectivePermissionCache 在权限事实发生变化后生成或重算：

- 初始化或 CMDB 首次同步完成后；
- CMDB 增量同步导致组应用归属变化；
- 应用新增、环境新增、环境下线；
- 用户入组或离组；
- 权限申请审批通过；
- 组长设置用户明确拒绝；
- 跨组协作授权创建、修改或到期；
- Role 功能权限模板或数据规则发生变更。

生成方式：

```text
同步重算：
  权限变更接口提交后立即重算，适合单用户或小范围变更。

事务后异步重算：
  权限源数据提交后投递后台任务，适合组权限变化、CMDB 批量同步等场景。

定时兜底：
  定时扫描即将过期或已过期的规则，清理缓存并修复异常遗漏。
```

当前规模下，优先采用：

```text
同步重算 + 定时兜底
```

后续如果 CMDB 同步量增大，再升级为：

```text
变更事件 + 异步任务队列 + 增量重算
```

### 8.6 组 RoleDataRule 变化的重算耗时估算

当组的 RoleDataRule 发生变化时，需要重算该组下所有成员的 EffectivePermissionCache。以下是基于当前系统规模（见 §8.1）的估算：

**模拟参数：**

| 参数 | 取值 | 依据 |
|---|---|---|
| 组人均应用数 | 10 个 | 每组的承接应用数量 |
| 组 RoleDataRule 数 | 约 40 条 | 10 应用 × 4 环境类型 |
| 组内成员数 | 50 人（上限） | 当前系统规模 |
| 人均个人 RoleDataRule | 约 5 条 | 申请 + 协作 + deny |

**估算结果：**

```text
50 人重算总耗时：约 40 - 100 ms

其中：
  - 读取组 RoleDataRule（~40 行）       : ~0.2 ms
  - 遍历 50 人，每人：
      - 读取个人 RoleDataRule（~5 行）  : ~0.3 ms
      - 内存计算展开（合并规则 → env_id）: ~0.5 ms
      - 删除旧缓存                       : ~0.3 ms
      - 批量写入新缓存（~20 行/人）      : ~0.8 ms
  - 事务提交开销                         : ~2 ms

不同成员规模：
  10 人  → ~20 ms
  50 人  → ~90 ms
  100 人 → ~180 ms
  200 人 → ~360 ms
```

**结论：在当前数据规模下，同步重算完全可以接受，不需要为组权限变更引入异步化。**

即使组达到 200 人，重算也在 400 ms 内完成，API 响应时间仍属正常范围。等到组规模超过 500 人或 CMDB 批量同步频繁触发时，再考虑升级为异步任务队列。

### 8.7 多实例并发与分布式锁

先给结论：**不需要分布式锁。**

原因分析：

EffectivePermissionCache 是**读模型（Read Model）**，不是权限源数据。它的正确性依赖以下性质：

**幂等性（Idempotency）：**
给定同一组 RoleDataRule 源数据，展开结果总是相同的。因此多实例并发重算时，后写入的 Cache 覆盖先写入的，最终状态总是正确的。

```text
T1: Instance A 读取 RoleDataRule（状态 S1）
T2: Instance B 修改 RoleDataRule → 写入新规则（状态 S2）
T3: Instance A 基于 S1 写入 Cache
T4: Instance B 基于 S2 写入 Cache（覆盖 A）
↑ 最终 Cache 处于 S2，正确
```

**读偏斜（Read Skew）分析：**

```text
T1: Instance A 开启事务，读取 RoleDataRule（S1）
T2: Instance B 提交 RoleDataRule 变更 → S2
T3: Instance A 基于 S1 写入 Cache 并提交
T4: 鉴权请求 → 读到 Cache（基于 S1）
```

这有问题吗？没有。因为 S1 是**过去某个时刻的正确状态**，不是错误状态。只是少了 T2 的新增权限——而默认拒绝策略下，**少授权比多授权安全**。等到下一次任意变更触发重算，Cache 就会更新到 S2。

**事务保证：**
事务保证的是 per-user 级别的原子性——一个用户的重算不会出现"只删了一半旧数据"的中间状态：

```python
with transaction.atomic():
    EffectivePermissionCache.objects.filter(user_id=uid).delete()
    EffectivePermissionCache.objects.bulk_create(new_entries)
```

**唯一需要关注的点：**

如果期望**强实时一致性**（权限变更后立即在所有实例生效），那么同步重算 + 数据库事务就已经够了——因为所有实例查询同一个数据库。但如果后续切换到 Redis Cache，则需要考虑缓存失效的广播（如 Redis Pub/Sub 或轮询版本号）。

**最终策略建议：**

```text
1. 数据库缓存阶段（阶段 1）：
   同步重算 + 事务原子性即可，无需分布式锁

2. Redis 缓存阶段（阶段 2）：
   可用 Redis rename 原子替换（见 §8.5），
   结合短 TTL 兜底，仍不需要分布式锁

3. 后续如果出现"必须所有实例同时切换到新 Cache"的强一致性需求，
   再引入分布式锁或版本号协调
```

### 8.4 RoleDataRule 与 EffectivePermissionCache 的使用边界

RoleDataRule 使用场景：

- 权限管理页面展示；
- 我的权限页面展示；
- 权限申请审批通过后写入；
- CMDB 同步组默认权限；
- 排查权限来源；
- 生成或重建 EffectivePermissionCache。

EffectivePermissionCache 使用场景：

- 发布；
- 回滚；
- 查看日志；
- 重启；
- 取消发布；
- 环境配置变更；
- 其他需要校验用户是否能操作某个应用环境的业务接口。

边界原则：

```text
管理和解释权限时使用 RoleDataRule；
业务接口做高频鉴权时使用 EffectivePermissionCache。
```

这样可以避免每个业务接口重复实现规则解析逻辑，也避免不同接口对 deny、过期时间、用户优先级的处理不一致。

### 8.5 Redis 升级方案

当前阶段可以先将 EffectivePermissionCache 存在关系型数据库中，并通过联合索引满足查询。

如果后续鉴权 QPS 提升，或 EffectivePermissionCache 数据量增长到百万级以上且接口延迟开始受影响，可以将读模型同步到 Redis。

推荐优先使用 Redis Set，而不是简单 key-value。

Set 方案：

```text
perm:data:allow:{user_id} = env_id set
perm:data:deny:{user_id}  = env_id set
```

鉴权逻辑：

```text
1. SISMEMBER perm:data:deny:{user_id} env_id
   命中则拒绝

2. SISMEMBER perm:data:allow:{user_id} env_id
   命中则允许

3. 默认拒绝
```

优点：

- 查询简单稳定；
- 单次判断为 O(1)；
- 用户维度清晰，重算某个用户时只需要替换该用户的 Set；
- deny 和 allow 分开存储，优先级明确；
- 适合当前 env_id 数量不极端、用户数量可控的场景。

更新策略：

```text
重算某个用户权限时：
  1. 生成新的 allow/deny env_id 集合
  2. 写入临时 key
  3. 使用 rename 原子替换正式 key
  4. 设置合理 TTL 或版本号
```

示例：

```text
perm:data:allow:{user_id}:tmp
perm:data:deny:{user_id}:tmp
rename -> perm:data:allow:{user_id}
rename -> perm:data:deny:{user_id}
```

如果需要进一步减少内存，可以评估 Bitmap：

```text
perm:data:allow:bitmap:{user_id}
perm:data:deny:bitmap:{user_id}
```

Bitmap 适合：

- `env_id` 可以映射为连续整数；
- 用户数量较多；
- 每个用户可访问的环境较多；
- 内存压力明显。

但 Bitmap 可读性和排错体验不如 Set，需要额外维护 `env_id -> offset` 映射。当前规模下不建议优先使用。

最终推荐演进路径：

```text
阶段 1：RoleDataRule + 数据库 EffectivePermissionCache
阶段 2：数据库 EffectivePermissionCache + Redis Set 加速
阶段 3：在数据量很大且 env_id 可连续映射时，再评估 Redis Bitmap
```

---

## 9. 同步与重算机制

以下变化需要触发有效权限重算：

- CMDB 同步组应用归属变化；
- CMDB 同步应用环境新增或删除；
- 用户入组、离组；
- 用户申请权限审批通过；
- 组长设置用户 deny；
- 跨组协作授权创建、变更、到期；
- Role 功能权限模板变更。

重算策略：

```text
组 RoleDataRule 变化：
  重算该组下所有成员的 EffectivePermissionCache
  └─ 耗时估算：50 人约 90 ms，200 人约 360 ms（详见 §8.6）
  └─ 安全保证：事务原子性 + 幂等性，无需分布式锁（详见 §8.7）

User RoleDataRule 变化：
  只重算该用户的 EffectivePermissionCache

应用环境变化：
  找到影响该 app_id/env_type 的规则，重算相关用户

用户入组/离组：
  重算该用户
  └─ 重算时：Group Role 来自新组，User Role（含 cross_group 协作权限）保持不变
  └─ 效果：原组 own_group 权限自动清理，跨组协作权限保留（详见 §5.1）
```

重算方式决策：

| 场景 | 推荐方式 | 原因 |
|---|---|---|
| 用户个人权限变更（申请审批、deny、入组/离组） | **同步重算** | 影响 1 人，耗时 < 5 ms |
| 组 RoleDataRule 变化（≤ 50 人） | **同步重算** | 耗时约 90 ms，可接受 |
| 组 RoleDataRule 变化（50-200 人） | **同步重算** | 耗时约 360 ms，仍可接受 |
| CMDB 批量同步（波及多个组） | **同步重算**（逐组） | 或升级为异步任务队列 |
| 后续数据量扩大后 | **变更事件 + 增量重算** | 避免批量全量扫描 |

安全保证：

- **事务原子性**：每个用户的重算在单个事务内完成 DELETE + INSERT，不会出现中间状态；
- **幂等性**：给定相同 RoleDataRule 源数据，重算结果相同。多实例并发时后写入覆盖先写入，最终一致；
- **兜底机制**：定时任务扫描异常遗漏，确保缓存与源数据一致。

---

## 10. 页面与接口设计

### 10.1 组织权限

组织权限页面展示：

- 组织树；
- 最小承接组详情；
- 组成员；
- 组 Role 的功能权限；
- 组 Role 的数据权限；
- 用户继承组权限和个人权限后的有效权限。

数据权限展示建议按：

```text
业务线 -> 承接组 -> 应用 -> 环境类型 -> 环境实例
```

### 10.2 我的权限

我的权限页面分为：

- 功能权限；
- 数据权限。

数据权限支持筛选：

- 全部；
- 组内权限；
- 跨组协作；
- 临时权限；
- 即将过期；
- 明确拒绝。

### 10.3 权限申请

数据权限申请表单：

- 选择应用；
- 选择环境类型；
- 选择具体环境实例，或选择该类型下全部环境；
- 选择授权有效期，跨组协作必须填写；
- 填写申请原因。

审批通过后：

- 写入用户专属 Role 对应的 RoleDataRule；
- 触发用户 EffectivePermissionCache 重算。

### 10.4 权限审批

审批链路按环境类型确定：

```python
APPROVAL_CHAINS = {
    "dev": [],
    "test": ["app_owner"],
    "staging": ["app_owner", "group_owner"],
    "prod": ["app_owner", "group_owner", "security"],
}
```

跨组协作授权至少需要目标应用所属组负责人审批。

---

## 11. 实施计划

### 阶段一：模型调整

| 序号 | 任务 |
|---|---|
| 1.1 | Role 增加 `owner_type`，确认 Group/User 与 Role 的专属绑定关系 |
| 1.2 | Group 增加 `role_id` |
| 1.3 | User 增加 `role_id` |
| 1.4 | 新建 `RoleDataRule` |
| 1.5 | 新建 `EffectivePermissionCache` |
| 1.6 | 生成并验证数据库迁移 |

### 阶段二：CMDB/种子数据同步

| 序号 | 任务 |
|---|---|
| 2.1 | 初始化时为每个最小承接组创建专属 Group Role |
| 2.2 | 初始化时为每个用户创建空白 User Role |
| 2.3 | 为 Group Role 写入基础功能权限模板 |
| 2.4 | 根据 CMDB 应用归属为 Group Role 写入默认 dev 数据规则 |
| 2.5 | 应用新增时为所属组补充默认 RoleDataRule |
| 2.6 | 环境新增时触发相关有效权限重算 |

### 阶段三：权限计算与缓存

| 序号 | 任务 |
|---|---|
| 3.1 | 实现 `has_function_permission` |
| 3.2 | 实现 RoleDataRule 匹配函数 |
| 3.3 | 实现 `has_data_permission` |
| 3.4 | 实现 `can(user, action, env_id)` |
| 3.5 | 实现 EffectivePermissionCache 展开逻辑 |
| 3.6 | 接入发布、回滚、日志等后端接口 |

### 阶段四：权限申请与审批

| 序号 | 任务 |
|---|---|
| 4.1 | 新建权限申请模型 |
| 4.2 | 新建审批节点模型 |
| 4.3 | 实现数据权限申请接口 |
| 4.4 | 实现审批链路生成 |
| 4.5 | 审批通过后写入 User RoleDataRule |
| 4.6 | 审批通过后重算用户 EffectivePermissionCache |

### 阶段五：前端页面调整

| 序号 | 任务 |
|---|---|
| 5.1 | 重构组织权限页面 |
| 5.2 | 重构我的权限页面 |
| 5.3 | 新增权限申请页面 |
| 5.4 | 新增权限审批页面 |
| 5.5 | 前端展示按应用、环境类型、环境实例分组 |

### 阶段六：测试与验证

重点测试：

- 用户只拥有 `app-1/dev` 和 `app-2/prod` 时，不应拥有 `app-1/prod`；
- 组默认 dev 权限可正确继承；
- 用户申请 `test1-test4` 后，不应获得 `test5-test20`；
- User Deny 覆盖 User Allow 和 Group Allow；
- 跨组协作权限到期后失效；
- 新增应用后所属组默认 dev 权限生效；
- 所有敏感接口后端强制鉴权。

---

## 12. 面试表达建议

可以这样描述本次优化：

> 原系统中功能权限和数据权限都挂在 Role 上，这是当时真实项目的历史实现。它的问题不是 Role 这个载体本身，而是数据权限把 app_ids 和 env_ids 分开存储，运行时容易形成笛卡尔积误授权。  
>  
> 我在重构时没有引入过重的通用 IAM，而是在保留专属 Role 模型的基础上，把数据权限改造成以应用为原子单位的 RoleDataRule。每条规则只描述一个应用下某类环境的授权范围，并通过 `is_all_envs`、`allow_env_ids`、`deny_env_ids` 表达批量授权和精确例外。  
>  
> 同时，为了避免高频发布链路每次解析规则，系统会将 RoleDataRule 展开成用户维度的 EffectivePermissionCache。这样既保证权限来源清晰可查，又保证运行时鉴权只需要按 `user_id + app_id + env_id` 快速判断。

---

## 13. 最终收益

- 修复 `app_ids * env_ids` 笛卡尔积误授权；
- 保留真实项目中 Role 承载权限的实现方式；
- 数据权限规则更直观，按应用即可排查；
- 组默认权限、用户独立权限、跨组协作、临时授权、明确拒绝都能表达；
- 高频鉴权路径稳定；
- 数据规模在当前业务体量下可控；
- 方案足够真实，不会显得像为了 Demo 额外虚构一个复杂权限中心。
