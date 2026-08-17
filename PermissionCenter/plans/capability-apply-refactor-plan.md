# 能力打包申请流程改造实施计划

> 基于 Demo v5 确认的交互方案，将"以能力为中心的打包申请流程"落地到实际代码
> 日期：2026-08-04

---

## ✅ 实施状态（2026-08-04 已完成）

> Phase 1（后端基础）+ Phase 2（前端向导）+ Phase 3（后端提交增强）已全部落地并 e2e 验证。

| 模块 | 完成内容 | 验证 |
|------|---------|------|
| 数据模型 | `CapabilityManifest` 增 `model_fields`/`scope_definitions`/`presets`/`tags`（JSONB，新增 `JSONAny` 类型） | AutoMigrate + seed 通过 |
| 能力 CRUD | 创建/更新支持 4 个新字段；新增 `GET /api/v1/capabilities/:cid/scope-options`（静态选项 + instance 实例列表） | API 200 |
| 权限市场 | 返回 presets 解析（action_codes→action_ids+ops）+ 搜索/筛选（q/app/model/tag） | API 验证通过 |
| 申请增强 | `submitRequest` 支持 `capability_id`/`preset_id`/`scope`/`scope_params`；风险组合升级（§5.4）；条件表达式生成并落申请单 | 低/中/高全场景验证 |
| 申请预览 | `POST /api/v1/requests/preview`：风险 + 审批链（含用户名/角色）+ 表达式 + 范围标签，不落库 | 前端 Step 5 使用 |
| 种子数据 | cmdb 能力富数据 + CloudPortal（public_resource，viewer/manager 预设，account/tag/instance 范围） | 市场 4 卡片 |
| 前端市场页 | 能力包卡片 + 搜索/标签筛选 + 5 步向导（浏览→主体→组合→范围→确认）+ 动态范围表单 + 实时表达式 + 提交成功 | 浏览器全流程走通 |

**已知遗留（后续迭代）**：
- `Requests.vue` 详情展示条件表达式（P1，当前申请单 content 已存 `scope_expression`，仅未在列表 UI 展示）
- `AppDetail.vue` 能力声明编辑表单补充新字段（P2，计划本就标注"可延后"）
- 前端样式按现有 BW 设计系统实现（与全站黑白风格一致，未采用计划 §2.0 的蓝色明亮主题，避免与既有设计系统冲突）

---

## 0. 现状 vs 目标

### 0.1 当前已具备（无需改动）

| 模块 | 已有能力 | 代码位置 |
|------|---------|---------|
| 申请主体类型 | `ApplicantSubjectType`（1=我/2=组/3=组织/4=应用） | `model/governance.go` |
| 申请提交 API | 支持 `subject_type`/`subject_id`/`risk_level` | `handler_governance.go:submitRequest` |
| 审批链构建 | 按主体类型 + 风险等级动态调整 | `handler_governance.go:buildApprovalChain` |
| 风险自动升级 | 下游应用 → 至少中风险 | `handler_governance.go` |
| 能力声明模型 | `CapabilityManifest` + `CapabilityAction` | `model/capability.go` |
| 能力声明 CRUD | 创建/编辑/发布/下架 | `handler_capability.go` |
| 权限市场 API | 已发布能力列表 + 策略模板 | `handler_marketplace.go` |
| 前端申请表单 | 有主体选择 + 预检联动 | `Marketplace.vue` |

### 0.2 需要新增/改造

| 改造项 | 当前状态 | 目标状态 |
|--------|---------|---------|
| 能力声明模型 | 只有 `name`/`data_model`/`actions` | 增加 `scope_definitions`/`model_fields`/`presets` |
| 权限市场展示 | 扁平列表（单个能力+动作） | 能力包卡片（含权限组合标签） |
| 申请流程 | 弹窗表单（扁平） | 5步向导（浏览→主体→组合→范围表单→确认） |
| 数据范围选择 | 下拉选择 `all/owner/dimension/instance` | 动态表单（select/input/expression/instance） |
| 条件表达式 | 不展示 | 实时展示 Casbin/OpenFGA 表达式 |
| 种子数据 | 基础能力声明 | 含 `scope_definitions`/`model_fields`/`presets` |

---

