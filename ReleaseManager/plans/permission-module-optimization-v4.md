# 权限模块优化计划 v4

## 概述

在 v3 权限模型重构（以应用为原子授权单元）基础上，对组织模型、审批配置、页面交互进行系统性增强，使权限系统具备完整的审批工作流能力和良好的用户体验。

---

## 一、组织模型增强

### 1.1 BusinessLine 模型

| 字段 | 类型 | 说明 |
|------|------|------|
| `leader` | FK → User | 业务线负责人，审批流中作为"业务线负责人"维度的审批人 |

### 1.2 Group 模型

| 字段 | 类型 | 说明 |
|------|------|------|
| `leader` | FK → User | 组负责人，审批流中作为"组负责人"维度的审批人 |

### 1.3 负责人查找逻辑（向上查找）

用户发起权限申请时，系统自动向上查找最近的业务线负责人：
- 从用户所在的归属组出发，向上遍历 `parent_group` 链
- 找到所属 BusinessLine，取 `business_line.leader`
- 若无，则继续向上查找父组的 BusinessLine

```python
def find_business_line_leader(user: User) -> User:
    """从用户出发，向上查找最近的业务线负责人"""
    primary_membership = user.memberships.filter(membership_type='primary').first()
    if not primary_membership:
        return None
    group = primary_membership.group
    # 向上遍历找到业务线
    while group:
        if group.business_line.leader:
            return group.business_line.leader
        group = group.parent_group
    return None
```

---

## 二、审批配置增强（核心设计）

### 2.1 设计目标

当前 `EnvironmentApprovalConfig` 仅支持简单的维度列表 + 每维度审批人数，无法表达：
- 审批流程的有序性（先 A 审批再 B 审批）
- 不同授权范围（本组/跨组）的差异化审批策略
- 条件触发规则（如：跨组 + prod 需要安全审批）
- 审批人的动态解析（指定部门、固定人员、按层级）

### 2.2 新模型设计

```python
class ApprovalFlowTemplate(models.Model):
    """审批流模板 - 可复用的审批流程定义"""
    name = models.CharField(max_length=64, verbose_name="模板名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="模板编码")
    description = models.TextField(blank=True, verbose_name="描述")
    # 审批步骤定义（有序）
    steps = models.JSONField(default=list, verbose_name="审批步骤")
    """
    steps 结构示例:
    [
        {
            "order": 1,
            "name": "应用负责人审批",
            "dimension": "app_owner",       # 审批维度标识
            "approver_resolver": "app_owner", # 审批人解析策略
            "resolver_config": {},           # 解析器配置
            "required_count": 1,             # 所需审批人数
            "timeout_hours": 24,             # 超时时间（小时）
        },
        {
            "order": 2,
            "name": "业务线负责人审批",
            "dimension": "business_line_leader",
            "approver_resolver": "business_line_leader",
            "resolver_config": {},
            "required_count": 1,
            "timeout_hours": 48,
        },
        {
            "order": 3,
            "name": "安全审批",
            "dimension": "security",
            "approver_resolver": "fixed_role",  # 固定角色/人员
            "resolver_config": {
                "role": "security_team",
                "user_ids": []                   # 或指定固定人员
            },
            "required_count": 1,
            "timeout_hours": 24,
        },
    ]
    """
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2.3 审批人解析策略（ApproverResolver）

| 策略标识 | 说明 | 解析逻辑 |
|---------|------|---------|
| `app_owner` | 应用负责人 | 从 Application 模型获取 owner 字段 |
| `group_leader` | 组负责人 | 从用户所在 Group 获取 leader |
| `business_line_leader` | 业务线负责人 | 向上查找最近的 BusinessLine.leader |
| `fixed_user` | 固定人员 | resolver_config 中指定 user_ids |
| `fixed_role` | 固定角色组 | resolver_config 中指定 role，查询该角色所有成员 |
| `parent_group_leader` | 上级组负责人 | 沿 parent_group 链向上查找 |
| `security_team` | 安全团队 | 系统预定义的安全角色组成员 |
| `ops_team` | 运维团队 | 系统预定义的运维角色组成员 |

### 2.4 审批策略配置（替代原 EnvironmentApprovalConfig）

```python
class EnvironmentApprovalConfig(models.Model):
    """环境审批配置 - 按环境类型 + 授权范围配置审批策略"""
    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    grant_scope = models.CharField(
        max_length=16, choices=[("own_group", "本组"), ("cross_group", "跨组协作")],
        verbose_name="授权范围"
    )
    requires_approval = models.BooleanField(default=False, verbose_name="是否需要审批")

    # 关联审批流模板
    flow_template = models.ForeignKey(
        ApprovalFlowTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="审批流模板"
    )

    # 条件规则 - 满足条件时才触发（可选）
    condition_rules = models.JSONField(default=list, blank=True, verbose_name="条件规则")
    """
    condition_rules 示例:
    [
        {"field": "env_type", "operator": "eq", "value": "prod"},
        {"field": "app_tag", "operator": "contains", "value": "core"},
    ]
    """

    priority = models.IntegerField(default=0, verbose_name="优先级")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "env_approval_config"
        unique_together = [("env_type", "grant_scope")]
        verbose_name = "环境审批配置"
