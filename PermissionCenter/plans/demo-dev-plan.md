# 演示场景开发计划（Phase 2）

> **日期**：2026-08-06
> **更新**：2026-08-07（改为交互式 PPT 风格演示播放器）
> **定位**：整体计划的第二阶段，在前端内构建沉浸式演示模块
> **前置条件**：Phase 1（功能完善）已完成
> **整体计划**：见 `plans/next-round-dev-plan.md`

---

## 一、设计理念

### 为什么不做 shell 脚本演示？

| 问题 | 说明 |
|------|------|
| **体验差** | 终端 curl 输出一堆 JSON，面试官看不懂 |
| **风险高** | 现场操作容易紧张出错，环境问题不可控 |
| **不沉浸** | 没有视觉引导，无法讲清楚业务流程 |

### 解决方案：前端内置 PPT 播放器

- 像 Windows 初始化向导一样，点「下一步」逐步展示
- 每步渲染一个简化的模拟 UI 截面，带入场/退场动画
- 所有数据内置 mock，**不依赖后端运行**
- 面试官要求实操时，随时切回正常模块

---

## 二、场景详细设计

### 场景 1：小黄（应用 Owner）— 8 步

| 步 | 模拟画面 | 解说 | 动画 |
|----|----------|------|------|
| 1 | 登录页：下拉选「小黄」→ 点击登录 | "应用 Owner 小黄登录权限中心" | fade |
| 2 | 工作台：显示「小黄的监控服务」应用卡片 | "进入工作台，选择自己负责的应用" | slide-left |
| 3 | 能力编辑器：绑定 host:list ✅ host:read ✅ | "打包能力「主机监控」，绑定只读接口" | slide-left |
| 4 | 预设配置：用户/组织可申请，数据级控制 | "配置预设「只读监控」，设定可申请范围" | slide-left |
| 5 | 授权管理：点击「🚀 上架」按钮 | "将预设上架到能力市场" | slide-left |
| 6 | 审批流程：Owner确认 → 平台复核 → 通过 | "走审批流程（自动模拟，带步骤动画）" | pop-in |
| 7 | 状态确认：published ✅ 标签 | "预设已上架，能力市场已可见" | slide-left |
| 8 | 完成页：✅ + 核心架构图 | "完整闭环：声明 → 配置 → 上架 → 审批" | celebrate |

### 场景 2：小红（权限申请者）— 8 步

| 步 | 模拟画面 | 解说 | 动画 |
|----|----------|------|------|
| 1 | 登录页：下拉选「小红」→ 点击登录 | "普通用户小红登录系统" | fade |
| 2 | 能力市场：卡片列表，高亮「主机监控」 | "进入能力市场，发现小黄发布的主机监控能力" | slide-left |
| 3 | 预设选择：选中「只读监控」 | "选择只读监控预设，查看包含的接口权限" | slide-left |
| 4 | 主体选择：👤 小红（人）+ 🔌 小红的数据分析（程序） | "选择双主体：人 + 程序身份" | slide-left |
| 5 | 申请确认：填写理由 → 提交 | "提交申请，系统生成申请单 #N" | slide-left |
| 6 | 角色切换：过渡动画 → 小黄的审批中心 | "切换到小黄视角，看到待审批工单" | slide-left |
| 7 | 审批操作：点击「✅ 通过」→ 策略生效 | "审批通过，策略立即生效" | pop-in |
| 8 | 权限验证：GET 200 ✅ POST 403 🚫 | "验证权限：读取允许，写入拒绝" | celebrate |

---

## 三、技术实现

### 3.1 文件清单

