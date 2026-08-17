# 下一轮开发计划（两阶段）

> **日期**：2026-08-06
> **更新**：2026-08-07（Phase 2 改为交互式演示播放器）
> **详细计划**：
> - 功能完善：见本文档 §二
> - 演示开发：见 `plans/demo-dev-plan.md`

---

## 一、阶段概览

| 阶段 | 目标 | 周期 | 产出 |
|------|------|------|------|
| **Phase 1：功能完善** | 系统基本可用，无阻塞性 bug | 2-3 天 | 稳定可用的系统 | ✅ |
| **Phase 2：演示开发** | 交互式 PPT 风格演示播放器 | 2 天 | 前端演示模块 + 两套场景 | ⬜ |

---

## 二、Phase 1：功能完善（Day 1-3）

### 2.1 目标

| 目标 | 说明 |
|------|------|
| **修复阻塞性 bug** | 确保核心流程可走通 |
| **完善缺失功能** | 补齐关键功能缺口 |
| **数据一致性** | 确保 Seed 数据正确 |
| **UI 一致性** | 统一页面风格 |

### 2.2 任务清单

#### Day 1：核心功能修复

| 优先级 | 任务 | 说明 | 状态 |
|--------|------|------|------|
| P0 | 预设级 status 字段 | Preset 结构加 status（published/draft） | ✅ |
| P0 | 预设上架/下架 API | publishPreset / offlinePreset 接口 | ✅ |
| P0 | 能力包创建后跳转 | 创建能力后自动跳转编辑页 | ✅ |
| P0 | 侧边栏菜单高亮 | 能力编辑页正确高亮"能力管理" | ✅ |
| P1 | 数据模型多选 | 从 API 获取所有资源模型 | ✅ |
| P1 | 可申请范围选择器 | 组织/人员/自建组独立行 | ✅ |

#### Day 2：双主体 + 审批完善

| 优先级 | 任务 | 说明 | 状态 |
|--------|------|------|------|
| P0 | AccessRequest 扩展 | 增加 grantee_type/grantee_name/applicant_id | ✅ |
| P0 | 申请向导双主体 | 第 2 步支持人 + 程序选择 | ✅ |
| P0 | 审批中心优化 | 显示申请人和授权主体 | ✅ |
| P1 | 审批通过自动授权 | 审批通过后自动创建策略 + OpenFGA 关系 | ✅ |

#### Day 3：UI 一致性 + 数据修复

| 优先级 | 任务 | 说明 | 状态 |
|--------|------|------|------|
| P1 | 能力编辑器样式 | 参考 v12 demo 统一按钮/卡片样式 | ✅ |
| P1 | 授权管理页完善 | 预设列表 + 状态管理 + 统计 | ✅ |
| P1 | Seed 数据优化 | 小黄/小红用户 + 演示应用 | ✅ |
| P2 | 其他页面 UI 统一 | 参考 v12 demo 优化剩余页面 | ⬜ |

### 2.3 验收标准

- [x] 能力包预设可独立上架/下架
- [x] 申请单支持双主体（人 + 程序）
- [x] 审批通过后权限立即生效
- [x] Seed 数据正确（小黄/小红用户可登录）
- [x] 核心流程无阻塞性 bug

### 2.4 测试验证

```bash
# 1. 重新部署
make up

# 2. Seed 数据
make seed

# 3. 核心流程验证
# - 小黄登录 → 应用管理 → 能力编辑 → 预设上架
# - 小红登录 → 能力市场 → 申请 → 审批 → 权限验证

# 4. 权限验证
bash scripts/verify-permissions.sh
```

---

## 三、Phase 2：交互式演示播放器（Day 4-5）

### 3.1 设计理念

> **核心需求**：面试演示时，不需要现场操作真实系统，而是像 PPT 一样逐步播放预录制的流程。
> 如果面试官要求现场操作，随时切回正常模块实操。

**两种运行模式**：
- **离线模式**（默认）：所有数据内置 mock，无需后端运行，0 依赖演示
- **在线模式**：可选连接 `localhost:8080`，调用真实 API 获取实时数据