```

### 2.5 默认审批策略（建议配置）

#### 本组权限（own_group）

| 环境类型 | 需要审批 | 审批流 |
|---------|---------|--------|
| dev | 否 | 无（默认具备） |
| test | 是 | 应用负责人 → 1人 |
| staging | 是 | 应用负责人(1人) → 业务线负责人(1人) |
| prod | 是 | 应用负责人(1人) → 业务线负责人(1人) → 安全审批(1人) → 运维审批(1人) |

#### 跨组协作（cross_group）

| 环境类型 | 需要审批 | 审批流 |
|---------|---------|--------|
| dev | 是 | 应用负责人(1人) → 业务线负责人(1人) |
| test | 是 | 应用负责人(1人) → 业务线负责人(1人) |
| staging | 是 | 应用负责人(1人) → 业务线负责人(1人) → 安全审批(1人) |
| prod | 是 | 应用负责人(1人) → 业务线负责人(1人) → 安全审批(1人) → 运维审批(1人) |

### 2.6 审批流计算接口

```python
@api_view(['POST'])
def calculate_approval_flow(request):
    """
    根据用户、应用、环境类型、授权范围，动态计算审批流。
    前端提交权限申请时调用此接口，展示审批流程预览。
    
    请求: { app_id, env_type, grant_scope, is_all_envs, env_ids }
    响应: {
        steps: [{ order, name, dimension, approvers: [{id, name}], required_count }],
        total_approvers: number,
        estimated_time: "1-2 个工作日"
    }
    """
```

---

## 三、组织权限树页面优化

### 3.1 页面标题
- 将"组织权限管理"改为"组织权限"

### 3.2 组节点 - 权限规则展示优化

当前问题：组数据权限规则以平铺表格展示，不直观。

优化方案：改为**应用 → 环境**的折叠树形展示：

```
📦 支付核心服务 (payment-core)
  ├─ dev  ✅ 全部环境
  ├─ test ✅ env-3, env-4
  └─ prod ❌ 排除 env-10

📦 用户中心 (user-center) [跨组协作]
  ├─ test ✅ 全部环境
  └─ staging ✅ env-8
```

操作：应用行可点击展开/收起环境详情，每个应用卡片显示环境类型标签。

### 3.3 组节点 - 权限分类展示

分两个 Tab 展示：
- **本组应用权限**：`grant_scope = own_group` 的规则
- **协作应用权限**：`grant_scope = cross_group` 的规则

### 3.4 用户节点 - 权限分类展示

当前问题：组继承权限不分本组/跨组，跨组协作规则被混入"组继承权限"。

优化方案：分三个 Tab 展示：
- **本组继承权限**：`grant_scope = own_group` 的组规则
- **跨组协作权限**：`grant_scope = cross_group` 的组规则
- **个人权限**：User Role 的规则

### 3.5 业务线/组节点 - 负责人信息展示

在业务线节点和组节点的详情卡片中，增加负责人字段展示：
- 业务线节点：显示 `leader` 字段
- 组节点：显示 `leader` 字段，成员列表中将组长标记为"组长"

---

## 四、我的权限页面重构

### 4.1 当前问题

当前"我的权限"页面仅是权限查看，缺少权限申请工作流入口。

### 4.2 重构方案

将"我的权限"改为两个 Tab：

#### Tab 1: 当前权限（保留现有功能）
- 用户基本信息 + 归属组/协作组
- 数据权限规则（本组/跨组/个人 三个子 Tab）
- 每个规则显示有效期，过期规则标红

#### Tab 2: 申请权限（新增，替代原独立申请页）

**步骤 1：选择业务线**
- 默认显示用户所在业务线（向上查找）
- 可切换为其他业务线（下拉选择）
- 显示对应业务线负责人（谁将审批）

**步骤 2：选择应用**
- 根据步骤 1 的业务线，加载该业务线下的应用列表
- 支持搜索

**步骤 3：选择环境和授权范围**
- 环境类型选择（dev/test/staging/prod）
- 全部环境 / 具体环境 **互斥选择**（Switch 控制）
- 授权范围根据选择的应用自动显示（own_group）
- 跨组协作需选择**时间范围**（DatePicker，必填）

**步骤 4：审批流预览**
- 调用后端 `/authz/calculate-approval-flow/` 接口
- 实时展示审批步骤、审批人、预计耗时
- 申请原因填写

**步骤 5：提交**
- 确认信息后提交，创建 PermissionRequest + 对应 Approval 记录

### 4.3 交互流程

```
[选择业务线] → [选择应用] → [选择环境] → [预览审批流] → [填写原因] → [提交]
     ↓               ↓              ↓              ↓
 自动查负责人    过滤应用列表    互斥选择      后端动态计算
