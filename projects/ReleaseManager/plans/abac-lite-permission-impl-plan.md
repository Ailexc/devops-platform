# ABAC-Lite 权限架构实现计划

> 文档版本: v2.0
> 最后更新: 2026-07-25
> 目标: 在数据权限基础上，以统一策略模型实现组织可见范围控制 + 操作权限守卫

---

## 目录

1. [背景与目标](#1-背景与目标)
2. [架构设计](#2-架构设计)
3. [核心模块详解](#3-核心模块详解)
   - [3.1 模块目录结构](#31-模块目录结构)
   - [3.2 PAP: 声明式策略定义](#32-pap-声明式策略定义)
   - [3.3 PIP: 原子检查器](#33-pip-原子检查器)
   - [3.4 PDP: 决策引擎](#34-pdp-决策引擎)
   - [3.5 PEP: 统一守卫装饰器](#35-pep-统一守卫装饰器)
   - [3.6 filter_org_tree](#36-filter_org_tree)
4. [后端 API 改造清单](#4-后端-api-改造清单)
5. [前端改造清单](#5-前端改造清单)
6. [种子数据调整](#6-种子数据调整)
7. [实施步骤与计划](#7-实施步骤与计划)
8. [风险与注意事项](#8-风险与注意事项)

---

## 1. 背景与目标

### 1.1 背景

当前系统经历了三代权限模型演进：

| 版本 | 方案 | 问题 |
|------|------|------|
| v1 | 经典 RBAC：角色 + 权限点 | 权限点爆炸，几百个 API 手动勾选，漏配导致报错 |
| v2 | 权限模板：角色 + 模板 + 权限点 | 前端配置简化，后端模板解析复杂，灵活度不足 |
| v3（当前）| 纯数据权限：去掉功能权限点 | 所有菜单可见，按数据范围管控操作，但缺少按钮级精细化控制 |

### 1.2 核心诉求

1. **组织树可见范围** — 不同角色的用户只能看到自己管辖范围内的组织架构
2. **操作权限守卫** — 后端 API 有统一的鉴权拦截，防止越权操作
3. **按钮级精细化控制** — 特定模块（如权限管理）按上下文动态显示/隐藏操作按钮
4. **避免权限点爆炸** — 不引入"用户-权限点"的静态映射表

### 1.3 设计原则

```
1. 只问「用户在某个资源上能否做某个操作」，不问「用户有哪些权限点」
2. 权限判定 = 当前用户属性 + 目标资源属性 + 操作类型 → 允许/拒绝
3. "发起" ≠ "生效"：分享/申请等操作走审批流，普通成员也可发起
4. 组织树全量展示，不搞"躲躲藏藏"——后端保证不越权即可
5. 前端控制为 UX 优化（按钮禁用+提示），后端守卫为安全底线
6. 复用已有的组织关系模型，不引入新数据表（除非必要）
```

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端（React + Ant Design）                    │
│                                                                     │
│  资源鉴权查询 ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │      │
│  │ 组织树渲染      │  │ 详情面板       │  │ 操作按钮       │  │      │
│  │ · 全量展示      │  │ · accessible  │  │ · disabled     │  │      │
│  │ · accessible   │  │   ↓ 正常显示  │  │   + tooltip    │  │      │
│  │ · available_   │  │ · !accessible │  │ · 后端 403 兜底 │  │      │
│  │   actions      │  │   ↓ 无权提示  │  │                │  │      │
│  └────────────────┘  └────────────────┘  └────────────────┘  │      │
│                          │                                     │      │
└──────────────────────────┼─────────────────────────────────────┘      │
                           │ HTTP Request                               │
                           ▼                                             │
┌─────────────────────────────────────────────────────────────────────┐  │
│                        后端（Django + DRF）                          │  │
│                                                                     │  │
│  ┌─────────────┐  ┌──────────────────────────────────────────────┐  │  │
│  │ ① JWT 认证  │  │  ② PEP（Policy Enforcement Point）           │  │  │
│  └─────────────┘  │  @require_permission 装饰器                  │  │  │
│                   │  → 拦截请求，调用 PDP 决策                    │  │  │
│                   └──────────────────────┬───────────────────────┘  │  │
│                                          │                          │  │
│                   ┌──────────────────────▼───────────────────────┐  │  │
│                   │  ③ PDP（Policy Decision Point）              │  │  │
│                   │  PolicyDecisionPoint 类                      │  │  │
│                   │  · evaluate() → allow/deny                   │  │  │
│                   │  · get_available_actions() → list             │  │  │
│                   └──────┬───────────────────────┬───────────────┘  │  │
│                          │                       │                  │  │
│              ┌───────────▼──────┐     ┌──────────▼───────────┐     │  │
│              │ ④ PAP 策略定义   │     │ ⑤ PIP 属性源         │     │  │
│              │ Policy 子类      │     │ BaseChecker 子类     │     │  │
│              │ + Rule 声明式规则 │     │ + Django ORM         │     │  │
│              └──────────────────┘     └──────────────────────┘     │  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心分层

```
backend/apps/authz/access_control/
├── __init__.py          # 对外暴露 check_user_can(), get_user_org_scope()
├── pap/                 # Policy Administration Point — 策略定义层
│   ├── __init__.py
│   ├── base.py          # PolicyMeta 元类、Rule 描述符、PolicyRegistry
│   └── policies.py      # 具体的策略子类（GroupManagePolicy, GroupViewPolicy...）
├── pip/                 # Policy Information Point — 属性/检查器层
│   ├── __init__.py
│   ├── base.py          # BaseChecker 基类、组合检查器（_OrChecker 等）
│   └── checkers.py      # 具体的检查器子类（IsGroupLeader, IsGroupMember...）
├── pdp/                 # Policy Decision Point — 决策引擎层
│   ├── __init__.py
│   └── engine.py        # PolicyDecisionPoint 类
└── pep/                 # Policy Enforcement Point — 守卫执行层
    ├── __init__.py
    └── decorators.py    # @require_permission 装饰器
```

### 2.3 核心概念：资源（Resource）

```
Resource = (resource_type, resource_id)

预定义的资源类型:
┌────────────────┬──────────────────────────────────┬─────────────────────┐
│ resource_type  │ 含义                             │ 对应模型            │
├────────────────┼──────────────────────────────────┼─────────────────────┤
│ business_line  │ 业务线                           │ BusinessLine        │
│ group          │ 组织组                           │ Group               │
│ user           │ 用户                             │ User                │
│ app            │ 应用                             │ Application         │
│ release        │ 发布单                           │ Release             │
│ environment    │ 环境                             │ Environment         │
└────────────────┴──────────────────────────────────┴─────────────────────┘
```

### 2.4 核心概念：操作（Action）

```
Action 是字符串标识符，定义在 Policy 子类的 action 属性中。

当前预定义:
┌────────────────┬─────────────────────────────────────────────────────┐
│ action         │ 含义                                                │
├────────────────┼─────────────────────────────────────────────────────┤
│ manage         │ 管理资源（增删改成员、调整权限、修改配置等）         │
│ view           │ 查看资源详情                                        │
│ share          │ 发起协作分享（走审批流）                             │
│ apply          │ 发起权限申请（走审批流）                             │
│ revoke         │ 回收协作权限                                        │
│ edit           │ 编辑资源属性                                        │
│ delete         │ 删除资源                                            │
└────────────────┴─────────────────────────────────────────────────────┘

注意: action 不存数据库，不绑定用户，只出现在策略定义代码中。
运行时通过 PDP 实时计算"当前用户 → 某资源 → 能否执行某 action"。
```

---

## 3. 核心模块详解

### 3.1 模块目录结构

```
backend/apps/authz/access_control/
├── __init__.py
│
├── pap/                    # ── Policy Administration Point ──
│   ├── __init__.py
│   ├── base.py             # PolicyMeta 元类, Rule 描述符, PolicyRegistry
│   └── policies.py         # 声明式策略定义（子类继承 Policy）
│
├── pip/                    # ── Policy Information Point ──
│   ├── __init__.py
│   ├── base.py             # BaseChecker 基类, _OrChecker/_AndChecker/_NotChecker
│   └── checkers.py         # 具体检查器（继承 BaseChecker）
│
├── pdp/                    # ── Policy Decision Point ──
│   ├── __init__.py
│   └── engine.py           # PolicyDecisionPoint 类
│
└── pep/                    # ── Policy Enforcement Point ──
    ├── __init__.py
    └── decorators.py       # @require_permission 装饰器
```

### 3.2 PAP: 声明式策略定义

**设计思想（仿 DRF Serializer）：**

DRF Serializer 通过元类自动收集 `fields`，我们从同样的思路——`PolicyMeta` 元类在子类定义时自动收集类体中的 `Rule` 实例，注册到全局 `PolicyRegistry`。

#### 元类与描述符（`pap/base.py`）

```python
class PolicyMeta(type):
    """元类: 在子类定义时自动收集 Rule 并注册到全局注册表"""
    
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if name == "Policy":
            return cls  # 跳过基类
        
        # 从类属性中收集 Rule 描述符实例
        rules = []
        for attr_name, attr_val in attrs.items():
            if isinstance(attr_val, Rule):
                attr_val._name = attr_name
                rules.append(attr_val)
        
        cls._rules = rules
        cls._id = getattr(cls, "id", name)
        PolicyRegistry.register(cls)
        return cls


class Rule:
    """声明式规则描述符 — 类似 DRF 的 Field"""
    
    def __init__(self, effect: str, checker: "BaseChecker", reason: str = ""):
        self.effect = effect       # "allow" | "deny"
        self.checker = checker     # BaseChecker 实例（或组合）
        self.reason = reason
        self._name = ""            # 自动填充


class PolicyRegistry:
    """全局策略注册表"""
    _registry = {}
    
    @classmethod
    def register(cls, policy_cls):
        key = (policy_cls.resource_type, policy_cls.action)
        cls._registry[key] = policy_cls
    
    @classmethod
    def get(cls, resource_type, action):
        return cls._registry.get((resource_type, action))
    
    @classmethod
    def get_by_resource_type(cls, resource_type):
        return [p for k, p in cls._registry.items() if k[0] == resource_type]
```

#### 基类 `Policy`（`pap/base.py`）

```python
class Policy(metaclass=PolicyMeta):
    """策略基类 — 所有策略定义须继承此类"""
    
    id: str = ""
    resource_type: str = ""
    action: str = ""
    title: str = ""
    description: str = ""
    default_effect: str = "deny"
    
    @classmethod
    def get_rules(cls):
        return cls._rules
    
    @classmethod
    def get_id(cls):
        return cls._id
```

#### 具体策略（`pap/policies.py`）

```python
class GroupManagePolicy(Policy):
    """组管理权限 — 增删改成员、调整权限等"""
    id = "group_manage"
    resource_type = "group"
    action = "manage"
    title = "组管理"
    description = "谁能管理一个组的成员和配置"
    default_effect = "deny"
    
    deny_admin   = Rule("deny",  PIP.IsAuditAdmin,  "审计管理员不可操作")
    allow_leader = Rule("allow", PIP.IsGroupLeader,  "组负责人可管理本组")
    allow_bl     = Rule("allow", PIP.IsBlLeader,     "业务线负责人可管理下属组")


class GroupViewPolicy(Policy):
    """组查看权限"""
    id = "group_view"
    resource_type = "group"
    action = "view"
    title = "组查看"
    default_effect = "deny"
    
    allow_admin  = Rule("allow", PIP.IsAuditAdmin,   "审计管理员全量可见")
    allow_leader = Rule("allow", PIP.IsGroupLeader,   "组负责人可见")
    allow_bl     = Rule("allow", PIP.IsBlLeader,      "业务线负责人可见")
    allow_member = Rule("allow", PIP.IsGroupMember,   "组成员可见")


class GroupSharePolicy(Policy):
    """分享协作应用 — 走审批流"""
    id = "group_share"
    resource_type = "group"
    action = "share"
    title = "分享协作"
    description = "将本组负责的应用分享给其他组（发起审批）"
    default_effect = "deny"
    
    allow_member = Rule("allow", PIP.IsGroupMember,  "组成员可发起协作申请")


class GroupApplyPolicy(Policy):
    """申请权限 — 走审批流"""
    id = "group_apply"
    resource_type = "group"
    action = "apply"
    title = "权限申请"
    description = "发起权限申请（走审批流）"
    default_effect = "deny"
    
    allow_any    = Rule("allow", PIP.IsAuthenticated, "已认证用户可申请")


class GroupRevokePolicy(Policy):
    """回收协作权限"""
    id = "group_revoke"
    resource_type = "group"
    action = "revoke"
    title = "回收协作"
    description = "回收分享出去的协作权限"
    default_effect = "deny"
    
    deny_admin   = Rule("deny",  PIP.IsAuditAdmin,   "审计管理员不可操作")
    allow_member = Rule("allow", PIP.IsGroupMember,   "组成员可发起回收")
    allow_leader = Rule("allow", PIP.IsGroupLeader,   "组负责人可直接回收")
```

### 3.3 PIP: 原子检查器

**设计思想：**

每个检查器是 `BaseChecker` 的子类，只需实现：
- `id` — 唯一标识符
- `description` — 人类可读描述
- `check(user, resource)` — 返回 bool

支持 `|`（或）、`&`（与）、`~`（非）操作符组合。

#### 基类（`pip/base.py`）

```python
class BaseChecker:
    """原子检查器基类"""
    
    id: str = ""
    description: str = ""
    
    def check(self, user, resource) -> bool:
        raise NotImplementedError
    
    def __or__(self, other):
        return _OrChecker(self, other)
    
    def __and__(self, other):
        return _AndChecker(self, other)
    
    def __invert__(self):
        return _NotChecker(self)


class _OrChecker(BaseChecker):
    def __init__(self, a, b):
        self._a, self._b = a, b
        self.id = f"({a.id} OR {b.id})"
        self.description = f"{a.description} 或 {b.description}"
    
    def check(self, user, resource) -> bool:
        return self._a.check(user, resource) or self._b.check(user, resource)


class _AndChecker(BaseChecker):
    def __init__(self, a, b):
        self._a, self._b = a, b
        self.id = f"({a.id} AND {b.id})"
        self.description = f"{a.description} 且 {b.description}"
    
    def check(self, user, resource) -> bool:
        return self._a.check(user, resource) and self._b.check(user, resource)


class _NotChecker(BaseChecker):
    def __init__(self, inner):
        self._inner = inner
        self.id = f"(NOT {inner.id})"
        self.description = f"非({inner.description})"
    
    def check(self, user, resource) -> bool:
        return not self._inner.check(user, resource)
```

#### 具体检查器（`pip/checkers.py`）

```python
class IsAuditAdmin(BaseChecker):
    id = "is_audit_admin"
    description = "用户是审计管理员"
    
    def check(self, user, resource) -> bool:
        return user.is_audit_admin


class IsGroupLeader(BaseChecker):
    id = "is_group_leader"
    description = "用户是该 resource 的组负责人"
    
    def check(self, user, resource) -> bool:
        return resource.leader_id == user.id


class IsBlLeader(BaseChecker):
    id = "is_bl_leader"
    description = "用户是该 resource 所属业务线的负责人"
    
    def check(self, user, resource) -> bool:
        return BusinessLine.objects.filter(
            leader=user, groups=resource
        ).exists()


class IsGroupMember(BaseChecker):
    id = "is_group_member"
    description = "用户是该 resource 的组成员"
    
    def check(self, user, resource) -> bool:
        return SubjectMembership.objects.filter(
            user=user, group=resource
        ).exists()


class IsAuthenticated(BaseChecker):
    id = "is_authenticated"
    description = "用户已通过认证"
    
    def check(self, user, resource) -> bool:
        return True
```

#### 组合使用示例

```python
# 在 pap/policies.py 中引用
import pip.checkers as PIP

# 方括号表示"走审批流"的操作
class CrossSharePolicy(Policy):
    resource_type = "group"
    action = "share"
    
    # 组合检查器：是组成员 且 不是审计管理员
    allow_member = Rule("allow", PIP.IsGroupMember & ~PIP.IsAuditAdmin, "组成员可发起分享")
```

### 3.4 PDP: 决策引擎

**设计思想：**

面向对象的 `PolicyDecisionPoint` 类，封装 PDP 的全部逻辑。即使当前只有 `evaluate()` 一个方法，类的存在本身就表达了"这是一个独立决策层"的设计意图。

#### 引擎类（`pdp/engine.py`）

```python
class PolicyDecisionPoint:
    """
    策略决策点 — 核心鉴权引擎
    
    设计说明:
    - 面向对象封装，表达 PDP 层存在
    - 加载 PAP 策略定义 + PIP 检查器 → 实时评估
    - 提供单次评估和批量评估接口
    - 提供 get_available_actions() 供前端直接消费
    """
    
    def __init__(self, policy_registry=None):
        self._registry = policy_registry or PolicyRegistry
        self._model_map = {
            "group": Group,
            "business_line": BusinessLine,
            "user": User,
        }
    
    def evaluate(self, user, resource_type, resource_id, action) -> bool:
        """
        评估：用户能否对某个资源执行某个操作
        
        流程:
        1. 按 (resource_type, action) 查找策略定义
        2. 加载资源实例
        3. 逐条规则评估（有序，命中即返回）
        4. 无规则命中则返回 default_effect
        """
        # 1. 查找策略
        policy_cls = self._registry.get(resource_type, action)
        if not policy_cls:
            return False
        
        # 2. 加载资源
        resource = self._load_resource(resource_type, resource_id)
        if resource is None:
            return False
        
        # 3. 逐规则评估
        for rule in policy_cls.get_rules():
            if rule.checker.check(user, resource):
                return rule.effect == "allow"
        
        # 4. 默认
        return policy_cls.default_effect == "allow"
    
    def evaluate_batch(self, user, checks: list) -> dict:
        """
        批量评估
        
        checks: [
            {"type": "group", "id": 3, "action": "manage"},
            {"type": "app",  "id": 5, "action": "edit"},
        ]
        返回: {"group:3:manage": True, "app:5:edit": False}
        """
        result = {}
        for check in checks:
            key = f"{check['type']}:{check['id']}:{check['action']}"
            result[key] = self.evaluate(
                user, check["type"], check["id"], check["action"]
            )
        return result
    
    def get_available_actions(self, user, resource_type, resource_id) -> list:
        """
        获取用户在某个资源上所有可用的操作列表
        
        这是前端树节点渲染的核心接口——返回当前节点可显示的按钮列表。
        """
        available = []
        for policy_cls in self._registry.get_by_resource_type(resource_type):
            if self.evaluate(user, resource_type, resource_id, policy_cls.action):
                available.append(policy_cls.action)
        return available
    
    def _load_resource(self, resource_type, resource_id):
        model = self._model_map.get(resource_type)
        if not model:
            return None
        try:
            return model.objects.get(id=resource_id)
        except model.DoesNotExist:
            return None
```

### 3.5 PEP: 统一守卫装饰器

```python
# pep/decorators.py

# 全局 PDP 实例（单例）
_pdp = PolicyDecisionPoint()


def require_permission(resource_type, action):
    """
    装饰器：要求当前用户对指定资源拥有指定操作权限。
    
    用法:
        @api_view(['POST'])
        @require_permission('group', 'manage')
        def add_member(request, group_id):
            ...
    
    参数提取约定:
        - resource_type='group'         → 从 kwargs 取 group_id
        - resource_type='business_line' → 从 kwargs 取 bl_id / business_line_id
        - resource_type='user'          → 从 kwargs 取 user_id
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            resource_id = _extract_resource_id(resource_type, kwargs)
            if resource_id is None:
                return Response(
                    {"code": 400, "message": "缺少资源ID"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            if not _pdp.evaluate(request.user, resource_type, resource_id, action):
                return Response(
                    {
                        "code": 403,
                        "message": "您没有权限对当前资源执行此操作",
                        "error_code": "PERMISSION_DENIED",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def _extract_resource_id(resource_type, kwargs):
    """从 kwargs 中自动提取资源 ID"""
    key_map = {
        "group":          ["group_id"],
        "business_line":  ["bl_id", "business_line_id"],
        "user":           ["user_id"],
        "app":            ["app_id"],
        "environment":    ["env_id", "environment_id"],
    }
    for key in key_map.get(resource_type, []):
        if key in kwargs:
            return kwargs[key]
    return None
```

### 3.6 `annotate_org_tree()` 与 `get_user_org_scope()`

**核心改动：组织树全量展示，不过滤。** 后端只做两件事：
1. 判断每个节点对当前用户是否 `accessible`（可访问详情）
2. 对 `accessible` 的节点附加 `available_actions`

不可访问的节点仍然出现在树中，但点击后右侧显示"无权查看"提示。

#### `get_user_org_scope(user) → dict`

```python
def get_user_org_scope(user):
    """
    返回用户组织可见/可管理范围。
    
    返回:
    {
        'is_audit_admin': bool,
        'accessible_group_ids': set | "all",      # 可查看详情的组
        'accessible_bl_ids': set | "all",         # 可查看详情的业务线
        'manageable_group_ids': set | "all",      # 可管理的组
        'is_business_line_leader': bool,
        'is_group_leader': bool,
    }
    
    审计管理员: 全部 accessible, manageable 为空
    """
    if user.is_audit_admin:
        return {
            "is_audit_admin": True,
            "accessible_bl_ids": "all",
            "accessible_group_ids": "all",
            "manageable_group_ids": set(),
            "is_business_line_leader": False,
            "is_group_leader": False,
        }
    
    accessible_bl_ids = set()
    accessible_group_ids = set()
    manageable_group_ids = set()
    
    # 业务线负责人 → 该业务线下全部 accessible + manageable
    for bl in BusinessLine.objects.filter(leader=user):
        accessible_bl_ids.add(bl.id)
        group_ids = list(Group.objects.filter(business_line=bl).values_list("id", flat=True))
        accessible_group_ids.update(group_ids)
        manageable_group_ids.update(group_ids)
    
    # 组负责人 → 本组 accessible + manageable
    for g in Group.objects.filter(leader=user):
        accessible_group_ids.add(g.id)
        manageable_group_ids.add(g.id)
        accessible_bl_ids.add(g.business_line_id)
    
    # 普通成员 → 所属组 accessible（不可 manage）
    for m in SubjectMembership.objects.filter(user=user).select_related("group"):
        accessible_group_ids.add(m.group_id)
        accessible_bl_ids.add(m.group.business_line_id)
    
    return {
        "is_audit_admin": False,
        "accessible_bl_ids": accessible_bl_ids,
        "accessible_group_ids": accessible_group_ids,
        "manageable_group_ids": manageable_group_ids,
        "is_business_line_leader": BusinessLine.objects.filter(leader=user).exists(),
        "is_group_leader": Group.objects.filter(leader=user).exists(),
    }
```

#### `annotate_org_tree(user, tree_nodes) → list`

```python
def annotate_org_tree(user, tree_nodes):
    """
    注解组织树（不过滤，全量展示）:
    1. 为每个节点附加 accessible: bool
    2. 为 accessible 的节点附加 available_actions: list
    
    前端据此决定:
    - accessible=false → 右侧显示"无权查看"
    - accessible=true → 正常渲染详情 + 操作按钮
    """
    scope = get_user_org_scope(user)
    pdp = PolicyDecisionPoint()
    
    def _is_accessible(node):
        if scope["accessible_bl_ids"] == "all" or scope["accessible_group_ids"] == "all":
            return True
        if node["type"] == "business_line":
            return node["id"] in scope["accessible_bl_ids"]
        if node["type"] == "group":
            return node["id"] in scope["accessible_group_ids"]
        if node["type"] == "user":
            # 用户节点跟随父组（由父组递归判断）
            return True
        return False
    
    def _annotate_node(node):
        new_node = {**node}
        accessible = _is_accessible(node)
        new_node["accessible"] = accessible
        
        if accessible:
            new_node["available_actions"] = pdp.get_available_actions(
                user, node["type"], node["id"]
            )
        else:
            new_node["available_actions"] = []
        
        if node.get("children"):
            new_node["children"] = [_annotate_node(c) for c in node["children"]]
        
        return new_node
    
    return [_annotate_node(n) for n in tree_nodes]
```

#### `__init__.py` 对外暴露

```python
# access_control/__init__.py

from .pdp.engine import PolicyDecisionPoint
from .pep.decorators import require_permission

# 全局 PDP 单例
_pdp = PolicyDecisionPoint()

def check_user_can(user, resource_type, resource_id, action) -> bool:
    """统一鉴权入口（便利函数）"""
    return _pdp.evaluate(user, resource_type, resource_id, action)

def check_user_can_batch(user, checks: list) -> dict:
    """批量鉴权入口"""
    return _pdp.evaluate_batch(user, checks)

def get_available_actions(user, resource_type, resource_id) -> list:
    """获取可用操作列表"""
    return _pdp.get_available_actions(user, resource_type, resource_id)

def get_user_org_scope(user) -> dict:
    """获取用户访问范围"""
    from .utils import get_user_org_scope as _scope
    return _scope(user)

def annotate_org_tree(user, tree_nodes) -> list:
    """注解组织树"""
    from .utils import annotate_org_tree as _annotate
    return _annotate(user, tree_nodes)
```

### 3.7 新增 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/authz/check-access/` | 单次鉴权查询 |
| `POST` | `/authz/check-access-batch/` | 批量鉴权查询（用于前端按钮可见性） |

### 3.8 数据模型变更

**唯一需要修改的模型字段：**

`User` 模型中的 `is_org_admin` 字段改为 `is_audit_admin`：

| 当前字段 | 改为 | 含义 |
|---------|------|------|
| `is_org_admin = BooleanField()` | `is_audit_admin = BooleanField()` | 审计管理员：全量可见，不可操作 |

其他字段不变。

**无需新增任何数据表。**

---

## 4. 后端 API 改造清单

### 4.1 组织管理 API

| # | API | 当前 | 改造后 |
|---|-----|------|--------|
| 1 | `GET /org/tree/` | 全部返回，无过滤 | 调用 `filter_org_tree()`，节点附加 `available_actions` |
| 2 | `POST /org/groups/{id}/members/` | 无校验 | 加 `@require_permission('group', 'manage')` |
| 3 | `DELETE /org/groups/{id}/members/{uid}` | 无校验 | 同上 |
| 4 | `PATCH /org/groups/{id}/members/{uid}` | 无校验 | 同上 |
| 5 | `PUT /org/groups/{id}/` | 无校验 | 同上 |
| 6 | `PUT /org/business-lines/{id}/` | 无校验 | 加 `@require_permission('business_line', 'manage')` |

### 4.2 权限管理 API

| # | API | 当前 | 改造后 |
|---|-----|------|--------|
| 7 | `GET /authz/groups/{id}/permissions/` | 无校验 | 加 `@require_permission('group', 'view')` |
| 8 | `GET /authz/users/{id}/permissions/` | 无校验 | 加 `@require_permission('user', 'view')` |
| 9 | `POST /authz/data-rules/` | 无校验 | 提取规则中的 group_id，校验 `manage` |
| 10 | `PUT /authz/data-rules/{id}/` | 无校验 | 同上 |
| 11 | `DELETE /authz/data-rules/{id}/` | 无校验 | 同上 |
| 12 | `GET /authz/groups/{id}/permission-adjust-detail/` | 无校验 | 加 `@require_permission('group', 'manage')` |
| 13 | `POST /authz/groups/{id}/permission-adjust-submit/` | 无校验 | 同上 |

---

## 5. 前端改造清单

### 5.1 `orgApi.tree()` 返回结构增强

```typescript
// 当前返回:
interface OrgTreeNode {
  id: number;
  type: 'business_line' | 'group' | 'user';
  name: string;
  children?: OrgTreeNode[];
}

// 改造后:
interface OrgTreeNode {
  id: number;
  type: 'business_line' | 'group' | 'user';
  name: string;
  code?: string;
  leader_name?: string;
  membership_type?: string;
  is_leader?: boolean;
  accessible: boolean;              // 新增：是否有权查看该节点详情
  available_actions: string[];      // 新增：当前用户可在此节点上执行的操作
  children?: OrgTreeNode[];
}
```

### 5.2 节点状态 → UI 渲染矩阵

| 节点状态 | 树中表现 | 点击后详情面板 |
|---------|---------|--------------|
| `accessible=true` + `available_actions` 包含 `manage` | 正常显示 | 显示详情 + 所有操作按钮（禁用+tooltip） |
| `accessible=true` + `available_actions` 不含 `manage` | 正常显示 | 显示详情 + 部分按钮禁用（如管理按钮灰显，提示"仅组负责人可操作"） |
| `accessible=false` | 正常显示（全量展示） | 显示"⛔ 无权查看"占位提示 |

### 5.3 按钮禁用 + 工具提示

不再隐藏按钮，改为 disabled + tooltip：

```typescript
const ACTION_BUTTON_CONFIG: Record<string, {
  label: string;
  icon: ReactNode;
  disabledReason: string;       // 无权时显示的提示文案
  action: () => void;
}> = {
  manage: {
    label: '权限调整',
    icon: <SettingOutlined />,
    disabledReason: '仅组负责人可调整权限，请联系组长',
    action: handleAdjust,
  },
  share: {
    label: '分享协作',
    icon: <ShareAltOutlined />,
    disabledReason: '仅组成员可发起分享',
    action: handleShare,
  },
  apply: {
    label: '申请权限',
    icon: <PlusOutlined />,
    disabledReason: '',
    action: handleApply,
  },
  revoke: {
    label: '回收协作',
    icon: <RollbackOutlined />,
    disabledReason: '仅组成员可回收',
    action: handleRevoke,
  },
};
```

渲染逻辑：

```tsx
{ACTION_BUTTON_CONFIG.map(({ key, config }) => {
  const hasAction = selectedNode.available_actions?.includes(key);
  return (
    <Tooltip key={key} title={!hasAction ? config.disabledReason : undefined}>
      <Button
        icon={config.icon}
        disabled={!hasAction}
        onClick={hasAction ? config.action : undefined}
      >
        {config.label}
      </Button>
    </Tooltip>
  );
})}
```

### 5.4 无权查看占位（`accessible=false` 时）

```tsx
// 在详情面板中:
if (!selectedNode.accessible) {
  return (
    <Card>
      <Empty
        image={<StopOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
        description={
          <span>
            ⛔ 您没有权限查看此{nodeType === 'business_line' ? '业务线' : '组'}的详情
            <br />
            <Text type="secondary">如需访问，请联系相关负责人</Text>
          </span>
        }
      />
    </Card>
  );
}
```

### 5.5 新增：鉴权查询 API

```typescript
authzApi.checkAccess: (data: { type: string; id: number; action: string }) 
  => Promise<{ allowed: boolean }>

authzApi.checkAccessBatch: (data: { checks: Array<{ type: string; id: number; action: string }> })
  => Promise<{ results: Record<string, boolean> }>
```

### 5.6 叶子组件：权限守卫

```tsx
// 通用权限守卫组件（用于按钮级二次校验）
function Can({ type, id, action, children, fallback }: {
  type: string;
  id: number;
  action: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const [allowed, setAllowed] = useState(false);
  
  useEffect(() => {
    authzApi.checkAccess({ type, id, action })
      .then(res => setAllowed(res.allowed))
      .catch(() => setAllowed(false));
  }, [type, id, action]);
  
  return allowed ? <>{children}</> : <>{fallback || null}</>;
}
```

---

## 6. 种子数据调整

### 6.1 设置业务线负责人

当前种子数据已正确设置：

| 业务线 | 负责人 | 状态 |
|--------|--------|------|
| 支付业务线 | 张三 | ✅ |
| 电商业务线 | 钱七 | ✅ |
| 基础平台 | 周九 | ✅ |

### 6.2 设置组负责人

当前种子数据已正确设置：

| 组 | 负责人 | 状态 |
|----|--------|------|
| 支付研发组 | 张三 | ✅ |
| 支付测试组 | 李四 | ✅ |
| 支付架构组 | 李四 | ✅ |
| 电商研发组 | 钱七 | ✅ |
| 电商测试组 | 孙八 | ✅ |
| 平台运维组 | 周九 | ✅ |
| 平台研发组 | 周九 | ✅ |
| 前端组 | 孙八 | ✅ |
| 数据平台组 | 周九 | ✅ |

### 6.3 设置审计管理员

仅通过手动 SQL 设置，无前端/API：

```sql
UPDATE user SET is_audit_admin = 1 WHERE username = 'admin';
```

| 用户 | 状态 |
|------|------|
| admin | `is_audit_admin = True` |
| 其他人 | `is_audit_admin = False` |

---

## 7. 实施步骤与计划

### 阶段一：核心鉴权引擎（后端）

| 步骤 | 文件 | 内容 | 工时 |
|------|------|------|------|
| 1.1 | 创建目录结构 | `access_control/` 下的 `pap/` `pip/` `pdp/` `pep/` | 0.5h |
| 1.2 | `pip/base.py` + `pip/checkers.py` | BaseChecker + 6 个具体检查器 | 1.5h |
| 1.3 | `pap/base.py` | PolicyMeta 元类、Rule 描述符、PolicyRegistry | 1.5h |
| 1.4 | `pap/policies.py` | 5 个策略定义（manage/view/share/apply/revoke） | 1h |
| 1.5 | `pdp/engine.py` | PolicyDecisionPoint 类（evaluate/batch/available_actions） | 1.5h |
| 1.6 | `pep/decorators.py` | @require_permission 装饰器 | 1h |
| 1.7 | `utils.py` | get_user_org_scope() + annotate_org_tree() | 1.5h |
| 1.8 | `__init__.py` | 对外暴露接口 | 0.5h |
| 1.9 | 新增 API | `/authz/check-access/` + `/authz/check-access-batch/` | 1h |
| 1.10 | User 模型字段迁移 | `is_org_admin` → `is_audit_admin` + 生成迁移文件 | 0.5h |

### 阶段二：后端 API 改造

| 步骤 | 内容 | 工时 |
|------|------|------|
| 2.1 | 改造 `org_tree` — 调用 annotate_org_tree() + 全量展示 | 1h |
| 2.2 | 组织管理 API 加守卫（增删改成员、改组信息 × 4） | 1h |
| 2.3 | 权限 API 加守卫（组权限查看、用户权限查看 × 2） | 0.5h |
| 2.4 | 数据规则 API 加守卫（CRUD × 3） | 0.5h |
| 2.5 | 权限调整 API 加守卫（adjust-detail, adjust-submit × 2） | 0.5h |

### 阶段三：前端改造

| 步骤 | 内容 | 工时 |
|------|------|------|
| 3.1 | 扩展 `orgApi.tree()` 类型，增加 `accessible` + `available_actions` | 0.5h |
| 3.2 | 新增 `authzApi.checkAccess()` + `checkAccessBatch()` | 0.5h |
| 3.3 | 详情面板：`accessible=false` 时显示"无权查看"占位 | 1h |
| 3.4 | 操作按钮：改为 disabled + tooltip（不隐藏） | 1.5h |
| 3.5 | 新增 `Can` 权限守卫组件 | 0.5h |
| 3.6 | 端到端联调测试 | 1h |

### 总计划

```
第1天: 阶段一（核心鉴权引擎）→ 可独立测试 PDP
第2天: 阶段二（后端 API 改造）→ 可 curl 验证守卫
第3天: 阶段三（前端改造）+ 联调
总计: 约 3 天 / 17 人时
```

---

## 8. 风险与注意事项

### 8.1 性能考虑

- `get_user_org_scope()` 每次请求调用，但查询量很小
- `get_available_actions()` 会逐策略评估，当前 5 个策略可忽略不计
- 未来策略数 > 20 时，可考虑缓存 `available_actions` 结果

### 8.2 边界情况

| 场景 | 处理方式 |
|------|---------|
| 用户不属于任何组 | 树全量展示，所有节点 `accessible=false` |
| 用户既是业务线负责人又是组负责人 | 取并集，取最大范围 |
| 用户被移除组后 | 下一请求自动重新计算 scope |
| 审计管理员 | 全量 `accessible=true`，`available_actions` 为空 |
| 用户点击 `accessible=false` 的节点 | 前端显示"无权查看"，后端 API 也会返回 403 |
| 新增 action | 新增 Policy 子类 + 注册 checker，无需改动 PDP 引擎 |

### 8.3 不在此次范围内的内容

- ❌ 不改动 JWT 认证逻辑
- ❌ 不改动已有的数据权限计算逻辑（`has_data_permission` 等）
- ❌ 不做其他模块（发布、审批等）的按钮级控制，只做权限管理模块本身
- ❌ 不做"我的权限总览"页面（第 2 层透明化）
- ❌ 不做性能优化/缓存（后续迭代）

### 8.4 后续可扩展方向

1. **前端通用 `Can` 组件** — 推广到其他模块
2. **策略热加载** — 将 Policy 定义存库，支持页面配置
3. **审计日志** — 记录所有 `403 PERMISSION_DENIED` 事件
4. **策略模拟器** — 管理界面可测试"如果用户 X 对资源 Y 做操作 Z 会怎样"

---

## 附录 A：API 响应示例

### 改造后的 `GET /org/tree/`（李四登录）

```json
{
  "code": 200,
  "data": [
    {
      "id": 1, "type": "business_line",
      "name": "支付业务线", "code": "payment",
      "accessible": true,
      "available_actions": [],
      "children": [
        {
          "id": 2, "type": "group",
          "name": "支付研发组", "code": "payment-dev",
          "leader_name": "张三",
          "accessible": false,
          "available_actions": [],
          "children": [
            { "id": 1, "type": "user", "name": "张三", "code": "zhangsan",
              "membership_type": "primary", "is_leader": true,
              "accessible": false, "available_actions": [] },
            { "id": 2, "type": "user", "name": "李四", "code": "lisi",
              "membership_type": "primary", "is_leader": false,
              "accessible": false, "available_actions": [] }
          ]
        },
        {
          "id": 3, "type": "group",
          "name": "支付架构组", "code": "payment-arch",
          "leader_name": "李四",
          "accessible": true,
          "available_actions": ["manage", "share", "apply", "revoke"],
          "children": [
            { "id": 2, "type": "user",
              "name": "李四", "code": "lisi",
              "membership_type": "primary", "is_leader": true,
              "accessible": true, "available_actions": [] },
            { "id": 4, "type": "user",
              "name": "赵六", "code": "zhaoliu",
              "membership_type": "primary", "is_leader": false,
              "accessible": true, "available_actions": [] }
          ]
        },
        {
          "id": 4, "type": "group",
          "name": "支付测试组", "code": "payment-test",
          "leader_name": "李四",
          "accessible": false,
          "available_actions": [],
          "children": []
        }
      ]
    },
    {
      "id": 2, "type": "business_line",
      "name": "电商业务线", "code": "ecommerce",
      "accessible": false,
      "available_actions": [],
      "children": []
    },
    {
      "id": 3, "type": "business_line",
      "name": "基础平台", "code": "platform",
      "accessible": false,
      "available_actions": [],
      "children": []
    }
  ]
}
```

### 改造后的 `GET /org/tree/`（赵六登录）

```json
{
  "code": 200,
  "data": [
    {
      "id": 1, "type": "business_line",
      "name": "支付业务线", "code": "payment",
      "accessible": true,
      "available_actions": [],
      "children": [
        {
          "id": 3, "type": "group",
          "name": "支付架构组", "code": "payment-arch",
          "leader_name": "李四",
          "accessible": true,
          "available_actions": ["share", "apply", "revoke"],
          "children": [
            { "id": 2, "type": "user",
              "name": "李四", "code": "lisi",
              "membership_type": "primary", "is_leader": true,
              "accessible": true, "available_actions": [] },
            { "id": 4, "type": "user",
              "name": "赵六", "code": "zhaoliu",
              "membership_type": "primary", "is_leader": false,
              "accessible": true, "available_actions": [] }
          ]
        },
        {
          "id": 2, "type": "group",
          "name": "支付研发组", "code": "payment-dev",
          "accessible": false,
          "available_actions": [],
          "children": []
        },
        {
          "id": 4, "type": "group",
          "name": "支付测试组", "code": "payment-test",
          "accessible": false,
          "available_actions": [],
          "children": []
        }
      ]
    },
    {
      "id": 2, "type": "business_line",
      "name": "电商业务线", "code": "ecommerce",
      "accessible": false,
      "available_actions": [],
      "children": []
    }
  ]
}
```

### 鉴权 API

```json
// POST /authz/check-access-batch/
// Request:
{
  "checks": [
    {"type": "group", "id": 3, "action": "manage"},
    {"type": "group", "id": 3, "action": "share"},
    {"type": "group", "id": 3, "action": "apply"}
  ]
}

// Response (李四):
{
  "code": 200,
  "data": {
    "group:3:manage": true,
    "group:3:share": true,
    "group:3:apply": true
  }
}

// Response (赵六):
{
  "code": 200,
  "data": {
    "group:3:manage": false,     ← 赵六不可管理
    "group:3:share": true,       ← 但可发起分享
    "group:3:apply": true        ← 可申请权限
  }
}
```

---

## 附录 B：单元测试计划

```python
# tests/test_access_control.py

# ── 检查器测试 ──

def test_is_audit_admin_checker():
    ...

def test_is_group_leader_checker():
    ...

def test_is_group_member_checker():
    ...

def test_is_bl_leader_checker():
    ...

def test_checker_combinator_or():
    """测试 | 组合"""
    ...

def test_checker_combinator_and():
    """测试 & 组合"""
    ...

def test_checker_combinator_not():
    """测试 ~ 组合"""
    ...

# ── PDP 评估测试 ──

def test_audit_admin_can_view_all():
    ...

def test_audit_admin_cannot_manage_anything():
    ...

def test_business_line_leader_can_manage_all_groups_under_bl():
    ...

def test_business_line_leader_cannot_manage_other_bl():
    ...

def test_group_leader_can_manage_own_group():
    ...

def test_regular_member_can_share_and_apply():
    """普通成员可分享/申请（走审批），但不可管理"""
    ...

def test_regular_member_cannot_manage():
    ...

def test_get_available_actions_returns_correct_list():
    ...

def test_deny_by_default():
    ...

# ── 组织范围测试 ──

def test_user_org_scope_audit_admin():
    ...

def test_user_org_scope_bl_leader():
    ...

def test_user_org_scope_group_leader():
    ...

def test_user_org_scope_regular_member():
    ...

def test_annotate_org_tree_sets_accessible_false_for_unrelated_group():
    """无关组 accessible=false"""
    ...

def test_annotate_org_tree_adds_available_actions():
    """可访问节点附加 available_actions"""
    ...

def test_annotate_org_tree_keeps_all_nodes():
    """全量展示，不过滤"""
    ...
```