## 1. 后端改造

### 1.1 数据模型扩展（`model/capability.go`）

**CapabilityManifest 增加 3 个 JSONB 字段：**

```go
type CapabilityManifest struct {
    // ... 现有字段 ...
    ModelFields     JSONMap    `gorm:"type:jsonb" json:"model_fields"`      // 数据模型字段定义
    ScopeDefinitions JSONMap    `gorm:"type:jsonb" json:"scope_definitions"` // 数据范围表单模板
    Presets         JSONMap    `gorm:"type:jsonb" json:"presets"`           // 权限组合预设
    Tags            StringArray `gorm:"type:jsonb" json:"tags"`             // 标签（用于搜索和筛选）
}
```

**字段说明：**

| 字段 | 结构 | 说明 |
|------|------|------|
| `model_fields` | `[{name, type, desc, indexed}]` | 数据模型的字段列表，决定哪些条件可用 |
| `scope_definitions` | `{scope: {label, type, source, options, ...}}` | 每种数据范围的表单定义 |
| `presets` | `[{id, name, icon, desc, action_codes, allowed_scopes}]` | 权限组合预设 |
| `tags` | `["CMDB", "host", "主机", "运维"]` | 搜索标签（应用名+数据模型+业务关键词） |

**scope_definitions 支持的表单类型：**

| type | 说明 | 后端处理 |
|------|------|---------|
| `auto` | 系统自动处理（如 all/owner） | 无需用户输入 |
| `select` | 从选项列表选择 | `source: static` 或 `source: api, api: /path` |
| `input` | 自由输入 | 带 `placeholder`/`validation_hint` |
| `expression` | 表达式输入 | 带 `examples`/`validation_hint` |
| `instance` | 实例选择器 | `source: api, api: /path` |

**工作量：0.5 天**

---

### 1.2 能力声明 API 扩展（`handler_capability.go`）

**改动点：**

1. `createCapability` / `updateCapability` — 接收并存储 `model_fields`/`scope_definitions`/`presets`
2. `getCapabilities` — 返回时携带新字段
3. 新增 `GET /api/v1/capabilities/:id/scope-options?scope=xxx` — 动态获取 scope 选项（如从 API 获取云账号列表）

**工作量：0.5 天**

---

### 1.3 权限市场 API 扩展（`handler_marketplace.go`）

**改动点：**

1. `marketplaceCapabilities` — 返回时携带 `presets`/`scope_definitions`（前端需要用来渲染卡片和表单）
2. 新增 `POST /api/v1/requests/preview` — 预览申请单（含条件表达式生成），不实际提交

**工作量：0.5 天**

---

### 1.4 申请提交 API 增强（`handler_governance.go`）

**改动点：**

1. `submitRequest` — 增加 `capability_id`/`preset_id`/`scope`/`scope_params` 字段支持
2. `buildApprovalChain` — 根据 `preset_id` 和 `scope` 调整风险等级（如"完整管理+所有数据"组合升级为高风险）
3. 条件表达式生成逻辑 — 根据 scope + scope_params 生成 Casbin/OpenFGA 表达式存储到申请单

**工作量：1 天**

---

### 1.5 种子数据更新（`seed.go`）

**改动点：**

为 cmdb 应用的能力声明增加：
- `model_fields`: `[{name: "owner_id", type: "string"}, {name: "org_id", type: "string"}, ...]`
- `scope_definitions`: 各种 scope 的表单定义
- `presets`: 只读查看/运维操作/完整管理 三个预设
- `tags`: `["CMDB", "host", "主机", "配置管理", "运维"]`

为新增的"公共资源池"应用（CloudPortal）创建：
- 完整的能力声明（含 model_fields/scope_definitions/presets/tags）
- 对应的 actions、种子策略
- `tags`: `["CloudPortal", "public_resource", "公共资源", "云账号", "标签"]`

**工作量：1 天**

---

## 2. 前端改造

### 2.0 权限市场 UI/UX 设计规范

#### 2.0.1 设计原则