```

---

## 五、审批配置页面增强

### 5.1 当前问题

当前审批配置页面仅支持按环境开启/关闭审批 + 简单维度配置，无法：
- 按授权范围（本组/跨组）区分策略
- 配置审批流模板
- 管理审批人解析策略

### 5.2 重构方案

#### 页面布局

```
┌─────────────────────────────────────────────────────┐
│ 审批配置                                             │
├──────────┬──────────────────────────────────────────┤
│          │                                           │
│ 环境类型  │  审批策略列表                             │
│ 卡片列表  │  ┌─────────────────────────────────┐    │
│          │  │ dev · 本组权限                    │    │
│  ┌────┐  │  │ 审批: 关闭                        │    │
│  │dev │  │  │ 编辑                              │    │
│  └────┘  │  ├─────────────────────────────────┤    │
│  ┌────┐  │  │ dev · 跨组协作                    │    │
│  │test│  │  │ 审批: 开启                        │    │
│  └────┘  │  │ 审批流: 跨组基础审批流             │    │
│  ┌────┐  │  │ 编辑                              │    │
│  │stag│  │  ├─────────────────────────────────┤    │
│  └────┘  │  │ test · 本组权限                   │    │
│  ┌────┐  │  │ ...                               │    │
│  │prod│  │  └─────────────────────────────────┘    │
│  └────┘  │                                           │
│          │                                           │
├──────────┴──────────────────────────────────────────┤
│ 审批流模板管理（全局）                                │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 模板名称          │ 步骤数  │ 状态   │ 操作      │ │
│ │ 基础审批流        │ 1      │ 启用   │ 编辑/删除 │ │
│ │ 标准审批流        │ 2      │ 启用   │ 编辑/删除 │ │
│ │ 生产审批流        │ 4      │ 启用   │ 编辑/删除 │ │
│ └─────────────────────────────────────────────────┘ │
│ [+ 新建审批流模板]                                    │
└─────────────────────────────────────────────────────┘
```

#### 审批流模板编辑弹窗

```
┌──────────────────────────────────────────────┐
│ 编辑审批流模板 - 标准审批流                    │
├──────────────────────────────────────────────┤
│ 模板名称: [标准审批流           ]             │
│ 模板编码: [standard_approval    ]             │
│ 描述:     [测试/预发环境标准审批]             │
│                                              │
│ 审批步骤:                                    │
│ ┌──────────────────────────────────────┐    │
│ │ 步骤 1: 应用负责人审批                │    │
│ │   审批人: [应用负责人 ▾]              │    │
│ │   人数:   [1    ]                    │    │
│ │   超时:   [24   ] 小时               │    │
│ │   [删除]                             │    │
│ ├──────────────────────────────────────┤    │
│ │ 步骤 2: 业务线负责人审批              │    │
│ │   审批人: [业务线负责人 ▾]            │    │
│ │   人数:   [1    ]                    │    │
│ │   超时:   [48   ] 小时               │    │
│ │   [删除]                             │    │
│ └──────────────────────────────────────┘    │
│ [+ 添加审批步骤]                             │
│                                              │
│ [取消]  [保存]                               │
└──────────────────────────────────────────────┘
```

---

## 六、审批中心 - 权限审批集成

### 6.1 当前状态

- 审批中心已有基础 Approval 模型，支持 `release` 和 `permission` 两种类型
- 权限申请提交后创建 PermissionRequest 记录
- 审批通过/驳回逻辑在 `authz/views.py` 的 `approve_permission_request` 中
- 但缺少前端"我的待审批"中展示权限审批的入口

### 6.2 优化方案

在审批中心页面增加：
- 审批类型筛选：全部 / 发布审批 / 权限审批
- 权限审批卡片展示：
  - 申请人信息（姓名、归属组）
  - 申请内容（应用、环境类型、授权范围）
  - 审批流状态（当前步骤、已审批步骤）
  - 操作按钮（通过/驳回 + 审批意见）

### 6.3 审批流状态机

```
权限申请提交
    │
    ▼