### 3.2 目标

| 目标 | 说明 |
|------|------|
| **PPT 式交互** | 步骤切换有滑动/淡入动画，底部进度条，键盘 ←→ 翻页 |
| **场景 1** | 小黄（应用 Owner）：登录 → 能力编辑 → 预设上架 → 审批（8 步） |
| **场景 2** | 小红（权限申请者）：登录 → 能力市场 → 申请 → 审批 → 验证（8 步） |
| **独立菜单** | 侧栏新增「🎬 演示模式」入口，路由 `/demo` |
| **沉浸体验** | 全屏/大卡片模式，模拟系统 UI 截面，角色标识实时切换 |

### 3.3 交互设计

```
┌──────────────────────────────────────────────────────┐
│  侧栏  │  🎬 演示模式（/demo）                         │
│        │                                              │
│        │  ┌──────────────────────────────────────────┐│
│        │  │  👤 小黄 · 应用 Owner    步骤 3/8         ││
│        │  ├──────────────────────────────────────────┤│
│        │  │                                          ││
│        │  │    📱 模拟屏幕（简化 UI 组件）              ││
│        │  │    当前：能力编辑器 → 主机监控               ││
│        │  │                                          ││
│        │  │    动画过渡：slide-left / fade             ││
│        │  │                                          ││
│        │  ├──────────────────────────────────────────┤│
│        │  │  📝 "小黄作为应用 Owner，进入能力编辑器，  ││
│        │  │     打包「主机监控」能力，绑定只读接口..."   ││
│        │  ├──────────────────────────────────────────┤│
│        │  │  ████████░░░░░░  3/8                     ││
│        │  │  [← 上一步]    [▶ 下一步 · 空格]   [⟳]   ││
│        │  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

### 3.4 场景步骤编排

#### 场景 1：小黄（应用 Owner）— 8 步

| 步 | 画面组件 | 角色 | 解说文字 | 动画 |
|----|----------|------|---------|------|
| 1 | `LoginScreen` | — | "应用 Owner 小黄登录系统" | fade |
| 2 | `WorkbenchScreen` | 小黄 | "进入工作台，选择「小黄的监控服务」应用" | slide-left |
| 3 | `CapEditorScreen` | 小黄 | "打包能力「主机监控」，绑定 host:list / host:read 接口" | slide-left |
| 4 | `PresetConfigScreen` | 小黄 | "配置预设「只读监控」，限定用户/组织可申请" | slide-left |
| 5 | `AuthzMgmtScreen` | 小黄 | "进入授权管理，点击「上架」按钮" | slide-left |
| 6 | `ApprovalFlowScreen` | 系统 | "走审批流程 → Owner 确认 → 平台复核 → 审批通过" | pop-in |
| 7 | `StatusConfirmScreen` | 小黄 | "预设状态已变为 published，能力市场已可见" | slide-left |
| 8 | `CompleteScreen` | — | "✅ 小黄的发布流程完成：声明 → 配置 → 上架 → 审批" | celebrate |

#### 场景 2：小红（权限申请者）— 8 步

| 步 | 画面组件 | 角色 | 解说文字 | 动画 |
|----|----------|------|---------|------|
| 1 | `LoginScreen` | — | "普通用户小红登录系统" | fade |
| 2 | `MarketplaceScreen` | 小红 | "进入能力市场，发现「小黄的监控服务 - 主机监控」" | slide-left |
| 3 | `PresetSelectScreen` | 小红 | "选择「只读监控」预设，查看包含的接口" | slide-left |
| 4 | `SubjectSelectScreen` | 小红 | "选择授权主体：小红自己（人）+ 小红的数据分析（程序）" | slide-left |
| 5 | `SubmitConfirmScreen` | 小红 | "填写理由「需要读取生产环境主机」，提交申请" | slide-left |
| 6 | `SwitchUserScreen` | 小黄 | "切换到小黄视角，审批中心看到待审批工单" | slide-left |
| 7 | `ApprovalScreen` | 小黄 | "审批通过 → 策略立即生效 → 授权完成" | pop-in |
| 8 | `VerifyScreen` | — | "✅ 权限验证：GET 主机 200 ✅ / POST 主机 403 🚫" | celebrate |

### 3.5 文件结构

```
frontend/src/
├── router/index.ts              ← 新增路由 /demo
├── views/Layout.vue             ← 侧栏新增「🎬 演示模式」菜单项
├── views/
│   └── DemoPlay.vue             ← 主页面：播放器 + 场景选择 + 控制栏
├── components/
│   └── demo/
│       ├── PlayerControls.vue   ← 底部控制栏（上一步/下一步/进度/重播）
│       ├── ScenarioHeader.vue   ← 顶部角色标识 + 场景标题
│       └── screens/             ← 每步的模拟屏幕（精简 UI 组件）
│           ├── LoginScreen.vue          ← 登录页（复用于两个场景）
│           ├── WorkbenchScreen.vue      ← 工作台概览
│           ├── CapEditorScreen.vue      ← 能力编辑器（接口绑定）
│           ├── PresetConfigScreen.vue   ← 预设配置（主体类型）
│           ├── AuthzMgmtScreen.vue      ← 授权管理（上架/下架）
│           ├── ApprovalFlowScreen.vue   ← 审批流程动画
│           ├── StatusConfirmScreen.vue  ← 状态确认
│           ├── CompleteScreen.vue       ← 完成页（撒花动画）
│           ├── MarketplaceScreen.vue    ← 能力市场（卡片列表）
│           ├── PresetSelectScreen.vue   ← 预设选择
│           ├── SubjectSelectScreen.vue  ← 双主体选择
│           ├── SubmitConfirmScreen.vue  ← 申请确认
│           ├── SwitchUserScreen.vue     ← 角色切换过渡
│           ├── ApprovalScreen.vue       ← 审批操作
│           └── VerifyScreen.vue         ← 权限验证（curl 结果展示）
```

### 3.6 交互细节

| 特性 | 实现 |
|------|------|
| **键盘控制** | `→` / `Space` 下一步，`←` 上一步，`R` 重播，`F` 全屏 |
| **自动播放** | 可选「自动播放」按钮，每步停 4 秒 |
| **过渡动画** | `slide-left`（前进）、`slide-right`（后退）、`pop-in`（弹窗）、`fade`（首尾步） |
| **完成动画** | 最后一步显示 ✅ + 粒子/光效（纯 CSS） |
| **角色标识** | 顶部显示当前操作人（头像 + 姓名 + 角色标签），角色切换时有过渡动画 |
| **模拟屏幕** | 每个 Screen 组件 ~30-50 行，简化模拟真实 UI，重点突出 |
| **数据源** | 默认内置 mock JSON；可选 `fetch()` 调用真实 API |
| **响应式** | 适配 1024px+ 屏幕（面试投屏场景） |

### 3.7 技术方案

| 项 | 方案 |
|----|------|
| **框架** | Vue 3 `<script setup>` + Composition API |
| **样式** | 复用现有 CSS 变量（`--brand`, `--bg-card` 等），新增演示专用变量 |
| **状态** | `ref()` 管理当前场景、当前步骤、播放状态 |
| **动画** | CSS `transition` + `@keyframes`，无外部动画库 |
| **数据** | 两个场景各一个 `steps[]` 数组，每步含 `{ component, role, narration, animation }` |
| **键盘** | `useEventListener` 监听 `keydown` |

---

## 四、时间线总览

```
Day 1-3: Phase 1（功能完善）✅
├── Day 1: 核心功能修复
├── Day 2: 双主体 + 审批完善
└── Day 3: UI 一致性 + 数据修复

