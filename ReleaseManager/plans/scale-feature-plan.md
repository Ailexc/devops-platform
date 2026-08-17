# 实例伸缩功能实施计划

> 日期: 2026-08-01
> 状态: 待审核

---

## 一、功能概述

统一抽象"实例伸缩"能力，覆盖 K8s 和 EC2 两种部署模式：

| 操作 | K8s | EC2 |
|------|-----|-----|
| 停机 | `scale --replicas=0` | 关机 |
| 启动 | `scale --replicas=N` | 开机 |
| 扩容 | `scale --replicas=N+M` | 增加机器 |
| 缩容 | `scale --replicas=N-M` | 减少机器 |

**审批逻辑**：所有操作统一按环境的 `ReleaseApprovalConfig` 配置，与发布审批逻辑一致。

**实例数上限**：由应用管理中的 `AppEnvConfig.replicas`（环境副本数配置）决定。扩容不能超过此上限，因为 EC2 实例需要提前申请资源，不像 Pod 可以随意创建。

---

## 二、数据模型变更

### 2.1 Environment 新增 `deploy_type`

```python
# backend/apps/infrastructures/models.py
DEPLOY_TYPES = [
    ('k8s', 'Kubernetes'),
    ('ec2', 'EC2 / 虚拟机'),
]

class Environment(models.Model):
    # ... 现有字段不动
    deploy_type = models.CharField(max_length=8, choices=DEPLOY_TYPES, default='k8s',
                                   verbose_name="部署类型")
```

### 2.2 Application 移除 `deploy_mode`

- 删除 `Application.deploy_mode` 字段
- Migration 设 `null=True` 过渡，后续清理

### 2.3 AppEnvConfig 现有字段（无需变更）

`AppEnvConfig.replicas` 已存在，作为该应用在该环境下的**配置副本数/实例数上限**。

### 2.4 种子数据

| 环境 | deploy_type |
|------|-------------|
| dev, dev2 | k8s |
| test1~test5 | k8s |
| pre1, pre2 | k8s |
| prod1 | ec2 |
| prod2 | k8s |

---

## 三、后端 API

### 3.1 新增接口 `POST /api/v1/apps/{id}/scale/`

**Request:**
```json
{
  "env_code": "dev",
  "target_replicas": 0,
  "reason": "夜间停机节省资源"
}
```

**Response（无需审批时直接执行）:**
```json
{
  "code": 200,
  "data": {
    "requires_approval": false,
    "execution_id": "xxx",
    "message": "缩容成功: 2 → 0"
  }
}
```

**Response（需要审批时）:**
```json
{
  "code": 200,
  "data": {
    "requires_approval": true,
    "message": "扩容需审批，已提交审批单"
  }
}
```

**校验逻辑：**
```python
# target_replicas 不能超过 AppEnvConfig.replicas
env_config = AppEnvConfig.objects.get(application=app, environment=env)
if target_replicas > env_config.replicas:
    return error("目标实例数不能超过应用配置的环境副本数上限")
```

### 3.2 审批逻辑

查询 `ReleaseApprovalConfig`（按 env_type）：

```python
config = ReleaseApprovalConfig.objects.get(env_type=env.env_type)
if config.requires_approval:
    # 创建审批单
else:
    # 直接执行
```

**所有操作（停机/启动/扩容/缩容）统一按此配置，不做任何特殊判断。**

---

## 四、前端 UI 变更

### 4.1 应用详情页 — 环境配置区

**新增"编辑"按钮**（本次只加按钮，功能后续实现）：

```
┌─────────────────────────────────────────────┐
│  环境配置                                    │
├─────────────────────────────────────────────┤
│  环境      副本数  部署策略    操作           │
│  ─────────────────────────────────────────── │
│  dev       2      滚动更新    [编辑]         │
│  test1     2      滚动更新    [编辑]         │
│  pre1      2      蓝绿部署    [编辑]         │
│  prod1     4      滚动更新    [编辑]         │
└─────────────────────────────────────────────┘
```

> 点击"编辑"按钮：本次先弹提示"功能开发中"，后续实现完整的编辑弹窗。
> 编辑副本数时会触发审批逻辑（因为改副本数上限意味着资源申请）。

### 4.2 应用详情页 / 发布详情页 — 实例伸缩操作区

**上限来源**：`AppEnvConfig.replicas`（应用管理中配置的环境副本数）

```
┌─────────────────────────────────────────────┐
│  应用: python-app    环境: dev (K8s)         │
├─────────────────────────────────────────────┤
│                                             │
│  当前实例:  2/2 Pods Running                 │
│  配置上限:  2（应用管理 → 环境配置）          │
│                                             │
│  ┌─────┐  ┌─────┐  ┌─────┐                 │
│  │ - 1 │  │  2  │  │ + 1 │  目标实例数       │
│  └─────┘  └─────┘  └─────┘                 │
│  (0~2 范围，不能超过配置上限)                 │
│                                             │
│  [  停机  ]        [  扩缩容  ]              │
│                                             │
└─────────────────────────────────────────────┘
```

**EC2 模式差异：**
- "2/2 Pods Running" → "2 台机器运行中"
- 显示机器 IP 列表（模拟数据）
- 上限同理受 `AppEnvConfig.replicas` 限制

---

## 五、文件变更清单

| # | 文件 | 操作 | 说明 |
|---|------|------|------|
| 1 | `backend/apps/infrastructures/models.py` | 修改 | Environment 加 `deploy_type` |
| 2 | `backend/apps/applications/models.py` | 修改 | 移除 `deploy_mode` |
| 3 | `backend/apps/infrastructures/serializers.py` | 修改 | 序列化新增 `deploy_type` |
| 4 | `backend/apps/applications/serializers.py` | 修改 | 移除 `deploy_mode`，env_config 加 deploy_type |
| 5 | `backend/apps/infrastructures/views.py` | 修改 | 新增 scale API |
| 6 | `backend/apps/accounts/management/commands/init_seed.py` | 修改 | 更新环境种子数据 |
| 7 | `executor/app/runner.py` | 修改 | `_do_scale` 支持 ec2 分支 |
| 8 | `frontend/src/api/index.ts` | 修改 | 新增 scale API |
| 9 | `frontend/src/pages/apps/detail.tsx` | 修改 | 环境配置加编辑按钮 + 伸缩操作组件 |
| 10 | `frontend/src/pages/releases/app-detail.tsx` | 修改 | 新增伸缩操作组件 |
| 11 | `frontend/src/pages/infrastructures/index.tsx` | 修改 | 环境卡片显示 deploy_type |

---

## 六、不做的事情

- ❌ EC2 真实 SSH 操作（Demo 系统只做 UI + 模拟日志）
- ❌ 自动扩缩容（HPA）
- ❌ 独立扩缩容历史页面（复用 DeployHistory）
- ❌ Application.deploy_mode 保留（无意义，以环境为准）
- ❌ 环境副本数编辑弹窗（本次只加按钮，功能后续实现）