| 原则 | 说明 |
|------|------|
| **明亮现代** | 白色背景 + 蓝色主色调 + 圆角卡片 + 柔和阴影，拒绝暗黑风格 |
| **信息密度适中** | 卡片式布局，每行 2-3 个能力包，留白充足 |
| **标签驱动** | 每个能力包带多维标签（应用/数据模型/权限组合），支持搜索和筛选 |
| **渐进披露** | 卡片展示摘要，点击展开详情，不一次性堆砌所有信息 |

#### 2.0.2 色彩系统

```css
/* 明亮风格主题变量 */
--primary: #2563eb;          /* 蓝色主色 */
--primary-light: #3b82f6;    /* 浅蓝 */
--primary-bg: #eff6ff;       /* 极浅蓝背景 */
--success: #16a34a;          /* 绿色 */
--success-bg: #f0fdf4;       /* 极浅绿 */
--warning: #d97706;          /* 橙色 */
--warning-bg: #fffbeb;       /* 极浅橙 */
--danger: #dc2626;           /* 红色 */
--gray-50: #f9fafb;          /* 背景 */
--gray-100: #f3f4f6;         /* 卡片背景 */
--gray-200: #e5e7eb;         /* 边框 */
--gray-500: #6b7280;         /* 次要文字 */
--gray-900: #111827;         /* 主文字 */
--radius: 12px;              /* 圆角 */
--radius-sm: 8px;
--shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
--shadow-md: 0 4px 6px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
```

#### 2.0.3 标签体系

每个能力包展示以下标签，支持搜索和筛选：

| 标签类型 | 颜色 | 示例 | 说明 |
|---------|------|------|------|
| **应用标签** | 蓝色 `primary-bg` | `CMDB` `CloudPortal` `Monitor` | 能力所属应用，点击可按应用筛选 |
| **数据模型标签** | 紫色 `purple-bg` | `host` `network` `public_resource` | 关联的数据模型，空则显示"纯接口" |
| **权限组合标签** | 绿色 `success-bg` | `👁️ 只读` `🔧 运维` `⚡ 完整` | 包含的预设权限组合 |
| **状态标签** | 灰色/绿色 | `已发布` `v1` | 版本和状态 |
| **申请热度标签** | 橙色 `warning-bg` | `🔥 热门` `被申请 12 次` | 申请次数（可选） |

#### 2.0.4 搜索与筛选栏

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 搜索能力名称、描述、应用...          [应用 ▾] [模型 ▾] │
├─────────────────────────────────────────────────────────────┤
│  标签筛选：                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ CMDB ✓ │ │ Monitor│ │ host   │ │ network│ │ 全部   │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
└─────────────────────────────────────────────────────────────┘
```

- **搜索框**：全文搜索（名称 + 描述 + 应用名 + 数据模型）
- **应用筛选**：下拉选择应用，支持多选
- **模型筛选**：下拉选择数据模型
- **标签云**：点击标签快速筛选，支持多选组合

#### 2.0.5 能力包卡片设计

```
┌──────────────────────────────────────────────────────────────┐
│  🖥️  主机管理                                    [CMDB]      │
│  ─────────────────────────────────────────────────────────── │
│  主机资源的完整生命周期管理                                    │
│                                                              │
│  数据模型: host                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 👁️ 只读  │ │ 🔧 运维  │ │ ⚡ 完整  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                              │
│  接口: GET /hosts · GET /hosts/:id · POST /hosts · ...      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              [ 📋 申请此能力 ]                        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**卡片结构：**
- **头部**：图标 + 名称 + 应用标签（右上角）
- **描述**：能力描述文字
- **标签区**：数据模型标签 + 权限组合标签（pill 样式）
- **接口预览**：折叠显示包含的接口（默认显示前 3 个，展开显示全部）
- **操作区**：「申请此能力」按钮（蓝色圆角按钮）

**交互：**
- 卡片 hover：轻微上浮 + 阴影加深
- 点击卡片：展开详情（接口列表 + 数据范围说明）
- 点击「申请」：进入 5 步向导

#### 2.0.6 5 步向导 UI 设计