Day 4-5: Phase 2（演示播放器）
├── Day 4: 播放器框架 + 场景 1（小黄 8 步）
└── Day 5: 场景 2（小红 8 步）+ 动画打磨 + 全流程验证
```

---

## 五、验收清单

### Phase 1 验收 ✅

- [x] 预设可独立上架/下架
- [x] 申请单支持双主体
- [x] 审批通过后权限生效
- [x] Seed 数据正确
- [x] 核心流程无阻塞性 bug

### Phase 2 验收

- [ ] 侧栏有「🎬 演示模式」入口，点击进入 `/demo`
- [ ] 场景选择：顶部 tab 切换小黄/小红
- [ ] 小黄场景 8 步可完整播放，每步有动画过渡
- [ ] 小红场景 8 步可完整播放，每步有动画过渡
- [ ] 键盘 ←→ 翻页流畅
- [ ] 进度条实时更新
- [ ] 角色标识随步骤切换
- [ ] 完成页有庆祝动画
- [ ] 离线模式（无后端）可正常演示

---

*计划更新于 2026-08-06*

---

## 二、开发任务分解

### Phase 1：预设级生命周期（Day 1）

#### 1.1 后端：Preset 模型扩展

**文件**：`backend/internal/model/capability.go`

```go
// Preset 结构扩展
type CapabilityPreset struct {
    ID            string   `json:"id"`
    Name          string   `json:"name"`
    Desc          string   `json:"desc"`
    Status        string   `json:"status"`        // 🆕 published | draft
    ActionCodes   []string `json:"action_codes"`
    GranteeTypes  []string `json:"grantee_types"`
    ApplyScope    any      `json:"apply_scope"`
    DataControl   bool     `json:"data_control"`
    DataModels    []string `json:"data_models"`
    // 🆕 新增字段
    PublishedAt   *time.Time `json:"published_at"`
    PublishedBy   *uint64    `json:"published_by"`
}
```

#### 1.2 后端：预设上架/下架 API

**文件**：`backend/internal/api/handler_capability.go`

```go
// 预设上架（走审批）
func (d *Deps) publishPreset(c *gin.Context) {
    cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
    pid := c.Param("pid")
    // 1. 校验权限（能力包 owner）
    // 2. 更新 preset status = "published"
    // 3. 记录审计日志
    // 4. 返回成功
}

