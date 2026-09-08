# 接口权限与数据权限的桥梁：能力声明（Capability Manifest）

> **状态变更（2026-08-04）**：本文已评审并整合并入 `plans/rectification-plan.md`，保留备查，不再单独维护。

> **日期**：2026-08-04
> **背景**：基于 `refactor-plan.md` 阶段 5（数据范围表达式 + filter 增强）的讨论
> **状态**：设计讨论，待评审后进入实施

---

## 1. 问题：两层授权，一座缺桥

当前系统采用**双层叠加**授权模型：

```
请求 → Casbin（接口层：能不能调 API）→ OpenFGA（数据层：能操作哪些数据）→ AND 放行
```

两层独立建模、独立管理，用户在实际操作时面临三个困惑：

### 1.1 我要操作数据 X，需要什么接口权限？

用户知道要查 `host-01` 的详情，但不知道需要 `cmdb:host:read` 还是 `cmdb:host:list`。接口权限与数据模型之间没有显式映射。

### 1.2 我有这个接口权限，能操作哪些数据？

`cmdb:host:read` 接口放行了，但不知道能看到哪几台主机。接口权限的"数据范围"是什么，用户无从得知。

### 1.3 数据权限申请时，怎么知道应该勾选哪些数据？

策略表单里选了"数据模型=host"，然后手动勾选实例——但用户不知道勾哪些才合理，也不知道哪些数据模型与当前操作相关。

### 1.4 问题根源

```
现状：
  应用 → OpenAPI → 权限点（action code）→ 板块模板
  应用 → ????  → 数据模型（resource model）→ 实例

缺失：
  应用 → ????  → 能力声明（哪个 action 操作哪个数据模型）
```

**接口权限与数据权限之间缺少显式的"能力声明"（Capability Declaration）作为桥梁。**

---

## 2. 解决方案：能力声明（Capability Manifest）

### 2.1 核心思路

应用注册时，不仅提交 OpenAPI 文档（生成接口权限点），还需提交一份**能力声明**，显式描述：

- 该应用有哪些**能力**（如"主机管理"）
- 每个能力关联哪些**接口权限点**（action codes）
- 每个能力操作哪个**数据模型**（resource model）
- 每个数据操作支持什么**数据范围类型**（无限制 / owner / 维度 / 实例）

```yaml
# 应用能力声明（capability_manifest.yaml）
app: cmdb
capabilities:
  - name: 主机管理
    actions: [cmdb:host:list, cmdb:host:read, cmdb:host:create, cmdb:host:update, cmdb:host:delete]
    data_model: host
    data_operations:
      - operation: read
        description: 查看主机详情
        required_action: cmdb:host:read
        data_scope: none            # 无限制（有接口权限即可）
      - operation: create
        description: 创建主机
        required_action: cmdb:host:create
        data_scope: none
      - operation: update
        description: 更新主机配置
        required_action: cmdb:host:update
        data_scope: owner           # 仅操作自己的
        default_scope: owner
      - operation: delete
        description: 删除主机
        required_action: cmdb:host:delete
        data_scope: instance        # 需实例级授权
```

### 2.2 三层模型

```
┌─────────────────────────────────────────────────────┐
│  第 1 层：能力声明（Capability Manifest）             │
│  应用声明：我有哪些能力、每个能力操作什么数据           │
├─────────────────────────────────────────────────────┤
│  第 2 层：接口权限（Action）                          │
│  权限点：cmdb:host:read / cmdb:host:update            │
├─────────────────────────────────────────────────────┤
│  第 3 层：数据权限（Resource Scope）                  │
│  数据范围：实例勾选 / 维度筛选 / owner / 全部          │
└─────────────────────────────────────────────────────┘
          ↕ 桥梁是第 1 层（能力声明）
```

### 2.3 数据库设计