**向导容器：**
```
┌──────────────────────────────────────────────────────────────┐
│  ① 浏览能力  →  ② 申请主体  →  ③ 权限组合  →  ④ 数据范围  →  ⑤ 确认  │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [当前步骤内容]                                              │
│                                                              │
│  ┌──────────┐  ┌──────────────────────────────────────────┐ │
│  │ ← 上一步 │  │                    下一步 →              │ │
│  └──────────┘  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**步骤指示器：**
- 圆形数字 + 文字标签
- 当前步骤：蓝色填充
- 已完成：绿色填充 + 勾号
- 未完成：灰色边框

#### 2.0.7 响应式布局

| 断点 | 卡片列数 | 说明 |
|------|---------|------|
| ≥1200px | 3 列 | 桌面端 |
| 768-1199px | 2 列 | 平板 |
| <768px | 1 列 | 手机 |

#### 2.0.8 组件清单

| 组件 | 说明 | 复用性 |
|------|------|--------|
| `CapabilityCard.vue` | 能力包卡片 | 权限市场 + 应用详情 |
| `TagFilter.vue` | 标签筛选栏 | 权限市场 + 其他列表页 |
| `StepWizard.vue` | 5 步向导容器 | 申请流程 + 其他向导 |
| `SubjectSelector.vue` | 申请主体选择 | 申请流程 |
| `PresetSelector.vue` | 权限组合选择 | 申请流程 |
| `ScopeForm.vue` | 动态数据范围表单 | 申请流程 |
| `ExpressionPreview.vue` | 条件表达式预览 | 申请流程 + 我的权限 |
| `RequestPreview.vue` | 申请单预览 | 申请流程 + 审批页面 |

### 2.1 权限中心页面重构（`Marketplace.vue`）

**当前：** 扁平列表 + 弹窗表单
**目标：** 能力包卡片 + 5 步向导

**改造内容：**

| 步骤 | 内容 | 组件 |
|------|------|------|
| Step 1: 浏览能力 | 能力包卡片网格（图标/名称/应用/描述/权限组合标签） | 新增 `CapabilityCard.vue` |
| Step 2: 申请主体 | 4 种主体卡片 + 具体实例选择器 | 新增 `SubjectSelector.vue` |
| Step 3: 权限组合 | 权限组合卡片（只读/运维/完整管理） | 新增 `PresetSelector.vue` |
| Step 4: 数据范围 | 动态表单（根据 scope_definitions 渲染） | 新增 `ScopeForm.vue` + `ExpressionEditor.vue` + `InstanceSelector.vue` |
| Step 5: 确认申请 | 预览（主体/能力/组合/范围/表达式/审批链） | 新增 `RequestPreview.vue` |

**工作量：3 天**

---

### 2.2 申请/审批页面增强（`Requests.vue`）

**改动点：**

1. 申请列表增加"方向"列（自助申请 / owner 授权）
2. 申请列表增加"申请主体"列（我/组/组织/应用）
3. 申请详情展示条件表达式

**工作量：0.5 天**

---

### 2.3 API 客户端扩展（`api/client.ts`）

**新增方法：**

```typescript
// 能力声明 scope 选项
capabilityScopeOptions: (id: number, scope: string) =>
  request(`/api/v1/capabilities/${id}/scope-options?scope=${scope}`),

// 申请单预览（不提交）
previewRequest: (r: any) =>
  request('/api/v1/requests/preview', 'POST', r),