// 预设下架（走审批）
func (d *Deps) offlinePreset(c *gin.Context) {
    cid, _ := strconv.ParseUint(c.Param("cid"), 10, 64)
    pid := c.Param("pid")
    // 1. 校验权限
    // 2. 更新 preset status = "draft"
    // 3. 记录审计日志
    // 4. 返回成功
}
```

#### 1.3 后端：路由注册

**文件**：`backend/internal/api/router.go`

```go
// 预设级操作
mg.POST("/apps/:id/capabilities/:cid/presets/:pid/publish", d.publishPreset)
mg.POST("/apps/:id/capabilities/:cid/presets/:pid/offline", d.offlinePreset)
```

#### 1.4 前端：授权管理页完善

**文件**：`frontend/src/views/CapabilityAuthz.vue`

- 预设列表显示 status 标签（已上架/草稿）
- 每个预设操作按钮（上架/下架）
- 授权概况四维统计（用户/组织/组/程序）

#### 1.5 验收标准

- [ ] 预设可独立上架/下架
- [ ] 市场只显示已上架预设
- [ ] 审计日志记录上架/下架操作

---

### Phase 2：双主体模型（Day 1-2）

#### 2.1 后端：AccessRequest 模型扩展

**文件**：`backend/internal/model/governance.go`

```go
type AccessRequest struct {
    // ... 现有字段
    // 🆕 双主体字段
    GranteeType   string `json:"grantee_type"`   // user | org | group | app
    GranteeName   string `json:"grantee_name"`   // 如 "client:cloud-mgmt"
    ApplicantID   uint64 `json:"applicant_id"`   // 申请人（人）
}
```

#### 2.2 后端：submitRequest 扩展

**文件**：`backend/internal/api/handler_governance.go`

```go
func (d *Deps) submitRequest(c *gin.Context) {
    // ... 现有逻辑
    // 增加双主体解析
    req.GranteeType = body.GranteeType  // 如 "app"
    req.GranteeName = body.GranteeName  // 如 "client:cloud-mgmt"
    req.ApplicantID = d.currentUserID(c) // 申请人
}
```

#### 2.3 前端：申请向导扩展

**文件**：`frontend/src/views/Marketplace.vue`

- 第 2 步"选择主体"增加双主体选择
- 显示"申请人"和"授权主体"两个字段
- 程序主体提示"由 owner 人代理申请"

#### 2.4 验收标准

- [ ] 申请单包含 grantee_type/grantee_name/applicant_id
- [ ] 审批单显示申请人和授权主体
- [ ] 程序主体申请流程可走通

---

### Phase 3：表达式构建器（Day 2-3）

#### 3.1 前端：ExpressionBuilder 组件

**文件**：`frontend/src/components/ExpressionBuilder.vue`

```vue
<template>
  <div class="expr-builder">
    <div class="expr-row">
      <select v-model="field" class="input">
        <option v-for="f in fields" :key="f.name" :value="f.name">{{ f.name }}</option>
      </select>
      <select v-model="op" class="input">
        <option v-for="o in operators" :key="o" :value="o">{{ o }}</option>
      </select>
      <input v-model="value" class="input" placeholder="值" />
      <button @click="addCondition">+</button>
    </div>
    <div class="expr-preview">
      <code>{{ expression }}</code>
    </div>
  </div>