```
frontend/src/
├── router/index.ts                    ← 新增 /demo 路由
├── views/Layout.vue                   ← 侧栏新增菜单项
├── views/DemoPlay.vue                 ← 主页面（播放器）
├── components/demo/
│   ├── PlayerControls.vue             ← 底部控制栏
│   ├── ScenarioHeader.vue             ← 顶部角色标识
│   └── screens/                       ← 16 个模拟屏幕组件
│       ├── LoginScreen.vue
│       ├── WorkbenchScreen.vue
│       ├── CapEditorScreen.vue
│       ├── PresetConfigScreen.vue
│       ├── AuthzMgmtScreen.vue
│       ├── ApprovalFlowScreen.vue
│       ├── StatusConfirmScreen.vue
│       ├── CompleteScreen.vue
│       ├── MarketplaceScreen.vue
│       ├── PresetSelectScreen.vue
│       ├── SubjectSelectScreen.vue
│       ├── SubmitConfirmScreen.vue
│       ├── SwitchUserScreen.vue
│       ├── ApprovalScreen.vue
│       └── VerifyScreen.vue
```

### 3.2 DemoPlay.vue 核心逻辑

```ts
// 场景数据（预定义步骤序列）
const scenarios = {
  xiaohuang: {
    title: '小黄：应用管理流程',
    role: '应用 Owner',
    steps: [
      { component: 'LoginScreen',      role: '—',    narration: '应用 Owner 小黄登录系统',       animation: 'fade' },
      { component: 'WorkbenchScreen',  role: '小黄', narration: '进入工作台，选择「小黄的监控服务」', animation: 'slide-left' },
      { component: 'CapEditorScreen',  role: '小黄', narration: '打包能力「主机监控」，绑定只读接口', animation: 'slide-left' },
      { component: 'PresetConfigScreen', role: '小黄', narration: '配置预设「只读监控」，设定可申请范围', animation: 'slide-left' },
      { component: 'AuthzMgmtScreen',  role: '小黄', narration: '进入授权管理，点击上架',          animation: 'slide-left' },
      { component: 'ApprovalFlowScreen', role: '系统', narration: '走审批流程 → 审批通过',        animation: 'pop-in' },
      { component: 'StatusConfirmScreen', role: '小黄', narration: '预设状态已变为 published',      animation: 'slide-left' },
      { component: 'CompleteScreen',   role: '—',    narration: '✅ 完整闭环：声明→配置→上架→审批', animation: 'celebrate' },
    ],
  },
  xiaohong: {
    title: '小红：权限申请流程',
    role: '应用用户',
    steps: [
      { component: 'LoginScreen',      role: '—',    narration: '普通用户小红登录系统',             animation: 'fade' },
      { component: 'MarketplaceScreen', role: '小红', narration: '进入能力市场，发现主机监控能力',     animation: 'slide-left' },
      { component: 'PresetSelectScreen', role: '小红', narration: '选择「只读监控」预设',              animation: 'slide-left' },
      { component: 'SubjectSelectScreen', role: '小红', narration: '选择双主体：人 + 程序',            animation: 'slide-left' },
      { component: 'SubmitConfirmScreen', role: '小红', narration: '填写理由，提交申请',               animation: 'slide-left' },
      { component: 'SwitchUserScreen', role: '小黄', narration: '切换到小黄视角，审批中心',           animation: 'slide-left' },
      { component: 'ApprovalScreen',   role: '小黄', narration: '审批通过，策略立即生效',             animation: 'pop-in' },
      { component: 'VerifyScreen',     role: '—',    narration: '✅ 权限验证：GET 200 / POST 403',  animation: 'celebrate' },
    ],
  },
}

// 状态
const currentScenario = ref('xiaohuang')
const stepIndex = ref(0)
const isPlaying = ref(false)

// 控制
function next() { if (stepIndex.value < steps.length - 1) stepIndex.value++ }
function prev() { if (stepIndex.value > 0) stepIndex.value-- }
function reset() { stepIndex.value = 0 }
function toggleAutoPlay() { /* 每 4 秒自动 next() */ }

// 键盘
useEventListener(document, 'keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ') next()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'r' || e.key === 'R') reset()
})
```

### 3.3 模拟屏幕组件规范

每个 `*Screen.vue` 是一个精简的 UI 截面，~30-50 行：