```sql
-- 应用能力声明（连接接口权限和数据权限的桥梁）
CREATE TABLE capability_manifests (
    id          BIGSERIAL PRIMARY KEY,
    app_id      BIGINT NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    name        VARCHAR(128) NOT NULL,          -- 能力名称："主机管理"
    data_model  VARCHAR(128),                   -- 操作的数据模型（可空=纯接口能力）
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(app_id, name)
);

-- 能力 → 权限点关联（哪个权限点操作哪个数据模型的什么操作）
CREATE TABLE capability_actions (
    capability_id   BIGINT NOT NULL REFERENCES capability_manifests(id) ON DELETE CASCADE,
    action_id       BIGINT NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
    data_operation  VARCHAR(32) DEFAULT 'read',  -- read / write / list / create / delete
    data_scope      VARCHAR(32) DEFAULT 'none',  -- none / owner / dimension / instance
    description     VARCHAR(256),
    PRIMARY KEY (capability_id, action_id)
);
```

### 2.4 GORM 模型

```go
// CapabilityManifest 应用能力声明（接口权限 ↔ 数据权限 桥梁）
type CapabilityManifest struct {
    Base
    AppID       uint64 `gorm:"uniqueIndex:idx_cap_app_name;not null" json:"app_id"`
    Name        string `gorm:"size:128;not null" json:"name"`           // "主机管理"
    DataModel   string `gorm:"size:128" json:"data_model"`             // "host"（可空=纯接口能力）
    Description string `gorm:"size:512" json:"description"`
}

// CapabilityAction 能力 → 权限点 → 数据操作映射
type CapabilityAction struct {
    CapabilityID  uint64 `gorm:"primaryKey" json:"capability_id"`
    ActionID      uint64 `gorm:"primaryKey" json:"action_id"`
    DataOperation string `gorm:"size:32;default:'read'" json:"data_operation"` // read/write/list
    DataScope     string `gorm:"size:32;default:'none'" json:"data_scope"`     // none/owner/dimension/instance
    Description   string `gorm:"size:256" json:"description"`
}
```

---

## 3. 前端交互设计

### 3.1 权限市场：能力目录

```
┌─────────────────────────────────────────────────┐
│  cmdb — 配置管理数据库                            │
│                                                   │
│  能力目录：                                        │
│  ┌─────────────────────────────────────────────┐ │
│  │ 主机管理                                     │ │
│  │  接口：host:list / read / create / update    │ │
│  │  数据：host 模型                              │ │
│  │  read → 无限制  update → 仅 owner            │ │
│  │  [申请接口权限]  [申请数据权限]               │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ 网络管理                                     │ │
│  │  接口：network:list / read / create          │ │
│  │  数据：network 模型                           │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 3.2 智能申请表单

当用户点击"申请数据权限"时，系统自动检测前置条件：

```
┌─────────────────────────────────────────────────┐
│  申请数据权限：host 模型（更新操作）              │
│                                                   │
│  前置条件（自动检测）：                            │
│  ✅ 您已有 cmdb:host:read 接口权限               │
│  ❌ 您缺少 cmdb:host:update 接口权限              │
│     → [同时申请接口权限]（联动勾选）              │
│                                                   │
│  数据范围：                                       │
│  ○ 全部主机（data_scope: none）                   │
│  ● 仅自己的主机（data_scope: owner）              │
│  ● 按维度筛选（data_scope: dimension）：          │
│    组织 IN [payment, billing]                     │
│  ● 按实例勾选（data_scope: instance）：           │
│    □ host-01  □ host-02  □ host-03               │
│                                                   │
│  [提交申请]                                       │
└─────────────────────────────────────────────────┘
```

### 3.3 我的权限：反向查询

```
┌─────────────────────────────────────────────────┐
│  我的权限：alice                                  │
│                                                   │
│  已有接口权限：                                    │
│  ┌─────────────────────────────────────────────┐ │
│  │ cmdb:host:read                              │ │
│  │  关联能力：主机管理（查看）                   │ │
│  │  可操作数据：全部 host（无限制）              │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ cmdb:host:update                            │ │
│  │  关联能力：主机管理（更新）                   │ │
│  │  可操作数据：仅 owner 主机                   │ │
│  │  实例：host-01, host-02                      │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 4. API 设计