</template>
```

#### 3.2 后端：表达式校验 API

**文件**：`backend/internal/api/handler_capability.go`

```go
func (d *Deps) validateExpression(c *gin.Context) {
    var req struct {
        Expression string `json:"expression"`
        Model      string `json:"model"`
    }
    // 1. 语法校验（轻量正则或 cel.Parse）
    // 2. 字段校验（检查字段是否存在）
    // 3. 返回校验结果
}
```

#### 3.3 验收标准

- [ ] 表达式构建器可交互生成 CEL 表达式
- [ ] 表达式可提交后端校验
- [ ] 申请单可携带 expression 类型的数据范围

---

### Phase 4：测试流程建立（Day 3-4）

#### 4.1 单元测试

**目录**：`backend/internal/**/*_test.go`

| 模块 | 测试文件 | 覆盖内容 |
|------|----------|----------|
| model | `capability_test.go` | Preset 状态转换、ApplyScope 校验 |
| api | `handler_capability_test.go` | CRUD、上架/下架、权限校验 |
| api | `handler_governance_test.go` | 申请、审批、双主体 |
| authz | `casbin_test.go` | 策略匹配、缓存失效 |
| openfga | `fga_test.go` | Check、ListObjects、条件表达式 |

#### 4.2 集成测试

**目录**：`scripts/test-integration.sh`

```bash
#!/bin/bash
# 集成测试脚本

echo "=== 1. 启动服务 ==="
docker compose -f deploy/docker-compose.yml up -d

echo "=== 2. Seed 数据 ==="
docker compose exec iam-server iam-server seed

echo "=== 3. 基础 CRUD 测试 ==="
# 测试用户/组/应用/权限点 CRUD

echo "=== 4. 策略测试 ==="
# 测试策略创建/发布/缓存

echo "=== 5. 网关鉴权测试 ==="
# 测试 PEP → PDP 全链路

echo "=== 6. 能力包测试 ==="
# 测试能力包 CRUD + 预设上架/下架

echo "=== 7. 申请审批测试 ==="
# 测试申请 → 审批 → 开通

echo "=== 8. 数据权限测试 ==="
# 测试 OpenFGA Check/ListObjects

echo "=== 集成测试完成 ==="
```

#### 4.3 E2E 测试

**目录**：`scripts/test-e2e.sh`

```bash
#!/bin/bash
# E2E 测试脚本（基于 demo.sh 扩展）

echo "=== E2E 测试：能力包全生命周期 ==="