```vue
<!-- CapEditorScreen.vue -->
<template>
  <div class="mock-screen">
    <div class="mock-breadcrumb">应用管理 / 小黄的监控服务 / 主机监控</div>
    <h3 class="mock-title">📦 主机监控 · 能力编辑器</h3>
    <div class="mock-card">
      <div class="mock-label">绑定接口</div>
      <div class="mock-checklist">
        <span class="check on">✅ host:list — 列举主机</span>
        <span class="check on">✅ host:read — 读取详情</span>
        <span class="check off">⬜ host:create — 创建主机</span>
      </div>
    </div>
    <div class="mock-card">
      <div class="mock-label">权限预设</div>
      <div class="mock-pills">
        <span class="pill active">🔖 只读监控</span>
        <span class="pill">🔖 完整监控</span>
      </div>
    </div>
  </div>
</template>
```

---

## 四、任务分解

### Day 4：播放器框架 + 场景 1

| 优先级 | 任务 | 文件 | 说明 |
|--------|------|------|------|
| P0 | 路由 + 侧栏入口 | `router/index.ts` + `Layout.vue` | 新增 `/demo` 路由 + 菜单项 |
| P0 | 播放器主框架 | `DemoPlay.vue` | 场景选择 + 步骤管理 + 键盘控制 |
| P0 | 控制栏 | `PlayerControls.vue` | 上一步/下一步/进度条/重播 |
| P0 | 角色标识 | `ScenarioHeader.vue` | 当前操作人 + 角色标签 |
| P0 | 场景 1 屏幕组件 | `screens/`（8 个） | 小黄 8 步的模拟 UI |
| P1 | 过渡动画 | CSS | slide-left / fade / pop-in / celebrate |
| P1 | 自动播放 | `DemoPlay.vue` | 可选 4 秒间隔自动步进 |

### Day 5：场景 2 + 打磨 + 验证

| 优先级 | 任务 | 文件 | 说明 |
|--------|------|------|------|
| P0 | 场景 2 屏幕组件 | `screens/`（新增 7 个） | 小红 8 步（复用 LoginScreen） |
| P0 | 全流程验证 | — | 两个场景完整播放无报错 |
| P1 | 动画打磨 | CSS | 节奏感、微调时长 |
| P1 | 响应式适配 | CSS | 适配投屏/宽屏场景 |

---

## 五、验收标准

- [ ] 侧栏有「🎬 演示模式」菜单项
- [ ] 点击进入 `/demo` 页面，可选择场景
- [ ] 小黄场景 8 步可完整播放
- [ ] 小红场景 8 步可完整播放
- [ ] 键盘 ←→ / 空格翻页流畅
- [ ] 进度条实时更新
- [ ] 角色标识随步骤切换（带过渡）
- [ ] 完成页有庆祝动画
- [ ] 离线模式（无后端）可正常演示
- [ ] npm run build 无报错

---

*计划更新于 2026-08-07*

---

### Phase 4：权限验证（Day 2-3）

#### 4.1 端点权限验证

**验证脚本**：`scripts/verify-permissions.sh`

```bash
#!/bin/bash
# 端点权限验证

echo "=== 验证小红的端点权限 ==="

# 获取小红的 token
TOKEN=$(curl -s -X POST "https://api.permission-center.orb.local/v1/auth/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"xiaohong"}' | jq -r '.token')

# 测试 GET /api/v1/hosts（应该 200）
echo "1. 测试 GET /api/v1/hosts"
curl -s -o /dev/null -w "%{http_code}" \
  -X GET "https://cmdb.permission-center.orb.local/api/v1/hosts" \
  -H "Authorization: Bearer $TOKEN"
echo " (预期: 200)"

# 测试 POST /api/v1/hosts（应该 403）
echo "2. 测试 POST /api/v1/hosts"
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://cmdb.permission-center.orb.local/api/v1/hosts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'
echo " (预期: 403)"
```

#### 4.2 数据权限验证