### 4.1 管理 API（应用 owner 声明能力）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/apps/:id/capabilities` | 查看应用能力清单 |
| POST | `/api/v1/apps/:id/capabilities` | 声明新能力 |
| PUT | `/api/v1/apps/:id/capabilities/:cid` | 更新能力声明 |
| DELETE | `/api/v1/apps/:id/capabilities/:cid` | 删除能力 |
| POST | `/api/v1/apps/:id/capabilities/:cid/actions` | 绑定能力 → 权限点 |
| POST | `/api/v1/apps/:id/sync-capabilities` | 从 OpenAPI 自动生成能力声明 |

### 4.2 查询 API（权限市场 + 智能申请）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/marketplace/capabilities` | 浏览所有应用的能力目录 |
| GET | `/api/v1/marketplace/capabilities/:cid/prereqs` | 查询申请某能力的前置条件 |
| GET | `/api/v1/users/:uid/my-permissions` | 反向查询：我的权限 + 可操作数据范围 |

### 4.3 能力与数据范围的关系查询

```
GET /api/v1/marketplace/capabilities/:cid/prereqs?user=alice

Response:
{
  "capability": "主机管理",
  "data_model": "host",
  "prereqs": {
    "has_actions": ["cmdb:host:read"],
    "missing_actions": ["cmdb:host:update"],
    "can_apply_data_scope": ["owner", "dimension", "instance"]
  }
}
```

---

## 5. 自动化：从 OpenAPI 生成能力声明

OpenAPI 同步时，可以**半自动**生成能力声明：

```go
// 从 OpenAPI tag 推断能力名称
// 从 HTTP method 推断数据操作类型
// 从 path 参数推断数据模型
func inferCapabilityFromAPI(tag string, actions []Action) CapabilityManifest {
    cap := CapabilityManifest{Name: tag}
    for _, a := range actions {
        if strings.Contains(a.Path, "/{id}") {
            cap.DataModel = extractModel(a.Path)  // /api/v1/hosts/{id} → "host"
        }
        switch a.Method {
        case "GET":
            if strings.Contains(a.Path, "/{id}") {
                bindAction(a, "read", "owner")
            } else {
                bindAction(a, "list", "none")
            }
        case "POST":
            bindAction(a, "create", "none")
        case "PUT", "PATCH":
            bindAction(a, "update", "instance")
        case "DELETE":
            bindAction(a, "delete", "instance")
        }
    }
    return cap
}
```

这样应用 owner 只需**确认/微调**自动生成的能力声明，而非从零创建。

---

## 6. 实施计划

### 阶段 A：模型 + 存储层（0.5 天）
- 新增 `CapabilityManifest` / `CapabilityAction` 模型
- AutoMigrate 建表
- Repository CRUD 方法

### 阶段 B：API 层（1 天）
- 应用 owner 声明/管理能力的 API
- 权限市场查询 API
- 智能前置条件检测 API

### 阶段 C：OpenAPI 自动生成（0.5 天）
- `sync-applications` 时自动推断能力声明
- Owner 确认/微调 UI

### 阶段 D：前端（1 天）
- 权限市场能力目录页
- 智能申请表单（自动检测前置条件）
- 我的权限反向查询页

### 阶段 E：与 seed 集成（0.5 天）
- `seed.go` 中为 cmdb 应用生成能力声明
- 演示脚本覆盖能力声明流程

**合计约 3.5 天**

---

## 7. 设计原则

| 原则 | 说明 |
|------|------|
| **声明式，非推断** | 应用 owner 显式声明能力，系统不靠猜测 |
| **半自动化** | OpenAPI 同步时自动推断，owner 确认即可 |
| **桥梁在应用侧** | 能力声明由应用 owner 维护，权限中心只消费 |
| **可选但推荐** | 没有声明的应用仍可正常工作，但权限市场不展示 |
| **向前兼容** | 现有策略无需迁移，能力声明是新增维度 |