# 场景 1：能力包创建 → 配置 → 上架 → 申请 → 审批 → 授权
# 场景 2：双主体申请（人代理程序）
# 场景 3：数据范围表达式
# 场景 4：预设下架 → 市场不可见

echo "=== E2E 测试完成 ==="
```

#### 4.4 验收标准

- [ ] 单元测试覆盖率 > 60%
- [ ] 集成测试脚本可一键运行
- [ ] E2E 测试覆盖核心业务流程

---

### Phase 5：Seed 数据优化（Day 4）

#### 5.1 新增 Seed 数据

**文件**：`backend/cmd/iam-server/seed.go`

```go
// 新增能力包
seedCapability(appID, "数据库管理", "数据库查看与变更能力", []string{"db:list", "db:read", "db:backup"})
seedCapability(appID, "工单管理", "工单创建与处理能力", []string{"ticket:list", "ticket:create", "ticket:update"})

// 新增预设（含 status）
seedPreset(capID, "只读查看", "published", []string{"db:list", "db:read"})
seedPreset(capID, "DBA 管理", "draft", []string{"db:list", "db:read", "db:backup"})

// 新增双主体申请
seedRequest(userID, "app", "client:cloud-mgmt", "db:read", "需要读取数据库用于监控")
```

#### 5.2 验收标准

- [ ] Seed 数据覆盖所有新增功能
- [ ] Seed 脚本幂等可重复执行
- [ ] demo.sh 包含新增场景

---

### Phase 6：Demo 场景完善（Day 5）

#### 6.1 更新 demo.sh

**文件**：`scripts/demo.sh`

```bash
#!/bin/bash
# Demo 完整流程

echo "=== Demo 场景 1：能力包全生命周期 ==="
# 1. 创建能力包
# 2. 配置预设
# 3. 上架预设
# 4. 市场申请
# 5. 审批通过
# 6. 验证授权
# 7. 下架预设
# 8. 验证市场不可见

echo "=== Demo 场景 2：双主体申请 ==="
# 1. 人代理程序申请
# 2. 审批链路
# 3. 授权生效

echo "=== Demo 场景 3：数据权限表达式 ==="
# 1. 构建表达式
# 2. 申请带表达式的数据范围
# 3. 验证 OpenFGA 条件
```

#### 6.2 验收标准

- [ ] demo.sh 全链路通过
- [ ] 所有场景可独立演示
- [ ] 演示脚本有清晰的输出提示

---

## 三、测试流程设计

### 3.1 测试金字塔

```
          ┌─────────┐
          │  E2E    │  ← 核心业务流程（demo.sh）
          │  测试   │
          ├─────────┤
          │ 集成测试 │  ← API 接口 + 数据库
          │         │
          ├─────────┤
          │ 单元测试 │  ← 函数/方法级别
          │         │
          └─────────┘
```

### 3.2 测试执行流程

```bash
# 1. 单元测试
cd backend && go test ./... -v

# 2. 集成测试
bash scripts/test-integration.sh

# 3. E2E 测试
bash scripts/demo.sh

# 4. 前端测试（如有）
cd frontend && npm run test
```

### 3.3 测试数据管理

| 数据类型 | 管理方式 | 说明 |
|----------|----------|------|
| 用户/组 | Seed 脚本 | `iam-server seed` 幂等执行 |
| 应用/权限点 | Seed 脚本 | 从 OpenAPI 同步 |
| 能力包 | Seed 脚本 | 新增场景数据 |
| 策略 | Seed 脚本 | 授权数据 |
| 申请单 | 测试脚本 | E2E 测试时动态创建 |

---

## 四、数据填充方案

### 4.1 Seed 数据结构

```
用户（12人）
├── admin（管理员）
├── alice/bob/carol/dave（研发一部）
├── erin/frank（运维中心）
├── grace（安全合规）
└── hank/ivy/jack/kate/leo（其他部门）

组织树（9节点）
├── 总公司
│   ├── 研发中心
│   │   ├── 研发一部（alice 组长）
│   │   └── 研发二部（carol 组长）
│   ├── 运维中心
│   │   ├── 平台运维部（erin 组长）
│   │   └── 应用运维部（frank 组长）
│   └── 职能中心
│       └── 安全合规部（grace 组长）