**验证脚本**：`scripts/verify-data-permissions.sh`

```bash
#!/bin/bash
# 数据权限验证

echo "=== 验证小红的数据权限 ==="

# 获取小红的 token
TOKEN=$(curl -s -X POST "https://api.permission-center.orb.local/v1/auth/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"xiaohong"}' | jq -r '.token')

# 测试 filter（应该只返回生产环境主机）
echo "1. 测试 filter /api/v1/hosts"
curl -s "https://cmdb.permission-center.orb.local/api/v1/hosts" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {name, env}'
echo " (应该只有 prod 环境)"

# 测试 check-instance（生产环境主机应该 allow）
echo "2. 测试 check-instance web-01"
curl -s -X POST "https://api.permission-center.orb.local/v1/authz/check-instance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"host:read","resource_type":"host","instance_id":"web-01"}'
echo " (预期: allow)"

# 测试 check-instance（开发环境主机应该 deny）
echo "3. 测试 check-instance dev-01"
curl -s -X POST "https://api.permission-center.orb.local/v1/authz/check-instance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"host:read","resource_type":"host","instance_id":"dev-01"}'
echo " (预期: deny)"
```

#### 4.3 验收标准

- [ ] 端点权限验证通过（GET 200, POST 403）
- [ ] 数据权限验证通过（只看到 prod 主机）
- [ ] 验证脚本可一键运行

---

### Phase 5：演示脚本（Day 3）

#### 5.1 演示脚本

**文件**：`scripts/demo-xiaohuang-xiaohong.sh`

```bash
#!/bin/bash
# 小黄小红演示脚本

echo "=========================================="
echo "  权限中心演示：小黄 vs 小红"
echo "=========================================="

echo ""
echo "【第一部分：小黄的应用管理】"
echo ""
echo "1. 登录小黄账号"
echo "   → 打开 https://frontend.permission-center.orb.local/login"
echo "   → 选择 '小黄（研发一部）'"
echo "   → 点击'一键登录'"
echo ""
echo "2. 进入应用管理"
echo "   → 点击左侧'应用管理'"
echo "   → 找到'小黄的监控服务'应用"
echo "   → 点击查看详情"
echo ""
echo "3. 查看能力包"
echo "   → 点击'查看该应用的能力'"
echo "   → 找到'主机监控'能力包"
echo "   → 点击'编辑'查看配置"
echo ""
echo "4. 查看预设"
echo "   → 展开'只读监控'预设"
echo "   → 展示绑定的接口（host:list, host:read）"
echo "   → 展示可申请范围设置"
echo ""
echo "5. 查看授权管理"
echo "   → 点击'授权管理'"
echo "   → 展示预设状态（已上架）"
echo "   → 展示授权统计"
echo ""

echo "=========================================="
echo ""
echo "【第二部分：小红的权限申请】"
echo ""
echo "1. 登录小红账号"
echo "   → 点击右上角'退出'"
echo "   → 选择'小红（研发二部）'"
echo "   → 点击'一键登录'"
echo ""
echo "2. 进入能力市场"
echo "   → 点击左侧'能力市场'"
echo "   → 找到'小黄的监控服务 - 主机监控'"
echo ""
echo "3. 申请权限"
echo "   → 点击'申请'"
echo "   → 选择主体：小红自己"
echo "   → 选择预设：只读监控"
echo "   → 填写理由：'需要监控生产环境主机'"
echo "   → 提交申请"
echo ""
echo "4. 等待审批"
echo "   → 进入'审批中心'"
echo "   → 看到小黄的待审批单"
echo "   → 小黄登录审批通过（演示时可跳过）"
echo ""

echo "=========================================="
echo ""
echo "【第三部分：权限验证】"
echo ""
echo "1. 端点权限验证"
echo "   → 打开终端"
echo "   → 运行: bash scripts/verify-permissions.sh"
echo "   → 展示 GET /api/v1/hosts → 200"
echo "   → 展示 POST /api/v1/hosts → 403"
echo ""
echo "2. 数据权限验证"
echo "   → 运行: bash scripts/verify-data-permissions.sh"
echo "   → 展示 filter 只返回生产环境主机"
echo "   → 展示 check-instance prod → allow"
echo "   → 展示 check-instance dev → deny"
echo ""
echo "=========================================="
echo ""
echo "【演示总结】"
echo ""
echo "核心价值展示："
echo "  ✅ 应用注册与管理"
echo "  ✅ 能力包声明与配置"
echo "  ✅ 预设上架（走审批）"
echo "  ✅ 能力市场浏览与申请"
echo "  ✅ 双主体申请（人 + 程序）"
echo "  ✅ 审批流程"
echo "  ✅ 端点权限控制"
echo "  ✅ 数据权限控制"
echo ""
echo "=========================================="
```