┌─────────┐  步骤1通过  ┌─────────┐  步骤2通过  ┌─────────┐
│ 步骤1   │ ─────────→ │ 步骤2   │ ─────────→ │ 步骤N   │ ──→ 全部通过
│ 待审批  │            │ 待审批  │            │ 待审批  │
└─────────┘            └─────────┘            └─────────┘
    │ 任一步骤驳回         │                      │
    ▼                     ▼                      ▼
  申请被驳回 ←────────────┴──────────────────────┘
```

---

## 七、实施计划

### 阶段一：后端模型 + 数据迁移（预计 1 天）

| 任务 | 说明 |
|------|------|
| 1.1 | BusinessLine 添加 `leader` 字段 |
| 1.2 | Group 添加 `leader` 字段 |
| 1.3 | 创建 `ApprovalFlowTemplate` 模型 |
| 1.4 | 重构 `EnvironmentApprovalConfig` 模型（添加 `env_type` + `grant_scope` 联合唯一键） |
| 1.5 | 创建数据库迁移文件 |
| 1.6 | 更新 seed 数据（初始化审批流模板 + 默认审批策略） |

### 阶段二：后端 API（预计 1 天）

| 任务 | 说明 |
|------|------|
| 2.1 | 业务线负责人查询接口 |
| 2.2 | 审批流模板 CRUD 接口 |
| 2.3 | 审批策略配置 CRUD 接口（替代原简单的 env 维度配置） |
| 2.4 | 审批流动态计算接口 `/authz/calculate-approval-flow/` |
| 2.5 | 权限申请提交时自动创建 Approval 记录（按审批流步骤） |
| 2.6 | 审批中心 - 权限审批列表 + 审批操作（步骤级） |

### 阶段三：前端页面（预计 1.5 天）

| 任务 | 说明 |
|------|------|
| 3.1 | 组织权限树：标题改为"组织权限"，规则改为应用折叠展示 |
| 3.2 | 组织权限树：组节点分"本组/协作"Tab，用户节点分"本组继承/跨组协作/个人"Tab |
| 3.3 | 组织权限树：业务线/组节点显示负责人信息 |
| 3.4 | 我的权限：重构为 Tab 页（当前权限 + 申请权限） |
| 3.5 | 我的权限 - 申请页：业务线选择 → 应用选择 → 环境选择 → 审批流预览 |
| 3.6 | 审批配置：重构为环境类型 + 授权范围矩阵 + 审批流模板关联 |
| 3.7 | 审批配置：新增审批流模板管理功能 |
| 3.8 | 审批中心：增加权限审批列表展示 + 审批操作 |

### 阶段四：联调测试（预计 0.5 天）

| 任务 | 说明 |
|------|------|
| 4.1 | 完整权限申请 → 审批流 → 审批通过 → 权限生效 链路测试 |
| 4.2 | 多步骤审批流测试（模拟多人审批场景） |
| 4.3 | 审批驳回 + 重新申请测试 |
| 4.4 | 有效期过期权限自动清理测试 |

---

## 八、接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/org/business-lines/` | 业务线列表（含负责人） |
| GET | `/api/v1/org/business-lines/<id>/leader/` | 查询业务线负责人 |
| GET/POST | `/api/v1/authz/approval-flow-templates/` | 审批流模板列表/创建 |
| PUT/DELETE | `/api/v1/authz/approval-flow-templates/<id>/` | 审批流模板编辑/删除 |
| GET/POST | `/api/v1/authz/approval-strategies/` | 审批策略列表/创建 |
| PUT | `/api/v1/authz/approval-strategies/<id>/` | 审批策略编辑 |
| POST | `/api/v1/authz/calculate-approval-flow/` | 动态计算审批流 |
| GET | `/api/v1/approvals/pending/?type=permission` | 我的待审批（权限类） |
| POST | `/api/v1/approvals/<id>/approve-step/` | 审批某步骤通过 |
| POST | `/api/v1/approvals/<id>/reject-step/` | 审批某步骤驳回 |