应用（5个）
├── CMDB（alice + bob 负责）
├── 监控告警（erin + frank 负责）
├── ITSM 工单（carol + dave 负责）
├── 公共资源池（多人负责）
└── 运维工具平台（多人负责）

能力包（新增）
├── CMDB - 主机管理（已有）
├── CMDB - disk 管理（已有）
├── CMDB - 网络管理（新增）
├── CMDB - 数据库管理（新增）
└── ITSM - 工单管理（新增）

策略（丰富）
├── 接口权限（已有）
├── 数据权限（已有）
├── 组权限（已有）
└── 能力包权限（新增）
```

### 4.2 Seed 执行顺序

```bash
# 1. 清理旧数据（可选）
docker compose exec iam-server iam-server seed --clean

# 2. 执行 Seed
docker compose exec iam-server iam-server seed

# 3. 验证数据
bash scripts/demo.sh
```

---

## 五、端到端测试设计

### 5.1 测试场景矩阵

| 场景 | 前置条件 | 操作步骤 | 预期结果 |
|------|----------|----------|----------|
| **S1: 能力包上架** | 能力包已创建，预设为 draft | 1. 登录 alice<br>2. 进入能力编辑<br>3. 点击预设"上架" | 预设 status 变为 published |
| **S2: 市场申请** | 预设已上架 | 1. 登录 bob<br>2. 进入能力市场<br>3. 选择预设<br>4. 提交申请 | 申请单创建成功 |
| **S3: 审批通过** | 申请单已创建 | 1. 登录 alice<br>2. 进入审批中心<br>3. 审批通过 | 策略生效，授权成功 |
| **S4: 双主体申请** | 能力包支持程序主体 | 1. 登录 alice<br>2. 代理 cloud-mgmt 申请<br>3. 提交申请 | 申请单包含 grantee_type=app |
| **S5: 表达式申请** | 能力包支持表达式 | 1. 登录 bob<br>2. 构建表达式<br>3. 提交申请 | 申请单包含 expression |
| **S6: 预设下架** | 预设已上架 | 1. 登录 alice<br>2. 下架预设 | 预设 status 变为 draft |
| **S7: 市场不可见** | 预设已下架 | 1. 登录 bob<br>2. 查看能力市场 | 下架预设不可见 |

### 5.2 测试脚本示例

```bash
#!/bin/bash
# test-e2e.sh

BASE_URL="https://api.permission-center.orb.local"
TOKEN=$(curl -s -X POST "$BASE_URL/v1/auth/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice"}' | jq -r '.token')

echo "=== S1: 能力包上架 ==="
curl -X POST "$BASE_URL/v1/apps/1/capabilities/15/presets/p1/publish" \
  -H "Authorization: Bearer $TOKEN"
# 验证 status 变为 published

echo "=== S2: 市场申请 ==="
BOB_TOKEN=$(curl -s -X POST "$BASE_URL/v1/auth/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob"}' | jq -r '.token')

curl -X POST "$BASE_URL/v1/requests" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_id": 15,
    "preset_id": "p1",
    "grantee_type": "user",
    "reason": "需要读取网络信息"
  }'
# 验证申请单创建成功

