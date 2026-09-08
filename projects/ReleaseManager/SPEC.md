# 发布系统 Demo — 完整规格说明书 (Spec)

> 文档版本: v1.0
> 最后更新: 2026-07-22

---

## 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)
3. [数据模型设计](#3-数据模型设计)
4. [API 接口设计](#4-api-接口设计)
5. [前端页面设计](#5-前端页面设计)
6. [权限校验设计](#6-权限校验设计)
7. [K8s 集成设计](#7-k8s-集成设计)
8. [Demo 应用设计](#8-demo-应用设计)
9. [种子数据设计](#9-种子数据设计)
10. [实施计划](#10-实施计划)

---

## 1. 项目概述

### 1.1 目标

构建一个功能相对完整的发布系统 Demo，覆盖从应用管理、发布流水线、审批、灰度发布到回滚的全链路流程。通过本地 kind 集群模拟真实 K8s 部署，使用三种语言的 Demo 应用展示发布效果。

### 1.2 核心需求

- 完整的数据模型：业务线、应用、环境、集群、发布单、审批、部署历史等
- 权限模型：组织树（归属组/协作组）+ 个人例外权限，区分功能权限和数据权限
- 发布全链路：创建发布 → 审批 → 部署各环境 → 灰度 → 全量 → 回滚
- K8s 集成：本地 kind 集群，支持滚动更新、灰度发布、蓝绿部署
- 三种 Demo 应用：Python (FastAPI)、Go、Node.js (Express)

### 1.3 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| 后端 | Python 3.11+ / Django 5 + DRF + SimpleJWT | RESTful API |
| 前端 | React 18 + TypeScript + Ant Design 5 + Vite | 中后台管理 |
| 数据库 | SQLite（Demo 零依赖） | 可平滑迁移 PostgreSQL |
| 本地 K8s | kind (Kubernetes in Docker) | 最轻量本地集群 |
| 容器化 | Docker + kind | 所有组件可本地运行 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Web UI (React + Ant Design)                  │
│  登录页 │ 仪表盘 │ 应用管理 │ 发布流水线 │ 审批中心 │ 权限管理 ...  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP REST API (JWT Auth)
┌───────────────────────────────▼─────────────────────────────────────┐
│                      API Server (Django + DRF)                       │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 认证/用户 │ │ 组织管理  │ │ 权限管理  │ │ 应用管理  │ │ 发布引擎  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────┬─────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │       │
│  │ 审批管理  │ │ 部署管理  │ │ 审计日志  │ │ 配置管理  │      │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │       │
│                                                            │       │
│  ┌─────────────────────────────────────────────────────────▼─────┐ │
│  │                    K8s Client (kubernetes.client)              │ │
│  │          Deployment / Service / Ingress / ConfigMap            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │ kubeconfig
┌───────────────────────────────────▼─────────────────────────────────┐
│                    kind Cluster (Kubernetes in Docker)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │ python-app│ │  go-app  │ │ node-app │ │ Nginx Ingress        │  │
│  │ (Deploy)  │ │(Deploy)  │ │(Deploy)  │ │ (流量路由)           │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 项目目录结构

```
release-system-demo/
├── backend/
│   ├── config/                    # Django 项目配置
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── accounts/              # 用户/认证
│   │   │   ├── models.py          # User
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── auth_backend.py    # 自定义 JWT 认证（选择用户登录）
│   │   ├── organizations/         # 组织管理
│   │   │   ├── models.py          # BusinessLine, Department, Group
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── authz/                 # 权限管理
│   │   │   ├── models.py          # Role, Permission, GroupPermission, UserPermission, SubjectMembership
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── permissions.py     # 自定义权限校验类
│   │   ├── infrastructures/       # 基础设施
│   │   │   ├── models.py          # Environment, Cluster, Namespace
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── applications/          # 应用管理
│   │   │   ├── models.py          # Application, AppEnvConfig
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── releases/              # 发布核心
│   │   │   ├── models.py          # Release, ReleaseTask, TaskLog, Artifact
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── pipeline.py        # 流水线状态机
│   │   │   └── deploy_strategy.py # 部署策略（滚动/灰度/蓝绿）
│   │   ├── approvals/             # 审批
│   │   │   ├── models.py          # Approval
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── deployments/           # 部署管理
│   │   │   ├── models.py          # DeployHistory, PodInstance, RollbackRecord
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── k8s_operator.py    # K8s 操作封装
│   │   └── audit/                 # 审计日志
│   │       ├── models.py          # AuditLog
│   │       ├── serializers.py
│   │       ├── views.py
│   │       └── urls.py
│   ├── artifacts/               # 制品管理
│   │   ├── models.py            # Artifact, ArtifactRepository, ArtifactPromotion
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── configs/                 # 配置管理
│   │   ├── models.py            # ConfigTemplate, ConfigVariable, ConfigVariableValue, ConfigRelease
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── config_engine.py     # 配置渲染引擎
│   ├── utils/
│   │   ├── k8s_client.py          # K8s 客户端单例
│   │   └── permissions.py         # 权限校验装饰器/工具函数
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                   # API 调用层
│   │   │   ├── client.ts          # axios 实例 + JWT 拦截器
│   │   │   ├── accounts.ts
│   │   │   ├── organizations.ts
│   │   │   ├── authz.ts
│   │   │   ├── applications.ts
│   │   │   ├── releases.ts
│   │   │   ├── approvals.ts
│   │   │   ├── deployments.ts
│   │   │   └── audit.ts
│   │   ├── components/            # 通用组件
│   │   │   ├── Layout/
│   │   │   │   ├── AppLayout.tsx       # 主布局（侧边栏+头部+内容区）
│   │   │   │   └── Sidebar.tsx         # 侧边栏（根据权限动态渲染菜单）
│   │   │   ├── PermissionTree/
│   │   │   │   ├── OrgTree.tsx         # 组织树组件
│   │   │   │   └── ResourceTree.tsx    # 资源树组件
│   │   │   ├── Pipeline/
│   │   │   │   └── PipelineStage.tsx   # 流水线阶段可视化组件
│   │   │   └── Common/
│   │   │       ├── PermissionGuard.tsx # 权限守卫组件
│   │   │       └── DataScope.tsx       # 数据权限组件
│   │   ├── pages/                 # 页面组件
│   │   │   ├── login/
│   │   │   │   └── index.tsx
│   │   │   ├── dashboard/
│   │   │   │   └── index.tsx
│   │   │   ├── apps/
│   │   │   │   ├── index.tsx          # 应用列表
│   │   │   │   ├── detail.tsx         # 应用详情
│   │   │   │   └── app-env-config.tsx # 环境配置
│   │   │   ├── releases/
│   │   │   │   ├── index.tsx          # 发布列表
│   │   │   │   ├── create.tsx         # 创建发布
│   │   │   │   └── detail.tsx         # 发布流水线详情
│   │   │   ├── approvals/
│   │   │   │   └── index.tsx          # 审批中心
│   │   │   ├── permissions/
│   │   │   │   ├── index.tsx          # 权限管理首页
│   │   │   │   ├── role-manager.tsx   # 角色管理
│   │   │   │   ├── group-permission.tsx # 组权限配置
│   │   │   │   ├── user-permission.tsx  # 用户权限查看
│   │   │   │   └── my-permissions.tsx   # 我的权限(个人中心)
│   │   │   ├── infrastructures/
│   │   │   │   └── index.tsx          # 环境/集群管理
│   │   │   ├── deploy-history/
│   │   │   │   └── index.tsx          # 部署历史
│   │   │   └── audit/
│   │   │       └── index.tsx          # 审计日志
│   │   ├── store/
│   │   │   ├── useAuthStore.ts   # 用户认证状态
│   │   │   └── usePermissionStore.ts  # 权限状态
│   │   ├── router/
│   │   │   └── index.tsx         # 路由配置 + 权限守卫
│   │   ├── utils/
│   │   │   ├── permission.ts     # 前端权限工具函数
│   │   │   └── constants.ts      # 常量定义
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── demo-apps/                    # Demo 应用
│   ├── python/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── go/
│   │   ├── main.go
│   │   ├── go.mod
│   │   └── Dockerfile
│   └── node/
│       ├── app.js
│       ├── package.json
│       └── Dockerfile
├── scripts/                      # 部署脚本
│   ├── setup-kind.sh             # 创建 kind 集群
│   ├── build-demo-images.sh      # 构建 Demo 镜像并导入 kind
│   └── init-db.sh                # 初始化种子数据
├── k8s/                          # K8s 配置模板
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
├── SPEC.md                       # 本规格文档
└── README.md
```

---

## 3. 数据模型设计

### 3.1 组织与权限模块

#### 3.1.1 BusinessLine（业务线）

```python
class BusinessLine(models.Model):
    """业务线"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="业务线名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="业务线编码")
    description = models.TextField(blank=True, verbose_name="描述")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_line"
        ordering = ["sort_order", "id"]
```

#### 3.1.2 Group（组织组）

```python
class Group(models.Model):
    """组织组 - 权限的基本载体"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="组名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="组编码")
    description = models.TextField(blank=True, verbose_name="描述")
    business_line = models.ForeignKey(BusinessLine, on_delete=models.CASCADE, related_name="groups",
                                      verbose_name="所属业务线")
    parent_group = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="child_groups", verbose_name="父组")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "`group`"  # group 是 SQL 保留字
        ordering = ["business_line", "name"]
```

#### 3.1.3 User（用户）

```python
class User(models.Model):
    """用户 - 无密码，Demo 通过选择用户登录"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=32, unique=True, verbose_name="用户名")
    display_name = models.CharField(max_length=64, verbose_name="显示名称")
    email = models.EmailField(max_length=128, blank=True, verbose_name="邮箱")
    avatar_url = models.URLField(blank=True, verbose_name="头像")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user"
```

#### 3.1.4 SubjectMembership（用户与组的关系）

```python
class SubjectMembership(models.Model):
    """用户与组的关系"""
    MEMBERSHIP_TYPES = [
        ('primary', '归属'),
        ('collaborator', '协作'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    membership_type = models.CharField(max_length=16, choices=MEMBERSHIP_TYPES, default='primary',
                                       verbose_name="成员类型")
    # 协作成员可缩小资源范围，归属成员为 None 表示继承组完整范围
    resource_scope = models.JSONField(null=True, blank=True, verbose_name="资源范围限制",
                                      help_text="协作成员可见的资源范围: {\"app_ids\": [1,2,3]}")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "subject_membership"
        unique_together = [("user", "group")]
```

#### 3.1.5 Role（角色）

```python
class Role(models.Model):
    """角色 - 动作集合模板，不是授权主体"""
    ROLE_TYPES = [
        ('admin', '管理员'),
        ('deployer', '发布者'),
        ('release_manager', '发布管理员'),
        ('auditor', '审计员'),
        ('viewer', '观察者'),
        ('app_owner', '应用负责人'),
        ('biz_owner', '业务线负责人'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, verbose_name="角色名称")
    code = models.CharField(max_length=32, unique=True, choices=ROLE_TYPES, verbose_name="角色编码")
    description = models.TextField(blank=True, verbose_name="描述")
    # 角色默认具备的功能权限列表
    permission_codes = models.JSONField(default=list, verbose_name="功能权限编码列表",
                                        help_text="['menu_dashboard', 'page_apps', 'action_deploy', ...]")
    is_system = models.BooleanField(default=False, verbose_name="系统内置")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "role"
```

#### 3.1.6 GroupPermission（组权限分配）

```python
class GroupPermission(models.Model):
    """组权限 - 组在某个资源范围内拥有哪些动作"""
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="permissions")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="+")
    # 资源范围
    business_lines = models.JSONField(default=list, verbose_name="业务线 ID 列表",
                                      help_text="[] 表示无限制")
    app_ids = models.JSONField(default=list, verbose_name="应用 ID 列表",
                               help_text="[] 表示继承业务线下所有应用")
    env_ids = models.JSONField(default=list, verbose_name="环境 ID 列表",
                               help_text="[] 表示所有环境")
    effect = models.CharField(max_length=8, choices=[('allow', '允许'), ('deny', '拒绝')],
                              default='allow')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "group_permission"
```

#### 3.1.7 UserPermission（用户个人例外权限）

```python
class UserPermission(models.Model):
    """用户个人例外权限 - 额外的 allow 或 deny"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="extra_permissions")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="+")
    business_lines = models.JSONField(default=list, verbose_name="业务线 ID 列表")
    app_ids = models.JSONField(default=list, verbose_name="应用 ID 列表")
    env_ids = models.JSONField(default=list, verbose_name="环境 ID 列表")
    effect = models.CharField(max_length=8, choices=[('allow', '允许'), ('deny', '拒绝')],
                              default='allow')
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name="生效时间")
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    source = models.CharField(max_length=32, default='manual', verbose_name="来源",
                              help_text="manual / approval / system")
    source_id = models.CharField(max_length=64, blank=True, verbose_name="来源 ID",
                                 help_text="审批单号等")
    reason = models.TextField(blank=True, verbose_name="原因")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "user_permission"
```

### 3.2 基础设施模块

#### 3.2.1 Environment（环境）

```python
class Environment(models.Model):
    """部署环境"""
    ENV_TYPES = [
        ('dev', '开发'),
        ('test', '测试'),
        ('staging', '预发'),
        ('prod', '生产'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, verbose_name="环境名称")
    code = models.CharField(max_length=16, unique=True, choices=ENV_TYPES, verbose_name="环境编码")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_prod = models.BooleanField(default=False, verbose_name="是否生产环境")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "environment"
        ordering = ["sort_order"]
```

#### 3.2.2 Cluster（K8s 集群）

```python
class Cluster(models.Model):
    """K8s 集群"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="集群名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="集群编码")
    api_server = models.URLField(verbose_name="API Server 地址")
    kubeconfig = models.TextField(blank=True, verbose_name="Kubeconfig 内容")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="clusters")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cluster"
```

#### 3.2.3 K8sNamespace（K8s 命名空间）

```python
class K8sNamespace(models.Model):
    """K8s 命名空间"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="命名空间名称")
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="namespaces")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "k8s_namespace"
        unique_together = [("name", "cluster")]
```

### 3.3 应用管理模块

#### 3.3.1 Application（应用）

```python
class Application(models.Model):
    """应用"""
    LANGUAGES = [
        ('python', 'Python'),
        ('go', 'Go'),
        ('node', 'Node.js'),
        ('java', 'Java'),
        ('other', '其他'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="应用名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="应用编码")
    description = models.TextField(blank=True, verbose_name="描述")
    language = models.CharField(max_length=16, choices=LANGUAGES, verbose_name="开发语言")
    repo_url = models.URLField(blank=True, verbose_name="仓库地址")
    business_line = models.ForeignKey(BusinessLine, on_delete=models.CASCADE, related_name="apps")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="owned_apps",
                              verbose_name="应用负责人")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application"
```

#### 3.3.2 AppEnvConfig（应用环境配置）

```python
class AppEnvConfig(models.Model):
    """应用在各环境下的部署配置"""
    STRATEGIES = [
        ('rolling', '滚动更新'),
        ('blue_green', '蓝绿部署'),
        ('canary', '灰度发布'),
    ]

    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="env_configs")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="+")
    namespace = models.ForeignKey(K8sNamespace, on_delete=models.CASCADE, related_name="+")
    deploy_strategy = models.CharField(max_length=16, choices=STRATEGIES, default='rolling')
    replicas = models.IntegerField(default=1, verbose_name="副本数")
    canary_percent = models.IntegerField(default=10, verbose_name="灰度比例(%)",
                                         help_text="仅灰度策略有效")
    image_repo = models.CharField(max_length=128, verbose_name="镜像仓库")
    container_port = models.IntegerField(default=8080, verbose_name="容器端口")
    health_check_path = models.CharField(max_length=64, default='/health', verbose_name="健康检查路径")
    cpu_limit = models.CharField(max_length=16, default='500m', verbose_name="CPU 限制")
    memory_limit = models.CharField(max_length=16, default='512Mi', verbose_name="内存限制")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_env_config"
        unique_together = [("application", "environment")]
```

### 3.4 发布核心模块

#### 3.4.1 Release（发布单）

```python
class Release(models.Model):
    """发布单"""
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '审批通过'),
        ('rejected', '审批驳回'),
        ('running', '发布中'),
        ('paused', '已暂停'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('rolled_back', '已回滚'),
        ('cancelled', '已取消'),
    ]

    id = models.AutoField(primary_key=True)
    release_no = models.CharField(max_length=32, unique=True, verbose_name="发布单号",
                                  help_text="格式: REL-YYYYMMDD-xxxx")
    title = models.CharField(max_length=128, verbose_name="发布标题")
    description = models.TextField(blank=True, verbose_name="发布描述")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="releases")
    env_config = models.ForeignKey(AppEnvConfig, on_delete=models.CASCADE, related_name="+")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    version = models.CharField(max_length=32, verbose_name="版本号")
    commit_id = models.CharField(max_length=64, blank=True, verbose_name="Commit ID")
    commit_message = models.TextField(blank=True, verbose_name="Commit 信息")
    image_tag = models.CharField(max_length=128, verbose_name="镜像 Tag")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    deploy_strategy = models.CharField(max_length=16, choices=AppEnvConfig.STRATEGIES, default='rolling')
    canary_percent = models.IntegerField(default=10, verbose_name="灰度比例(%)")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_releases",
                                verbose_name="创建人")
    current_stage = models.CharField(max_length=32, blank=True, verbose_name="当前阶段")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "release"
        ordering = ["-created_at"]
```

#### 3.4.2 ReleaseTask（发布阶段任务）

```python
class ReleaseTask(models.Model):
    """发布阶段任务"""
    STAGES = [
        ('build', '构建'),
        ('deploy_dev', '部署开发'),
        ('verify_dev', '验证开发'),
        ('deploy_test', '部署测试'),
        ('verify_test', '验证测试'),
        ('approve_staging', '预发审批'),
        ('deploy_staging', '部署预发'),
        ('verify_staging', '验证预发'),
        ('gray_release', '灰度发布'),
        ('full_release', '全量发布'),
        ('final_verify', '最终验证'),
    ]

    STATUS_CHOICES = [
        ('pending', '等待'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('skipped', '跳过'),
    ]

    id = models.AutoField(primary_key=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="tasks")
    stage = models.CharField(max_length=32, choices=STAGES, verbose_name="阶段")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    retry_count = models.IntegerField(default=0)
    message = models.TextField(blank=True, verbose_name="结果信息")

    class Meta:
        db_table = "release_task"
        ordering = ["release", "id"]
        unique_together = [("release", "stage")]
```

#### 3.4.3 TaskLog（任务日志）

```python
class TaskLog(models.Model):
    """任务执行日志"""
    LEVELS = [
        ('info', 'Info'),
        ('warn', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]

    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(ReleaseTask, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=8, choices=LEVELS, default='info')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_log"
        ordering = ["created_at"]
```

#### 3.4.4 Artifact（制品）

```python
class Artifact(models.Model):
    """构建产物记录"""
    TYPES = [
        ('docker_image', 'Docker 镜像'),
        ('jar', 'JAR 包'),
        ('zip', '压缩包'),
    ]

    id = models.AutoField(primary_key=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="artifacts")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="+")
    version = models.CharField(max_length=32, verbose_name="版本")
    artifact_type = models.CharField(max_length=16, choices=TYPES, verbose_name="制品类型")
    storage_path = models.CharField(max_length=256, verbose_name="存储路径")
    image_tag = models.CharField(max_length=128, blank=True, verbose_name="镜像 Tag")
    hash = models.CharField(max_length=64, blank=True, verbose_name="校验值")
    size = models.BigIntegerField(default=0, verbose_name="大小(字节)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artifact"
```

### 3.5 审批模块

#### 3.5.1 Approval（审批记录）

```python
class Approval(models.Model):
    """审批记录"""
    ACTIONS = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]

    APPROVAL_TYPES = [
        ('release', '发布审批'),
        ('permission', '权限申请'),
    ]

    id = models.AutoField(primary_key=True)
    approval_type = models.CharField(max_length=16, choices=APPROVAL_TYPES, default='release')
    # 关联发布或权限申请
    release = models.ForeignKey(Release, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="approvals")
    user_permission = models.ForeignKey(UserPermission, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name="approvals")
    # 审批流程
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approvals",
                                 verbose_name="审批人")
    action = models.CharField(max_length=16, choices=ACTIONS, default='pending')
    comment = models.TextField(blank=True, verbose_name="审批意见")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approval"
        ordering = ["-created_at"]
```

### 3.6 部署模块

#### 3.6.1 DeployHistory（部署历史）

```python
class DeployHistory(models.Model):
    """部署历史"""
    ACTIONS = [
        ('deploy', '部署'),
        ('rollback', '回滚'),
        ('restart', '重启'),
        ('scale', '扩缩容'),
    ]

    id = models.AutoField(primary_key=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="deploy_histories")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="+")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    version = models.CharField(max_length=32, verbose_name="版本")
    image_tag = models.CharField(max_length=128, verbose_name="镜像 Tag")
    action = models.CharField(max_length=16, choices=ACTIONS, verbose_name="操作类型")
    status = models.CharField(max_length=16, choices=ReleaseTask.STATUS_CHOICES, default='pending')
    strategy = models.CharField(max_length=16, verbose_name="部署策略")
    canary_percent = models.IntegerField(null=True, blank=True, verbose_name="灰度比例")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "deploy_history"
        ordering = ["-created_at"]
```

#### 3.6.2 PodInstance（Pod 状态快照）

```python
class PodInstance(models.Model):
    """部署后的 Pod 状态快照"""
    STATUSES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown'),
    ]

    id = models.AutoField(primary_key=True)
    deploy_history = models.ForeignKey(DeployHistory, on_delete=models.CASCADE, related_name="pods")
    pod_name = models.CharField(max_length=128, verbose_name="Pod 名称")
    node_name = models.CharField(max_length=128, blank=True, verbose_name="节点名称")
    ip = models.CharField(max_length=32, blank=True, verbose_name="Pod IP")
    status = models.CharField(max_length=16, choices=STATUSES, verbose_name="Pod 状态")
    image = models.CharField(max_length=256, blank=True, verbose_name="镜像")
    started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pod_instance"
```

#### 3.6.3 RollbackRecord（回滚记录）

```python
class RollbackRecord(models.Model):
    """回滚记录"""
    id = models.AutoField(primary_key=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="rollbacks")
    deploy_history = models.ForeignKey(DeployHistory, on_delete=models.CASCADE, related_name="+")
    from_version = models.CharField(max_length=32, verbose_name="回滚前版本")
    to_version = models.CharField(max_length=32, verbose_name="回滚目标版本")
    reason = models.TextField(blank=True, verbose_name="回滚原因")
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rollback_record"
        ordering = ["-created_at"]
```

### 3.7 审计日志模块

#### 3.7.1 AuditLog（审计日志）

```python
class AuditLog(models.Model):
    """操作审计日志"""
    ACTIONS = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('deploy', '部署'),
        ('rollback', '回滚'),
        ('approve', '审批通过'),
        ('reject', '审批驳回'),
        ('login', '登录'),
        ('grant_permission', '授权'),
        ('revoke_permission', '撤权'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    action = models.CharField(max_length=32, choices=ACTIONS, verbose_name="操作")
    resource_type = models.CharField(max_length=32, verbose_name="资源类型",
                                     help_text="application / release / permission / ...")
    resource_id = models.IntegerField(verbose_name="资源 ID")
    detail = models.JSONField(default=dict, verbose_name="操作详情")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]
```

### 3.8 制品管理模块

#### 3.8.1 ArtifactRepository（制品仓库）

```python
class ArtifactRepository(models.Model):
    """制品仓库 - 存储制品的后端系统"""
    REPO_TYPES = [
        ('docker_registry', 'Docker Registry'),
        ('harbor', 'Harbor'),
        ('nexus', 'Nexus'),
        ('s3', 'S3 存储'),
        ('local', '本地存储'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="仓库名称")
    repo_type = models.CharField(max_length=32, choices=REPO_TYPES, verbose_name="仓库类型")
    url = models.URLField(verbose_name="仓库地址")
    # 认证信息（Demo 中可为空或简单处理）
    username = models.CharField(max_length=64, blank=True, verbose_name="用户名")
    password = models.CharField(max_length=128, blank=True, verbose_name="密码")
    is_default = models.BooleanField(default=False, verbose_name="是否默认仓库")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artifact_repository"
```

#### 3.8.2 Artifact（制品）

```python
class Artifact(models.Model):
    """制品 - 构建产物的记录，连接 CI 和 CD 的桥梁"""
    ARTIFACT_TYPES = [
        ('docker_image', 'Docker 镜像'),
        ('jar', 'JAR 包'),
        ('war', 'WAR 包'),
        ('npm_package', 'NPM 包'),
        ('python_wheel', 'Python Wheel'),
        ('binary', '二进制文件'),
        ('static_files', '静态文件'),
        ('helm_chart', 'Helm Chart'),
    ]

    id = models.AutoField(primary_key=True)
    # 关联信息
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="artifacts",
                                    verbose_name="所属应用")
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="artifacts", verbose_name="关联发布单")
    # 版本信息
    version = models.CharField(max_length=64, verbose_name="版本号")
    artifact_type = models.CharField(max_length=32, choices=ARTIFACT_TYPES, verbose_name="制品类型")
    # 存储信息
    repository = models.ForeignKey(ArtifactRepository, on_delete=models.CASCADE, related_name="+",
                                   verbose_name="制品仓库")
    storage_path = models.CharField(max_length=512, verbose_name="存储路径",
                                    help_text="Docker 镜像的完整名称或文件的存储路径")
    image_tag = models.CharField(max_length=128, blank=True, verbose_name="镜像 Tag",
                                 help_text="Docker 镜像特有，如 v1.2.3")
    file_name = models.CharField(max_length=256, blank=True, verbose_name="文件名",
                                 help_text="文件制品特有")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小(字节)")
    checksum = models.CharField(max_length=128, blank=True, verbose_name="校验值(SHA256)")
    # 构建元信息
    build_job_url = models.URLField(blank=True, verbose_name="构建任务链接")
    build_duration = models.IntegerField(default=0, verbose_name="构建耗时(秒)")
    commit_id = models.CharField(max_length=64, blank=True, verbose_name="构建时的 Commit ID")
    branch = models.CharField(max_length=64, blank=True, verbose_name="构建分支")
    # 额外元数据（JSON 灵活扩展）
    metadata = models.JSONField(default=dict, verbose_name="额外元数据",
                                help_text="构建参数、环境信息、依赖信息等")
    # 当前所处的环境晋级阶段
    current_env = models.CharField(max_length=16, blank=True, verbose_name="当前所在环境",
                                   help_text="dev / test / staging / prod")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "artifact"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "-created_at"]),
            models.Index(fields=["version"]),
        ]
```

#### 3.8.3 ArtifactPromotion（制品晋级记录）

```python
class ArtifactPromotion(models.Model):
    """制品晋级记录 - 制品从一个环境"晋级"到下一个环境"""
    PROMOTION_STATUS = [
        ('pending', '待晋级'),
        ('promoted', '已晋级'),
        ('rejected', '驳回'),
        ('rolled_back', '已回退'),
    ]

    id = models.AutoField(primary_key=True)
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="promotions")
    from_env = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+",
                                 verbose_name="来源环境")
    to_env = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+",
                               verbose_name="目标环境")
    status = models.CharField(max_length=16, choices=PROMOTION_STATUS, default='pending')
    # 关联的发布（晋级通常通过发布完成）
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="+")
    promoted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    promoted_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artifact_promotion"
        ordering = ["-created_at"]
```

#### 3.8.4 制品在发布流程中的位置

```
CI 构建完成
    │
    ▼
创建制品记录 (Artifact) ──── 存储到仓库 (ArtifactRepository)
    │
    ▼
晋级到 dev 环境 (ArtifactPromotion: null → dev)
    │
    ▼
晋级到 test 环境 (ArtifactPromotion: dev → test)
    │
    ▼
晋级到 staging 环境 (ArtifactPromotion: test → staging)
    │
    ▼
晋级到 prod 环境 (ArtifactPromotion: staging → prod)
    │
    ▼
制品归档/清理

每个晋级步骤通常对应一个发布阶段 (ReleaseTask)
```

### 3.9 配置管理模块

#### 3.9.1 核心概念说明

> **配置管理** 解决的是"应用代码与配置分离"的问题。同一个代码包部署到不同环境时，需要有不同的配置值（如数据库地址、API Key、日志级别等）。配置管理模块负责：
> 1. 定义配置模板（描述配置结构）
> 2. 管理环境变量值（按环境维护不同的值）
> 3. 渲染配置（模板 + 变量 → 最终的 YAML/配置文件）
> 4. 追踪配置变更（版本历史、差异对比）
> 5. 配置与发布联动（发布时携带配置版本）

#### 3.9.2 ConfigTemplate（配置模板）

```python
class ConfigTemplate(models.Model):
    """配置模板 - 定义配置的结构和变量占位符"""
    TEMPLATE_TYPES = [
        ('yaml', 'YAML 配置文件'),
        ('properties', 'Properties 文件'),
        ('env', '环境变量'),
        ('json', 'JSON 配置文件'),
        ('nginx', 'Nginx 配置'),
        ('custom', '自定义'),
    ]

    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="config_templates",
                                    verbose_name="所属应用")
    name = models.CharField(max_length=64, verbose_name="模板名称")
    template_type = models.CharField(max_length=16, choices=TEMPLATE_TYPES, verbose_name="模板类型")
    # 模板内容，使用 Jinja2 或 Go template 语法
    # 例如: "database_url: {{ DB_URL }}\nlog_level: {{ LOG_LEVEL }}"
    template_content = models.TextField(verbose_name="模板内容")
    description = models.TextField(blank=True, verbose_name="描述")
    # 配置文件的部署路径（部署时写入到容器中的路径）
    deploy_path = models.CharField(max_length=256, blank=True, verbose_name="部署路径",
                                   help_text="如 /etc/app/config.yaml")
    version = models.IntegerField(default=1, verbose_name="模板版本")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_template"
        unique_together = [("application", "name")]
```

#### 3.9.3 ConfigVariable（配置变量定义）

```python
class ConfigVariable(models.Model):
    """配置变量 - 模板中使用的变量定义"""
    VALUE_TYPES = [
        ('string', '字符串'),
        ('number', '数字'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
        ('text', '多行文本'),
    ]

    id = models.AutoField(primary_key=True)
    template = models.ForeignKey(ConfigTemplate, on_delete=models.CASCADE, related_name="variables",
                                 verbose_name="所属模板")
    key = models.CharField(max_length=128, verbose_name="变量名",
                           help_text="如 DB_URL, LOG_LEVEL, APP_NAME")
    value_type = models.CharField(max_length=16, choices=VALUE_TYPES, default='string')
    default_value = models.TextField(blank=True, verbose_name="默认值")
    description = models.TextField(blank=True, verbose_name="变量说明")
    is_secret = models.BooleanField(default=False, verbose_name="是否为敏感变量",
                                    help_text="敏感变量在 UI 中加密显示，如密码、Token")
    is_required = models.BooleanField(default=True, verbose_name="是否必填")
    validation_rule = models.CharField(max_length=256, blank=True, verbose_name="校验规则",
                                       help_text="正则表达式或取值范围")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "config_variable"
        unique_together = [("template", "key")]
        ordering = ["template", "sort_order"]
```

#### 3.9.4 ConfigVariableValue（变量值-按环境）

```python
class ConfigVariableValue(models.Model):
    """配置变量值 - 每个变量在不同环境下的具体值"""
    id = models.AutoField(primary_key=True)
    variable = models.ForeignKey(ConfigVariable, on_delete=models.CASCADE, related_name="values")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    value = models.TextField(verbose_name="变量值")
    # 敏感变量的加密值（Demo 中可简化，使用 Django 的加密）
    encrypted_value = models.TextField(blank=True, verbose_name="加密值")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_variable_value"
        unique_together = [("variable", "environment")]
```

#### 3.9.5 ConfigRelease（配置发布记录）

```python
class ConfigRelease(models.Model):
    """配置发布记录 - 记录某次发布时使用的配置版本"""
    id = models.AutoField(primary_key=True)
    template = models.ForeignKey(ConfigTemplate, on_delete=models.CASCADE, related_name="releases")
    version = models.IntegerField(verbose_name="配置版本号")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    # 渲染后的完整配置内容（快照，用于回滚和历史追溯）
    rendered_content = models.TextField(verbose_name="渲染后的配置内容")
    # 关联的发布单
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="config_releases")
    status = models.CharField(max_length=16, choices=[
        ('pending', '待应用'),
        ('applied', '已应用'),
        ('rolled_back', '已回滚'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_release"
        ordering = ["-created_at"]
```

#### 3.9.6 配置与发布的联动流程

```
发布流程中的配置处理:

1. 创建发布时:
   - 选择当前环境的配置版本
   - 预览配置渲染结果

2. 执行部署阶段:
   - 读取 ConfigRelease.rendered_content
   - 写入 K8s ConfigMap / Secret
   - 挂载到 Pod 中

3. 回滚操作:
   - 选择历史的 ConfigRelease
   - 重新应用旧的配置

4. 配置变更独立于代码发布:
   - 可以直接修改配置值并应用（不经过完整发布流程）
   - 修改敏感变量需要审批
```

### 3.10 更新后的 ER 图（关键关系）

```
BusinessLine ──┬── Group ──── SubjectMembership ──── User
               │       │
               │       └── GroupPermission ──── Role
               │
               └── Application ──── AppEnvConfig ──── Environment
                       │                │
                       │                ├── Cluster ──── K8sNamespace
                       │                │
                       ├── Artifact ─────┴── ArtifactRepository
                       │       │
                       │       └── ArtifactPromotion
                       │
                       ├── ConfigTemplate ──── ConfigVariable ──── ConfigVariableValue
                       │       │
                       │       └── ConfigRelease
                       │
                       └── Release ─────┘
                              │
                              ├── ReleaseTask ──── TaskLog
                              ├── Approval
                              ├── DeployHistory ──── PodInstance
                              └── RollbackRecord

User ──── UserPermission (个人例外权限)
```

---

## 4. API 接口设计

### 4.1 通用约定

- **Base URL**: `/api/v1/`
- **认证方式**: `Authorization: Bearer <jwt_token>`
- **响应格式**:

```json
{
    "code": 200,
    "message": "success",
    "data": { ... },
    "pagination": { "page": 1, "page_size": 20, "total": 100 }
}
```

- **错误格式**:

```json
{
    "code": 403,
    "message": "Permission denied",
    "detail": "您没有 payment-api/prod 的 deploy 权限"
}
```

### 4.2 认证接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/auth/login/` | 选择用户登录（Demo 模式） | 无需认证 |
| POST | `/api/v1/auth/logout/` | 退出登录 | 已登录 |
| GET  | `/api/v1/auth/me/` | 获取当前用户信息及权限 | 已登录 |

**POST /auth/login/ 请求**

```json
{
    "username": "zhangsan"
}
```

**POST /auth/login/ 响应**

```json
{
    "code": 200,
    "data": {
        "token": "eyJ...",
        "user": {
            "id": 1,
            "username": "zhangsan",
            "display_name": "张三",
            "avatar_url": ""
        },
        "permissions": {
            "roles": ["deployer"],
            "menu_codes": ["dashboard", "apps", "releases", "approvals"],
            "data_scope": {
                "business_line_ids": [1, 2],
                "app_ids": [1, 2, 3],
                "env_ids": [1, 2]
            }
        }
    }
}
```

### 4.3 用户接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/users/` | 用户列表（供登录选择） | 无需认证 |
| GET  | `/api/v1/users/{id}/` | 用户详情 | 登录 |
| GET  | `/api/v1/users/{id}/permissions/` | 用户权限概览（组内/协作/个人） | 登录 |

### 4.4 组织管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/org/tree/` | 获取组织树（业务线→组→用户） | 登录 |
| GET  | `/api/v1/org/business-lines/` | 业务线列表 | 登录 |
| POST | `/api/v1/org/business-lines/` | 创建业务线 | admin |
| PUT  | `/api/v1/org/business-lines/{id}/` | 更新业务线 | admin |
| GET  | `/api/v1/org/groups/` | 组列表 | 登录 |
| POST | `/api/v1/org/groups/` | 创建组 | admin |
| PUT  | `/api/v1/org/groups/{id}/` | 更新组 | admin |
| POST | `/api/v1/org/groups/{id}/members/` | 添加成员 | admin |
| DELETE | `/api/v1/org/groups/{id}/members/{user_id}/` | 移除成员 | admin |
| PATCH | `/api/v1/org/groups/{id}/members/{user_id}/` | 修改成员类型（归属/协作）或资源范围 | admin |

### 4.5 权限管理接口

#### 4.5.1 角色管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/authz/roles/` | 角色列表 | admin |
| POST | `/api/v1/authz/roles/` | 创建角色（仅自定义） | admin |
| PUT  | `/api/v1/authz/roles/{id}/` | 更新角色权限 | admin |
| DELETE | `/api/v1/authz/roles/{id}/` | 删除角色（仅自定义） | admin |

#### 4.5.2 组权限配置

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/authz/group-permissions/` | 组权限列表 | admin |
| POST | `/api/v1/authz/group-permissions/` | 配置组权限 | admin |
| PUT  | `/api/v1/authz/group-permissions/{id}/` | 更新组权限 | admin |
| DELETE | `/api/v1/authz/group-permissions/{id}/` | 删除组权限 | admin |
| GET  | `/api/v1/authz/groups/{id}/permissions/` | 查看某个组的权限详情 | admin |

#### 4.5.3 用户个人例外权限

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/authz/user-permissions/` | 用户例外界限列表 | admin |
| POST | `/api/v1/authz/user-permissions/` | 添加用户例外权限 | admin/app_owner |
| PUT  | `/api/v1/authz/user-permissions/{id}/` | 更新 | admin |
| DELETE | `/api/v1/authz/user-permissions/{id}/` | 删除 | admin |
| GET  | `/api/v1/authz/users/{id}/permissions/` | 查看某个用户的全部权限（组内+协作+个人） | admin/本人 |

#### 4.5.4 权限申请（用户自助）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/authz/permission-requests/` | 提交权限申请 | 登录 |
| GET  | `/api/v1/authz/permission-requests/` | 我的申请列表 | 登录 |

### 4.6 基础设施接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/infra/environments/` | 环境列表 | 登录 |
| POST | `/api/v1/infra/environments/` | 创建环境 | admin |
| GET  | `/api/v1/infra/clusters/` | 集群列表 | admin |
| POST | `/api/v1/infra/clusters/` | 创建集群 | admin |
| GET  | `/api/v1/infra/namespaces/` | 命名空间列表 | admin |

### 4.7 应用管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/apps/` | 应用列表（按数据权限过滤） | 登录 |
| POST | `/api/v1/apps/` | 创建应用 | admin/app_owner |
| GET  | `/api/v1/apps/{id}/` | 应用详情 | 登录 |
| PUT  | `/api/v1/apps/{id}/` | 更新应用 | admin/app_owner |
| DELETE | `/api/v1/apps/{id}/` | 删除应用 | admin |
| GET  | `/api/v1/apps/{id}/env-configs/` | 应用环境配置列表 | 登录 |
| POST | `/api/v1/apps/{id}/env-configs/` | 配置应用环境 | admin |
| PUT  | `/api/v1/apps/{id}/env-configs/{config_id}/` | 更新环境配置 | admin |
| GET  | `/api/v1/resource-tree/` | 获取资源树（业务线→应用→环境） | 登录 |

### 4.8 发布管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/releases/` | 发布列表 | 登录 |
| POST | `/api/v1/releases/` | 创建发布单 | deploy/deployer |
| GET  | `/api/v1/releases/{id}/` | 发布详情 | 登录 |
| POST | `/api/v1/releases/{id}/submit/` | 提交审批 | deployer(本人) |
| POST | `/api/v1/releases/{id}/cancel/` | 取消发布单 | deployer(本人)/admin |
| GET  | `/api/v1/releases/{id}/tasks/` | 发布阶段任务列表 | 登录 |
| POST | `/api/v1/releases/{id}/tasks/{task_id}/execute/` | 执行阶段任务 | deploy/deployer |
| POST | `/api/v1/releases/{id}/tasks/{task_id}/retry/` | 重试失败任务 | deploy/deployer |
| POST | `/api/v1/releases/{id}/rollback/` | 回滚发布 | release_manager |
| GET  | `/api/v1/releases/{id}/pipeline/` | 获取流水线状态 | 登录 |

### 4.9 审批接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/approvals/` | 审批列表（待审批/已审批） | 登录 |
| GET  | `/api/v1/approvals/pending/` | 我的待审批列表 | 登录 |
| POST | `/api/v1/approvals/{id}/approve/` | 审批通过 | app_owner/release_manager |
| POST | `/api/v1/approvals/{id}/reject/` | 审批驳回 | app_owner/release_manager |

### 4.10 部署历史接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/deploy-history/` | 部署历史列表 | 登录 |
| GET  | `/api/v1/deploy-history/{id}/` | 部署详情 | 登录 |
| GET  | `/api/v1/deploy-history/{id}/pods/` | 部署 Pod 列表 | 登录 |
| POST | `/api/v1/deploy-history/{id}/rollback/` | 从历史记录回滚 | release_manager |

### 4.11 审计日志接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/audit-logs/` | 审计日志列表 | admin/auditor |
| GET  | `/api/v1/audit-logs/{id}/` | 审计日志详情 | admin/auditor |

### 4.12 仪表盘接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/dashboard/stats/` | 统计数据（发布总数、成功率、待审批数等） | 登录 |
| GET  | `/api/v1/dashboard/recent-releases/` | 近期发布 | 登录 |
| GET  | `/api/v1/dashboard/my-pending-approvals/` | 我的待审批 | 登录 |

### 4.13 制品管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/artifacts/` | 制品列表 | 登录 |
| POST | `/api/v1/artifacts/` | 创建制品记录 | deployer |
| GET  | `/api/v1/artifacts/{id}/` | 制品详情 | 登录 |
| GET  | `/api/v1/artifacts/by-app/{app_id}/` | 按应用查询制品列表 | 登录 |
| GET  | `/api/v1/artifacts/{id}/promotions/` | 制品晋级历史 | 登录 |
| POST | `/api/v1/artifacts/{id}/promote/` | 晋级制品到下一环境 | deployer |
| GET  | `/api/v1/artifact-repositories/` | 制品仓库列表 | admin |
| POST | `/api/v1/artifact-repositories/` | 创建制品仓库 | admin |

### 4.14 配置管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET  | `/api/v1/config-templates/` | 配置模板列表 | 登录 |
| POST | `/api/v1/config-templates/` | 创建配置模板 | admin/app_owner |
| GET  | `/api/v1/config-templates/{id}/` | 模板详情（含变量列表） | 登录 |
| PUT  | `/api/v1/config-templates/{id}/` | 更新模板 | admin/app_owner |
| POST | `/api/v1/config-templates/{id}/render/` | 预览渲染结果 | 登录 |
| GET  | `/api/v1/config-variables/` | 变量列表 | 登录 |
| POST | `/api/v1/config-variables/` | 创建变量定义 | admin/app_owner |
| PUT  | `/api/v1/config-variables/{id}/` | 更新变量定义 | admin/app_owner |
| GET  | `/api/v1/config-variable-values/` | 变量值列表 | 登录 |
| PUT  | `/api/v1/config-variable-values/{id}/` | 更新变量值（按环境） | admin/app_owner |
| POST | `/api/v1/config-variable-values/batch/` | 批量更新变量值（按环境） | admin/app_owner |
| GET  | `/api/v1/config-releases/` | 配置发布记录 | 登录 |
| POST | `/api/v1/config-releases/` | 发布配置（渲染并记录） | deployer/admin |
| GET  | `/api/v1/config-releases/{id}/diff/` | 配置版本差异对比 | 登录 |

---

## 5. 前端页面设计

### 5.1 路由设计

```typescript
const routes = [
    { path: '/login', component: LoginPage, auth: false },
    { path: '/', component: AppLayout, auth: true, children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: DashboardPage, permission: 'page_dashboard' },
        { path: 'apps', component: AppListPage, permission: 'page_apps' },
        { path: 'apps/:id', component: AppDetailPage, permission: 'page_apps' },
        { path: 'apps/:id/env-config', component: AppEnvConfigPage, permission: 'page_apps' },
        { path: 'releases', component: ReleaseListPage, permission: 'page_releases' },
        { path: 'releases/new', component: CreateReleasePage, permission: 'action_create_release' },
        { path: 'releases/:id', component: ReleaseDetailPage, permission: 'page_releases' },
        { path: 'approvals', component: ApprovalCenterPage, permission: 'page_approvals' },
        { path: 'permissions', component: PermissionIndexPage, permission: 'page_permissions', children: [
            { path: 'roles', component: RoleManagerPage, permission: 'page_permission_roles' },
            { path: 'groups', component: GroupPermissionPage, permission: 'page_permission_groups' },
            { path: 'users/:id', component: UserPermissionPage, permission: 'page_permission_users' },
            { path: 'my', component: MyPermissionsPage, permission: 'page_my_permissions' },
        ]},
        { path: 'artifacts', component: ArtifactListPage, permission: 'page_artifacts' },
        { path: 'artifacts/:id', component: ArtifactDetailPage, permission: 'page_artifacts' },
        { path: 'config', component: ConfigIndexPage, permission: 'page_config', children: [
            { path: 'templates', component: ConfigTemplateListPage, permission: 'page_config_templates' },
            { path: 'templates/:id', component: ConfigTemplateDetailPage, permission: 'page_config_templates' },
            { path: 'variables', component: ConfigVariablePage, permission: 'page_config_variables' },
            { path: 'releases', component: ConfigReleaseListPage, permission: 'page_config_releases' },
        ]},
        { path: 'infrastructures', component: InfraPage, permission: 'page_infrastructures' },
        { path: 'deploy-history', component: DeployHistoryPage, permission: 'page_deploy_history' },
        { path: 'audit-logs', component: AuditLogPage, permission: 'page_audit_logs' },
    ]},
];
```

### 5.2 侧边栏菜单

根据用户权限动态渲染：

```
┌─ 仪表盘                      [menu_dashboard]      所有人可见
├─ 应用管理                    [menu_apps]           所有人可见
├─ 发布管理                    [menu_releases]       所有人可见
├─ 审批中心                    [menu_approvals]      有审批权限的人
├─ 权限管理                    [menu_permissions]    admin 可见
│  ├─ 角色管理                 [menu_permission_roles]
│  ├─ 组权限配置               [menu_permission_groups]
│  ├─ 用户权限                 [menu_permission_users]
│  └─ 我的权限                 [menu_my_permissions] 所有人可见
├─ 制品管理                    [menu_artifacts]       deployer 可见
├─ 配置管理                    [menu_config]          deployer 可见
│  ├─ 配置模板                 [menu_config_templates]
│  ├─ 变量管理                 [menu_config_variables]
│  └─ 配置发布记录             [menu_config_releases]
├─ 环境与集群                  [menu_infrastructures] admin 可见
├─ 部署历史                    [menu_deploy_history]  所有人可见
└─ 审计日志                    [menu_audit_logs]      admin/auditor 可见
```

### 5.3 关键页面交互

#### 5.3.1 登录页

- 下拉选择用户（展示所有用户列表）
- 选择后直接登录，无需密码
- 登录后跳转到仪表盘

#### 5.3.2 权限管理 - 组织树 + 权限配置

这是最核心的页面，布局如下：

```
┌─────────────────────────────────────────────────────────────────┐
│ 权限管理                                                    [+ 角色管理] │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────────────┐ ┌──────────────────────────────────────┐ │
│ │   组织树 (搜索)     │ │  权限详情面板                        │ │
│ │                    │ │                                      │ │
│ │  ▼ 支付业务线       │ │  [组信息] 支付研发组                  │ │
│ │    ▼ 支付研发组     │ │  业务线: 支付业务线                   │ │
│ │      张三 (归属)    │ │  成员: 3人 (2归属, 1协作)            │ │
│ │      李四 (归属)    │ │                                      │ │
│ │      王五 (协作)    │ │  [组权限范围]                         │ │
│ │    ▼ 前端组         │ │  角色: 发布者                        │ │
│ │      王五 (归属)    │ │  资源: payment-api, order-api        │ │
│ │      小刘 (归属)    │ │  环境: ☑ dev ☑ test ☐ staging ☐ prod │ │
│ │  ▼ 电商业务线       │ │  [操作] 编辑权限 ｜ 添加成员          │ │
│ │    ︙               │ │                                      │ │
│ │                    │ │  ── 成员列表 ──                       │ │
│ │                    │ │  ├─ 张三 (归属) → 继承组范围          │ │
│ │                    │ │  ├─ 李四 (归属) → 继承组范围          │ │
│ │                    │ │  └─ 王五 (协作) → 仅 payment-frontend │ │
│ └────────────────────┘ └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**交互逻辑**：
1. 左侧组织树展开到业务线 → 组 → 用户
2. 点击"组" → 右侧显示组权限详情 + 组成员列表
3. 点击"用户" → 右侧显示该用户权限概览（组内/协作/个人例外）
4. 支持搜索：搜索用户/组名称，树自动高亮匹配节点
5. 添加协作成员时，可指定其资源范围

#### 5.3.3 我的权限页

```
┌─ 我的权限 (王五) ──────────────────────────────────────────────┐
│                                                               │
│  当前角色: 发布者                                               │
│  归属组: 前端组                                                 │
│                                                               │
│  ┌─ 组内权限 (来源: 前端组)                                     │
│  │  ├─ frontend-app / dev, test → deploy, view_log             │
│  │  └─ frontend-app / dev, test → view_release                 │
│  │                                                             │
│  ├─ 跨组协作 (来源: 支付研发组)                                  │
│  │  └─ payment-frontend / dev, test → deploy, view_log         │
│  │                                                             │
│  └─ 个人例外权限                                                │
│     └─ payment-frontend / prod → deploy [来源: 审批单 #2025-001]│
│                                                               │
│  [+ 申请权限]                                                  │
└───────────────────────────────────────────────────────────────┘
```

#### 5.3.4 发布流水线页

```
┌─ 发布单 REL-20260722-0001 ────────────────────────────────────┐
│                                                               │
│  应用: payment-api ｜ 版本: v1.2.3 ｜ 环境: test → prod        │
│  状态: 发布中 ｜ 策略: 灰度发布(10%)                            │
│                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐ │
│  │ 构建  │→│部署开发│→│部署测试│→│预发审批│→│灰度10%│→│全量  │ │
│  │ ✓完成 │  │ ✓完成 │  │ ▶执行中│  │ ⏳等待 │  │ ⏳等待 │  │ ⏳等待│ │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘ │
│                                                               │
│  ── 当前阶段日志 ──                                            │
│  [2026-07-22 14:30:01] 开始部署到 test 环境...                │
│  [2026-07-22 14:30:05] 创建 Deployment payment-api-test       │
│  [2026-07-22 14:30:08] 等待 Pod 就绪...                       │
│  [2026-07-22 14:30:15] Pod payment-api-test-7d8f9c-1 Running  │
│  [2026-07-22 14:30:15] Pod payment-api-test-7d8f9c-2 Running  │
│  [2026-07-22 14:30:16] 健康检查通过                            │
│                                                               │
│  [操作] 暂停 ｜ 继续 ｜ 回滚                                    │
└───────────────────────────────────────────────────────────────┘
```

#### 5.3.5 制品管理页

```
┌─ 制品管理 ────────────────────────────────────────────────────┐
│                                                               │
│  [应用筛选: payment-api]  [类型筛选: 全部]  [+ 创建制品]       │
│                                                               │
│  ┌────┬────────┬────────┬────────┬────────┬────────┬────────┐ │
│  │ ID │ 版本   │ 类型   │ 应用   │ 环境   │ 构建时间│ 操作   │ │
│  ├────┼────────┼────────┼────────┼────────┼────────┼────────┤ │
│  │ 1  │ v1.2.3 │ Docker │ pay-   │ prod   │ 07-22  │ 详情   │ │
│  │    │        │ 镜像   │ ment   │        │ 14:30  │ 晋级   │ │
│  ├────┼────────┼────────┼────────┼────────┼────────┼────────┤ │
│  │ 2  │ v1.2.2 │ Docker │ pay-   │ staging│ 07-21  │ 详情   │ │
│  │    │        │ 镜像   │ ment   │        │ 10:00  │ 晋级   │ │
│  └────┴────────┴────────┴────────┴────────┴────────┴────────┘ │
│                                                               │
│  ── 制品晋级路径 ──                                            │
│  v1.2.3: 构建 → dev ✓ → test ✓ → staging ✓ → prod ▶          │
│  v1.2.2: 构建 → dev ✓ → test ✓ → staging ✓ → prod ✓          │
└───────────────────────────────────────────────────────────────┘
```

#### 5.3.6 配置管理 - 模板编辑页

```
┌─ 配置管理 → 配置模板 (payment-api) ─────────────────────────────┐
│                                                               │
│  模板名称: payment-api-config ｜ 类型: YAML ｜ 版本: v3         │
│  部署路径: /etc/app/config.yaml                               │
│                                                               │
│  ┌─ 模板内容 (Jinja2 模板) ────────────────────────────────┐  │
│  │ server:                                                   │  │
│  │   port: {{ SERVER_PORT }}                                 │  │
│  │ database:                                                 │  │
│  │   url: {{ DB_URL }}                                       │  │
│  │   pool_size: {{ DB_POOL_SIZE }}                           │  │
│  │ log:                                                      │  │
│  │   level: {{ LOG_LEVEL }}                                  │  │
│  │   file: /var/log/app.log                                  │  │
│  │ redis:                                                    │  │
│  │   host: {{ REDIS_HOST }}                                  │  │
│  │   password: {{ REDIS_PASSWORD }}                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ 变量列表 ───────────────────────────────────────────────┐ │
│  │ 变量名         │ 类型   │ dev     │ test    │ prod      │ │
│  │─────────────────────────────────────────────────────────│ │
│  │ SERVER_PORT    │ number │ 8080    │ 8080    │ 8080      │ │
│  │ DB_URL         │ string │ local.. │ test..  │ prod..    │ │
│  │ DB_POOL_SIZE   │ number │ 5       │ 10      │ 20        │ │
│  │ LOG_LEVEL      │ string │ DEBUG   │ DEBUG   │ INFO      │ │
│  │ REDIS_HOST     │ string │ local.. │ redis.. │ redis..   │ │
│  │ REDIS_PASSWORD │ secret │ ***     │ ***     │ ***       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  [操作] 预览渲染结果 ｜ 保存模板 ｜ 发布配置                    │
└───────────────────────────────────────────────────────────────┘
```

#### 5.3.7 配置发布记录与差异对比

```
┌─ 配置发布记录 (payment-api / prod) ────────────────────────────┐
│                                                               │
│  ┌────┬─────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ ID │ 版本    │ 发布人   │ 发布时间  │ 关联发布  │ 操作    │ │
│  ├────┼─────────┼──────────┼──────────┼──────────┼──────────┤ │
│  │ 3  │ v3      │ 张三     │ 07-22    │ REL-...  │ 回滚    │ │
│  │    │         │          │ 14:30    │          │ 对比    │ │
│  │ 2  │ v2      │ 李四     │ 07-20    │ REL-...  │ 对比    │ │
│  │ 1  │ v1      │ 张三     │ 07-15    │ REL-...  │ 对比    │ │
│  └────┴─────────┴──────────┴──────────┴──────────┴──────────┘ │
│                                                               │
│  ── v3 vs v2 差异对比 ──                                      │
│  @@ -3,5 +3,5 @@                                              │
│   database:                                                    │
│  -  url: prod-db-old.example.com                               │
│  +  url: prod-db-new.example.com                               │
│  -  pool_size: 10                                              │
│  +  pool_size: 20                                              │
│   log:                                                         │
│  -  level: DEBUG                                               │
│  +  level: INFO                                                │
└───────────────────────────────────────────────────────────────┘
```

### 5.4 页面/功能权限编码

```typescript
const PERMISSION_CODES = {
    // 菜单可见性
    menu_dashboard: '仪表盘菜单',
    menu_apps: '应用管理菜单',
    menu_releases: '发布管理菜单',
    menu_approvals: '审批中心菜单',
    menu_permissions: '权限管理菜单',
    menu_permission_roles: '角色管理菜单',
    menu_permission_groups: '组权限配置菜单',
    menu_permission_users: '用户权限菜单',
    menu_my_permissions: '我的权限菜单',
    menu_artifacts: '制品管理菜单',
    menu_config: '配置管理菜单',
    menu_config_templates: '配置模板菜单',
    menu_config_variables: '变量管理菜单',
    menu_config_releases: '配置发布记录菜单',
    menu_infrastructures: '环境与集群菜单',
    menu_deploy_history: '部署历史菜单',
    menu_audit_logs: '审计日志菜单',

    // 页面访问
    page_dashboard: '仪表盘页面',
    page_apps: '应用管理页面',
    page_releases: '发布管理页面',
    page_approvals: '审批中心页面',
    page_permissions: '权限管理页面',
    page_deploy_history: '部署历史页面',
    page_audit_logs: '审计日志页面',
    page_artifacts: '制品管理页面',
    page_config: '配置管理页面',
    page_config_templates: '配置模板页面',
    page_config_variables: '变量管理页面',
    page_config_releases: '配置发布记录页面',

    // 操作按钮
    action_create_app: '创建应用',
    action_edit_app: '编辑应用',
    action_delete_app: '删除应用',
    action_create_release: '创建发布',
    action_cancel_release: '取消发布',
    action_execute_task: '执行阶段任务',
    action_retry_task: '重试失败任务',
    action_approve: '审批通过',
    action_reject: '审批驳回',
    action_rollback: '回滚',
    action_manage_permission: '管理权限',
    action_manage_infra: '管理基础设施',
    action_view_audit: '查看审计日志',
    action_create_artifact: '创建制品',
    action_promote_artifact: '晋级制品',
    action_manage_config: '管理配置',
    action_publish_config: '发布配置',
    action_rollback_config: '回滚配置',
};
```

---

## 6. 权限校验设计

### 6.1 后端权限校验流程

```
请求 → JWTAuthentication middleware
     → 解析 JWT → 获取 user_id
     → 设置 request.user
     → 路由匹配 → 进入视图

视图层:
  @permission_required('action_deploy')  # 功能权限校验
  def deploy(request, release_id):
      # 数据权限校验
      release = get_object_or_404(Release, id=release_id)
      if not can(user=request.user, action='deploy', resource=release):
          return PermissionDenied("没有 deploy 权限")
      ...
```

### 6.2 权限校验核心函数

```python
# utils/permissions.py

def can(user: User, action: str, resource_type: str, resource_id: int) -> bool:
    """
    权限校验核心函数
    
    1. 检查用户个人例外权限 (DENY 优先)
    2. 检查用户所在组的权限 (归属 + 协作)
    3. 默认拒绝
    """
    # 1. 个人例外 - DENY
    if has_explicit_deny(user, action, resource_type, resource_id):
        return False
    
    # 2. 个人例外 - ALLOW
    if has_explicit_allow(user, action, resource_type, resource_id):
        return True
    
    # 3. 组权限 (归属组 + 协作组)
    if has_group_permission(user, action, resource_type, resource_id):
        return True
    
    # 4. 默认拒绝
    return False


def can(user: User, action: str, resource_type: str, resource_id: int) -> bool:
    """带缓存的权限校验"""
    cache_key = f"perm:{user.id}:{action}:{resource_type}:{resource_id}"
    result = cache.get(cache_key)
    if result is not None:
        return result == 'allow'
    
    result = _check_permission(user, action, resource_type, resource_id)
    cache.set(cache_key, 'allow' if result else 'deny', timeout=300)
    return result
```

### 6.3 数据权限过滤

对于列表接口，需要根据用户的数据权限范围过滤结果：

```python
# views.py
class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # 获取用户可见的应用 ID 列表
        visible_app_ids = get_visible_app_ids(request.user)
        apps = Application.objects.filter(id__in=visible_app_ids)
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)
```

### 6.4 前端权限校验

```typescript
// 功能权限 - 控制菜单/按钮显示
<PermissionGuard code="action_create_release">
    <Button>创建发布</Button>
</PermissionGuard>

// 数据权限 - 控制列表数据范围
const { data } = await api.get('/apps/', {
    params: { scope: user.data_scope }
});
```

### 6.5 登录即用策略

新用户登录后，系统自动为其分配 `viewer` 角色，确保：

- 可以看到仪表盘、应用列表、发布列表（只读）
- 如果用户属于某个组，自动继承该组的数据权限
- 测试环境默认有 deploy 权限（可通过组权限配置调整）

---

## 7. K8s 集成设计

### 7.1 本地集群方案

使用 **kind** (Kubernetes in Docker) 创建本地集群：

```bash
# scripts/setup-kind.sh
kind create cluster --name release-demo --config kind-config.yaml
```

kind-config.yaml:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
```

### 7.2 K8s 操作封装

```python
# utils/k8s_client.py

class K8sClient:
    def __init__(self, kubeconfig=None):
        if kubeconfig:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            temp_file.write(kubeconfig)
            temp_file.close()
            config.load_kube_config(temp_file.name)
        else:
            config.load_incluster_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    def rolling_update(self, namespace, name, image_tag, replicas=1):
        """滚动更新 Deployment"""
        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        deployment.spec.template.spec.containers[0].image = image_tag
        deployment.spec.replicas = replicas
        return self.apps_v1.patch_namespaced_deployment(name, namespace, deployment)
    
    def blue_green_deploy(self, namespace, name, image_tag, version):
        """蓝绿部署"""
        # 创建新版本 Deployment (name-{version})
        # 更新 Service selector 指向新版本
        pass
    
    def canary_deploy(self, namespace, name, image_tag, canary_percent):
        """灰度发布"""
        # 创建灰度 Deployment (name-canary)
        # 调整主 Deployment 和灰度 Deployment 的副本数比例
        pass
    
    def rollout_undo(self, namespace, name, revision=None):
        """回滚到上一版本"""
        return self.apps_v1.create_namespaced_deployment_rollback(
            name, namespace, 
            client.V1DeploymentRollback(name=name, rollback_to=revision)
        )
    
    def get_pods(self, namespace, label_selector):
        """获取 Pod 列表"""
        return self.core_v1.list_namespaced_pod(
            namespace, label_selector=label_selector
        )
    
    def check_health(self, namespace, name, health_check_path):
        """健康检查"""
        # 通过 port-forward 或 Service 访问 health check
        pass
```

### 7.3 部署策略实现

| 策略 | 核心逻辑 | 适用环境 |
|------|---------|---------|
| **滚动更新** | 修改 Deployment 镜像 → K8s 自动滚动 | dev, test |
| **蓝绿部署** | 创建新 Deployment → 切换 Service selector | staging |
| **灰度发布** | 创建灰度 Deployment → 按比例调整副本数 | staging → prod 过渡 |

### 7.4 发布阶段与 K8s 操作映射

| 发布阶段 | K8s 操作 | 说明 |
|---------|---------|------|
| 部署到 dev | 创建/更新 Deployment + Service | 滚动更新 |
| 部署到 test | 更新 Deployment 镜像 | 滚动更新 |
| 部署到 staging | 蓝绿部署 | 新版本独立部署，验证后切换 |
| 灰度发布 | 创建灰度 Deployment + 调整副本数比例 | 10% → 50% 逐步调整 |
| 全量发布 | 灰度 Deployment 提升为主，删除旧版本 | 100% 流量切换 |
| 回滚 | rollout undo 或切换到指定版本 | 恢复到历史版本 |

---

## 8. Demo 应用设计

### 8.1 Python (FastAPI)

```python
# demo-apps/python/app.py
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "app": "python-demo",
        "version": os.environ.get("APP_VERSION", "unknown"),
        "language": "Python",
        "hostname": os.environ.get("HOSTNAME", "unknown"),
    }

@app.get("/health")
def health():
    return {"status": "ok"}
```

### 8.2 Go

```go
// demo-apps/go/main.go
package main

import (
    "encoding/json"
    "net/http"
    "os"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        json.NewEncoder(w).Encode(map[string]string{
            "app":      "go-demo",
            "version":  os.Getenv("APP_VERSION"),
            "language": "Go",
            "hostname": os.Getenv("HOSTNAME"),
        })
    })
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
    })
    http.ListenAndServe(":8080", nil)
}
```

### 8.3 Node.js (Express)

```javascript
// demo-apps/node/app.js
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({
        app: 'node-demo',
        version: process.env.APP_VERSION || 'unknown',
        language: 'Node.js',
        hostname: process.env.HOSTNAME || 'unknown',
    });
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.listen(8080);
```

### 8.4 镜像构建与导入

```bash
# scripts/build-demo-images.sh
#!/bin/bash
KIND_CLUSTER="release-demo"

# 构建并导入 Python 应用
docker build -t python-demo:latest demo-apps/python/
kind load docker-image python-demo:latest --name $KIND_CLUSTER

# 构建并导入 Go 应用
docker build -t go-demo:latest demo-apps/go/
kind load docker-image go-demo:latest --name $KIND_CLUSTER

# 构建并导入 Node 应用
docker build -t node-demo:latest demo-apps/node/
kind load docker-image node-demo:latest --name $KIND_CLUSTER
```

---

## 9. 种子数据设计

### 9.1 业务线

| 编码 | 名称 | 排序 |
|------|------|------|
| payment | 支付业务线 | 1 |
| ecommerce | 电商业务线 | 2 |
| platform | 基础平台 | 3 |

### 9.2 环境

| 编码 | 名称 | 排序 | 生产环境 |
|------|------|------|---------|
| dev | 开发环境 | 1 | 否 |
| test | 测试环境 | 2 | 否 |
| staging | 预发环境 | 3 | 否 |
| prod | 生产环境 | 4 | 是 |

### 9.3 集群与命名空间

| 集群 | 环境 | 命名空间 |
|------|------|---------|
| kind-dev | dev | dev |
| kind-test | test | test |
| kind-staging | staging | staging |
| kind-prod | prod | prod |

### 9.4 组织组与用户

| 业务线 | 组 | 用户（归属） | 用户（协作） |
|-------|----|------------|------------|
| 支付业务线 | 支付研发组 | 张三(dev)、李四(dev) | 王五(前端组, 限 payment-frontend) |
| 支付业务线 | 支付测试组 | 赵六(qa) | - |
| 电商业务线 | 电商研发组 | 钱七(dev)、孙八(dev) | 王五(前端组, 限电商前端) |
| 基础平台 | 平台运维组 | 周九(ops) | - |
| 前端组 | 前端组 | 王五(dev)、小刘(dev) | - |

### 9.5 应用

| 应用编码 | 名称 | 语言 | 业务线 | 负责人 |
|---------|------|------|-------|-------|
| payment-api | 支付核心服务 | Go | 支付业务线 | 张三 |
| payment-frontend | 支付前端页面 | Node.js | 支付业务线 | 张三 |
| order-api | 订单服务 | Python | 电商业务线 | 钱七 |
| ecommerce-frontend | 电商前端 | Node.js | 电商业务线 | 王五 |
| user-service | 用户服务 | Go | 基础平台 | 周九 |
| notification-service | 通知服务 | Python | 基础平台 | 周九 |

### 9.6 角色与权限

| 角色 | 编码 | 功能权限 |
|------|------|---------|
| 管理员 | admin | 所有 |
| 发布者 | deployer | 仪表盘、应用管理、发布管理、审批中心、我的权限、部署历史 |
| 发布管理员 | release_manager | 以上 + 发布管理全部操作权限 |
| 审计员 | auditor | 仪表盘、发布管理(只读)、部署历史(只读)、审计日志 |
| 观察者 | viewer | 仪表盘、应用列表(只读)、发布列表(只读) |
| 应用负责人 | app_owner | 发布者权限 + 审批权限 + 应用管理编辑权限 |
| 业务线负责人 | biz_owner | 应用负责人权限 + 权限管理(本业务线范围) |

### 9.7 组权限默认配置

| 组 | 角色 | 资源范围(业务线) | 环境范围 |
|----|------|----------------|---------|
| 支付研发组 | 发布者 | 支付业务线 | dev, test |
| 支付测试组 | 观察者 | 支付业务线 | dev, test, staging, prod |
| 电商研发组 | 发布者 | 电商业务线 | dev, test |
| 平台运维组 | 发布管理员 | 基础平台 | dev, test, staging, prod |
| 前端组 | 发布者 | 前端组应用 | dev, test |

### 9.8 制品仓库

| 名称 | 类型 | 地址 | 默认 |
|------|------|------|------|
| 本地 Docker Registry | docker_registry | localhost:5000 | 是 |
| 本地文件存储 | local | /data/artifacts | 否 |

### 9.9 配置模板与变量

#### payment-api 配置模板

```yaml
# 模板示例: payment-api-config
server:
  port: {{ SERVER_PORT }}
database:
  url: {{ DB_URL }}
  pool_size: {{ DB_POOL_SIZE }}
log:
  level: {{ LOG_LEVEL }}
redis:
  host: {{ REDIS_HOST }}
  password: {{ REDIS_PASSWORD }}
```

| 变量名 | 类型 | 默认值 | 敏感 | dev | test | prod |
|--------|------|--------|------|-----|------|------|
| SERVER_PORT | number | 8080 | 否 | 8080 | 8080 | 8080 |
| DB_URL | string | - | 否 | localhost:5432/payment_dev | test-db:5432/payment_test | prod-db:5432/payment |
| DB_POOL_SIZE | number | 10 | 否 | 5 | 10 | 20 |
| LOG_LEVEL | string | INFO | 否 | DEBUG | DEBUG | INFO |
| REDIS_HOST | string | localhost | 否 | localhost | test-redis:6379 | prod-redis:6379 |
| REDIS_PASSWORD | string | - | 是 | - | - | encrypted_value |

#### 其他应用类似，每个应用都有一个对应的配置模板

### 9.10 初始制品

| 应用 | 版本 | 类型 | 镜像 Tag | 当前环境 |
|------|------|------|---------|---------|
| payment-api | v1.0.0 | docker_image | payment-api:v1.0.0 | prod |
| payment-api | v1.1.0 | docker_image | payment-api:v1.1.0 | staging |
| payment-frontend | v1.0.0 | docker_image | payment-frontend:v1.0.0 | prod |
| order-api | v1.0.0 | docker_image | order-api:v1.0.0 | test |
| user-service | v1.0.0 | docker_image | user-service:v1.0.0 | prod |
| notification-service | v1.0.0 | docker_image | notification-service:v1.0.0 | dev |

---

## 10. 实施计划

### Phase 1: 项目骨架 + 数据模型（3-4 天）

- [ ] 初始化 Django 项目
- [ ] 定义所有 Model（约 20 个表）
- [ ] 执行 makemigrations + migrate
- [ ] 初始化 React 项目（Vite + TypeScript + Ant Design）
- [ ] 配置路由、布局、axios 实例

### Phase 2: 权限系统（3-4 天）

- [ ] 实现用户选择登录 API
- [ ] 实现 JWT 认证中间件
- [ ] 实现组织树 API（业务线 → 组 → 用户）
- [ ] 实现角色 CRUD API
- [ ] 实现组权限配置 API
- [ ] 实现用户个人例外权限 API
- [ ] 实现权限校验核心函数 `can()`
- [ ] 实现数据权限过滤
- [ ] 前端：登录页、组织树组件、权限配置页面

### Phase 3: 应用管理 + 基础设施 + 制品 + 配置（3-4 天）

- [ ] 实现业务线 CRUD API
- [ ] 实现应用 CRUD API
- [ ] 实现环境/集群/命名空间 API
- [ ] 实现资源树 API
- [ ] 实现制品仓库 CRUD API
- [ ] 实现制品 CRUD + 晋级 API
- [ ] 实现配置模板 + 变量 + 变量值 CRUD API
- [ ] 实现配置渲染 + 发布 + 差异对比 API
- [ ] 前端：应用管理页面、环境配置页面
- [ ] 前端：制品管理页面、配置管理页面

### Phase 4: 发布核心模块（3-4 天）

- [ ] 实现发布单 CRUD API
- [ ] 实现发布流水线状态机
- [ ] 实现审批流程 API
- [ ] 实现阶段任务执行/重试
- [ ] 前端：发布列表、创建发布、发布流水线详情

### Phase 5: K8s 集成（2-3 天）

- [ ] 安装 kind 并创建本地集群
- [ ] 实现 K8s 客户端封装
- [ ] 实现滚动更新策略
- [ ] 实现蓝绿部署策略
- [ ] 实现灰度发布策略
- [ ] 实现 Pod 状态监控

### Phase 6: Demo 应用（1 天）

- [ ] 编写三种语言的 Demo 应用
- [ ] 编写 Dockerfile
- [ ] 构建镜像并导入 kind
- [ ] 编写部署脚本

### Phase 7: 联调 + 完善（2-3 天）

- [ ] 前后端联调全链路
- [ ] 补充审计日志
- [ ] 完善仪表盘数据
- [ ] 编写README

---

**总预计：18-23 天**

---

## 11. 后续规划与待办

> 当前版本（v1.0）优先覆盖发布系统的核心闭环能力，以下为已评估但当前版本暂不实现的功能，视后续反馈决定是否补充。

### 11.1 可补充（高 ROI，面试高价值）

| 功能 | 说明 | 预估工时 | 优先级 |
|------|------|---------|--------|
| **发布通知模块** | 站内信 + 模拟飞书消息，关键节点自动通知相关人员 | 2-3 天 | 高 |
| **发布检查清单** | 发布前需确认代码审查、测试通过、安全扫描等检查项 | 0.5 天 | 高 |
| **健康检查 + 自动回滚** | 部署后自动执行健康检查，失败则自动回滚 | 1 天 | 高 |
| **环境锁** | 防止多个发布同时操作同一环境 | 0.5 天 | 中 |
| **DevOps 四指标** | 部署频率、变更前置时间、变更失败率、MTTR 统计 | 1 天 | 中 |

### 11.2 可跳过（对 Demo 无必要或复杂度高）

| 功能 | 跳过理由 |
|------|---------|
| 多级审批流 | 单级审批已能展示流程，多级不会增加 Demo 的展示价值 |
| 发布窗口/黑屏时间 | Demo 环境没有真实的"禁止发布"需求 |
| CI/CD 深度集成 | GitLab CI / Jenkins 集成会增加外部依赖，构建阶段在 Demo 中通过本地 Docker build 模拟 |
| Secrets 加密方案 | 标记 is_secret 在前端用 *** 显示即可，不必实现真正的加密 |
| 灰度自动放量 | 手动控制灰度比例（10% → 50% → 100%）已能展示灰度能力 |
| 多集群/多区域部署 | 本地 kind 只有一个集群，不支持 |
| Service Mesh 集成 | 引入 Istio 等增加过多依赖，偏离 Demo 的本地闭环目标 |