#### 5.2 验收标准

- [ ] 演示脚本输出清晰的步骤说明
- [ ] 所有步骤可按顺序执行
- [ ] 演示时间控制在 10 分钟内

---

## 四、测试验证流程

### 4.1 测试分类

| 类型 | 内容 | 工具 |
|------|------|------|
| **流程验证** | 端到端业务流程 | demo 脚本 |
| **权限验证** | 端点 + 数据权限 | curl + jq |

### 4.2 测试脚本

#### 流程验证脚本

**文件**：`scripts/test-flow.sh`

```bash
#!/bin/bash
# 流程验证

echo "=== 1. 登录验证 ==="
# 测试小黄登录
# 测试小红登录

echo "=== 2. 应用注册验证 ==="
# 测试小黄应用注册
# 测试小红应用注册

echo "=== 3. 能力包验证 ==="
# 测试能力包创建
# 测试预设配置
# 测试预设上架

echo "=== 4. 申请审批验证 ==="
# 测试申请提交
# 测试审批通过
# 测试策略生效

echo "=== 流程验证完成 ==="
```

#### 权限验证脚本

**文件**：`scripts/test-permissions.sh`

```bash
#!/bin/bash
# 权限验证

echo "=== 端点权限验证 ==="
# GET /api/v1/hosts → 200
# POST /api/v1/hosts → 403

echo "=== 数据权限验证 ==="
# filter → 只返回 prod 主机
# check-instance prod → allow
# check-instance dev → deny

echo "=== 权限验证完成 ==="
```

### 4.3 执行顺序

```bash
# 1. 重新部署
make up

# 2. Seed 数据
make seed

# 3. 流程验证
bash scripts/test-flow.sh

# 4. 权限验证
bash scripts/test-permissions.sh

# 5. 演示验证
bash scripts/demo-xiaohuang-xiaohong.sh
```

---

## 五、时间线

| 日期 | 任务 | 产出 |
|------|------|------|
| **Day 1** | Seed 数据 + 前端优化 | 小黄小红用户 + 应用 + 能力包 |
| **Day 2** | 审批优化 + 权限验证 | 审批流程 + 验证脚本 |
| **Day 3** | 演示脚本 + 最终验证 | 演示脚本 + 全流程通过 |

---

## 六、验收清单

### Seed 数据

- [ ] 小黄用户可登录
- [ ] 小红用户可登录
- [ ] 小黄的应用已注册
- [ ] 小红的应用已注册
- [ ] 能力包已创建
- [ ] 预设已上架

### 前端界面

- [ ] 登录页可快速选择小黄/小红
- [ ] 能力市场清晰展示能力信息
- [ ] 申请向导双主体选择流畅
- [ ] 审批中心显示完整信息

### 权限验证

- [ ] 端点权限：GET 200, POST 403
- [ ] 数据权限：只看到 prod 主机
- [ ] check-instance prod → allow
- [ ] check-instance dev → deny

### 演示脚本

- [ ] 演示脚本可一键运行
- [ ] 所有步骤清晰说明
- [ ] 演示时间 < 10 分钟

---

*计划制定于 2026-08-06*