echo "=== E2E 测试完成 ==="
```

---

## 六、Demo 任务计划

### Demo 1：能力包全生命周期（15 分钟）

**场景**：CMDB 应用的"数据库管理"能力包从创建到授权的完整流程

**演示步骤**：

| 步骤 | 操作 | 页面 | 说明 |
|------|------|------|------|
| 1 | 登录 alice | 登录页 | 应用 owner |
| 2 | 进入应用管理 | 应用管理 | 选择 CMDB 应用 |
| 3 | 创建能力包 | 能力编辑器 | 名称"数据库管理"，描述"数据库查看与变更能力" |
| 4 | 配置预设 | 能力编辑器 | 绑定 db:list/db:read/db:backup 接口 |
| 5 | 设置可申请范围 | 能力编辑器 | 仅研发一部可申请 |
| 6 | 上架预设 | 授权管理 | 预设 status → published |
| 7 | 登录 bob | 登录页 | 普通用户 |
| 8 | 进入能力市场 | 能力市场 | 看到"数据库管理"能力 |
| 9 | 选择预设申请 | 申请向导 | 选择"只读查看"预设 |
| 10 | 提交申请 | 申请确认 | 填写理由 |
| 11 | 登录 alice | 登录页 | 审批人 |
| 12 | 审批通过 | 审批中心 | 点击"通过" |
| 13 | 验证授权 | 我的权限 | bob 看到新授权 |
| 14 | 验证网关 | 终端 | bob 可访问 db:list API |

**演示亮点**：
- 能力包声明 → 配置 → 上架 → 申请 → 审批 → 授权完整闭环
- 预设级生命周期管理
- 可申请范围控制
- 审批链路 + SoD

---

### Demo 2：双主体 + 数据权限表达式（10 分钟）

**场景**：应用 owner 代理程序申请带数据范围的权限

**演示步骤**：

| 步骤 | 操作 | 页面 | 说明 |
|------|------|------|------|
| 1 | 登录 alice | 登录页 | cloud-mgmt 应用 owner |
| 2 | 进入能力市场 | 能力市场 | 选择 CMDB - 主机管理 |
| 3 | 选择程序主体 | 申请向导 | 主体类型选"程序"，选择 cloud-mgmt |
| 4 | 构建数据表达式 | 申请向导 | 使用表达式构建器：`env == "prod"` |
| 5 | 提交申请 | 申请确认 | 理由"监控需要读取生产环境主机" |
| 6 | 审批通过 | 审批中心 | admin 审批 |
| 7 | 验证 OpenFGA | 系统观测 → PIP | 查看 cloud-mgmt 的授权关系 |
| 8 | 验证数据权限 | 终端 | cloud-mgmt 只能访问 prod 主机 |

**演示亮点**：
- 双主体模型（人代理程序申请）
- 表达式构建器交互
- OpenFGA 条件表达式
- 数据权限精确控制

---

## 七、时间线

| 日期 | 任务 | 产出 |
|------|------|------|
| **Day 1** | Phase 1 + Phase 2 | 预设生命周期 + 双主体模型 |
| **Day 2** | Phase 2 + Phase 3 | 双主体前端 + 表达式构建器 |
| **Day 3** | Phase 3 + Phase 4 | 表达式校验 + 测试框架 |
| **Day 4** | Phase 4 + Phase 5 | 测试脚本 + Seed 数据 |
| **Day 5** | Phase 6 + Demo | Demo 场景 + 演示准备 |

---

## 八、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 预设生命周期复杂度高 | 延期 | 简化为 status 字段 + 审批开关，不做复杂状态机 |
| 表达式构建器 UI 复杂 | 延期 | 先实现基础版本，后续迭代优化 |
| 测试覆盖率不足 | 质量 | 优先覆盖核心业务流程，非核心模块手动验证 |
| Seed 数据不一致 | 演示失败 | Seed 脚本幂等 + 演示前手动验证 |

---

## 九、验收清单

### 功能验收

- [ ] 预设可独立上架/下架
- [ ] 市场只显示已上架预设
- [ ] 申请单支持双主体
- [ ] 表达式构建器可交互生成
- [ ] 表达式可提交后端校验
- [ ] 数据权限表达式生效

### 测试验收

- [ ] 单元测试覆盖率 > 60%
- [ ] 集成测试脚本可一键运行
- [ ] E2E 测试覆盖核心流程
- [ ] demo.sh 全链路通过

### Demo 验收

- [ ] Demo 1：能力包全生命周期可演示
- [ ] Demo 2：双主体 + 表达式可演示
- [ ] 演示脚本有清晰输出

---

*计划制定于 2026-08-06*