```

**工作量：0.5 天**

---

### 2.4 应用详情页调整（`AppDetail.vue`）

**改动点：**

1. 能力声明编辑表单增加 `model_fields`/`scope_definitions`/`presets` 编辑
2. 这部分可以后续迭代，先用 seed 数据验证流程

**工作量：1 天（可延后）**

---

## 3. 工作量汇总

| 模块 | 任务 | 工作量 | 优先级 |
|------|------|--------|--------|
| **后端** | | | |
| model/capability.go | 增加 3 个 JSONB 字段 + tags 字段 | 0.5d | P0 |
| handler_capability.go | CRUD 支持新字段 + scope-options API + 搜索筛选 | 0.5d | P0 |
| handler_marketplace.go | 返回 presets/scope_definitions/tags + 搜索筛选支持 | 0.5d | P0 |
| handler_governance.go | submitRequest 增强 + 表达式生成 | 1d | P0 |
| seed.go | cmdb + CloudPortal 种子数据（含 tags） | 1d | P0 |
| **前端** | | | |
| Marketplace.vue | 能力包卡片 + 标签筛选 + 搜索 + 5 步向导 | 4d | P0 |
| Requests.vue | 申请列表增强 | 0.5d | P1 |
| api/client.ts | 新增 API 方法 | 0.5d | P0 |
| AppDetail.vue | 能力声明编辑表单 | 1d | P2 |
| **合计** | | **9.5d** | |

---

## 4. 执行计划

### Phase 1：后端基础（2 天）

```
Day 1 上午: model/capability.go 增加字段 + AutoMigrate
Day 1 下午: handler_capability.go 扩展 + scope-options API
Day 2 上午: handler_marketplace.go 返回新字段
Day 2 下午: seed.go 更新种子数据（cmdb + CloudPortal）
```

**验收：** API 返回含 `presets`/`scope_definitions`/`model_fields` 的能力声明

### Phase 2：前端向导 + UI 改造（4.5 天）

```
Day 3: Marketplace.vue 骨架 + 标签筛选栏 + 搜索框 + 能力包卡片网格
Day 4: Step 1（浏览能力卡片）+ Step 2（申请主体选择）
Day 5: Step 3（权限组合选择）+ Step 4（动态数据范围表单）+ 条件表达式展示
Day 6: Step 5（确认预览 + 审批链展示）+ 向导交互细节
Day 7 上午: api/client.ts 新增方法 + Requests.vue 增强
```

**验收：** 完整 5 步向导可走通，条件表达式实时展示

### Phase 3：后端提交增强（1 天）

```
Day 7 上午: handler_governance.go submitRequest 支持 capability_id/preset_id/scope/scope_params
Day 7 下午: 条件表达式生成逻辑 + 风险等级组合升级
```

**验收：** 提交申请后，申请单含条件表达式，审批链正确

### Phase 4：联调验收（1 天）

```
Day 8: e2e 联调 + demo.sh 更新 + bug 修复
```

**验收：** `demo.sh` 全链路通过，前端 5 步流程完整可演示

---

## 5. 技术细节

### 5.1 scope_definitions 数据结构示例

```json
{
  "all": {
    "label": "所有数据",
    "type": "auto",
    "desc": "无需填写，自动获得全部数据权限"
  },
  "owner": {
    "label": "仅我创建的",
    "type": "auto",
    "desc": "系统自动判断，基于 owner_id 字段"
  },
  "dimension": {
    "label": "按组织过滤",
    "type": "select",
    "desc": "选择你要访问的组织范围",
    "source": "static",
    "options": [
      {"value": "dept-dev-1", "label": "研发一部", "meta": "总公司 → 研发中心 → 研发一部"},
      {"value": "dept-dev-2", "label": "研发二部", "meta": "总公司 → 研发中心 → 研发二部"}
    ]
  },
  "instance": {
    "label": "选择具体实例",
    "type": "instance",
    "desc": "勾选你要访问的主机实例",
    "source": "api",
    "api": "/api/v1/resource-models/:model_id/instances"
  },
  "tag": {
    "label": "按标签过滤",
    "type": "expression",
    "desc": "输入标签表达式",
    "placeholder": "dept=研发部 AND env=prod",
    "examples": ["dept=研发部", "env=prod", "dept=研发部 AND env=prod"],
    "validation_hint": "格式: key=value [AND|OR key=value]"
  }
}
```

### 5.2 presets 数据结构示例

```json
[
  {
    "id": "readonly",
    "name": "只读查看",
    "icon": "👁️",
    "desc": "查看主机列表和详情",
    "action_codes": ["cmdb:host:list", "cmdb:host:read"],
    "allowed_scopes": ["all", "owner", "dimension", "instance"]
  },
  {
    "id": "operator",
    "name": "运维操作",
    "icon": "🔧",
    "desc": "查看 + 创建 + 更新",
    "action_codes": ["cmdb:host:list", "cmdb:host:read", "cmdb:host:create", "cmdb:host:update"],
    "allowed_scopes": ["all", "owner", "dimension", "instance"]
  },
  {
    "id": "full",
    "name": "完整管理",
    "icon": "⚡",
    "desc": "全部操作权限",
    "action_codes": ["cmdb:host:list", "cmdb:host:read", "cmdb:host:create", "cmdb:host:update", "cmdb:host:delete"],
    "allowed_scopes": ["all", "owner", "dimension", "instance"]
  }
]
```

### 5.3 条件表达式生成逻辑

```go
func buildScopeExpression(scope string, params map[string]any, cap *CapabilityManifest) string {
    model := cap.DataModel
    switch scope {
    case "all":
        return fmt.Sprintf("// Casbin 动作级\np, {user}, {app}, {actions}, *, allow\n// 无数据层限制")
    case "owner":
        return fmt.Sprintf("// OpenFGA 关系\n(%s:xxx, owner, user:{user})\n→ Check(user:{user}, reader, %s:xxx) if owner_id == {user}", model, model)
    case "dimension":
        dim := params["dimension"].(string)
        return fmt.Sprintf("// OpenFGA 组织维度\n(group:%s, member, user:{user})\n(%s:xxx, org, group:%s)\n→ ListObjects filter org=%s", dim, model, dim, dim)
    case "instance":
        ids := params["instance_ids"].([]uint64)
        // 生成 tuple 列表
        // ...
    case "tag":
        expr := params["expression"].(string)
        return fmt.Sprintf("// Casbin ABAC\np, {user}, {app}, {actions},\n  { %s }, allow", expr)
    }
}
```

### 5.4 风险等级组合升级规则

| 权限组合 | 数据范围 | 风险等级 |
|---------|---------|---------|
| 只读查看 | 所有数据 | 低 → 中 |
| 只读查看 | owner/dimension/instance | 低 |
| 运维操作 | 所有数据 | 中 |
| 运维操作 | 其他 | 低 → 中 |
| 完整管理 | 任意 | 中 → 高 |
| 任意 + 下游应用 | 任意 | 至少中 |

---

## 6. 验收标准

### 6.1 后端验收

- [ ] `GET /api/v1/marketplace/capabilities` 返回含 `presets`/`scope_definitions` 的能力列表
- [ ] `GET /api/v1/capabilities/:id/scope-options?scope=dimension` 返回选项列表
- [ ] `POST /api/v1/requests` 支持 `capability_id`/`preset_id`/`scope`/`scope_params`
- [ ] 申请单创建后含条件表达式
- [ ] 审批链根据主体类型 + 风险组合正确生成

### 6.2 前端验收

- [ ] 权限中心页面展示能力包卡片（图标/名称/应用/描述/权限组合标签）
- [ ] 标签筛选栏：应用标签、数据模型标签、权限组合标签，支持多选组合筛选
- [ ] 搜索框：支持按名称/描述/应用名/数据模型搜索
- [ ] 卡片 hover 效果：轻微上浮 + 阴影加深
- [ ] 卡片点击展开详情（接口列表 + 数据范围说明）
- [ ] 5 步向导完整可走通
- [ ] 申请主体选择后，后续步骤正确关联
- [ ] 数据范围表单根据 scope_definitions 动态渲染
- [ ] 条件表达式实时展示（Casbin/OpenFGA）
- [ ] 确认页面展示完整预览（主体/能力/组合/范围/表达式/审批链）
- [ ] 提交后进入审批流模拟
- [ ] 明亮现代风格（白色背景 + 蓝色主色 + 圆角卡片 + 柔和阴影）
- [ ] 响应式布局（桌面 3 列 / 平板 2 列 / 手机 1 列）

### 6.3 e2e 验收

- [ ] `demo.sh` 全链路通过
- [ ] 为自己申请 → 低风险 → 1 人审批
- [ ] 为自建组申请 → 组长确认
- [ ] 为下游应用申请 → 自动中风险 → 2 人审批
- [ ] 完整管理 + 所有数据 → 高风险 → 3 人审批

---

## 7. 风险与注意事项

| 风险 | 应对 |
|------|------|
| JSONB 字段迁移 | GORM AutoMigrate 自动处理，无需手写 SQL |
| 前端向导复杂度 | 拆分为独立组件，逐步集成 |
| 条件表达式准确性 | 先用模板生成，后续可接入真实 Casbin/OpenFGA 查询 |
| scope-options API 安全 | 需校验用户对目标应用的访问权限 |
| 种子数据量 | 先 cmdb + CloudPortal 两个应用，覆盖主要场景 |
