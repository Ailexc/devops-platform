# 发布系统 Demo — 应用管理模块优化 + 镜像管理开发计划

> 基于 2026-07-27 讨论结果整理

---

## 一、概述

本次开发主要针对 **应用管理** 模块（`/apps` 路由）进行优化，同时新增独立的 **镜像管理** 模块（`/images` 路由），将原先隐藏在应用中的镜像配置以独立菜单形式呈现，逻辑更清晰。

涉及：应用列表页、应用详情页、镜像注册表管理页、环境配置展示方式。同时对齐后端 API 响应格式（`{code, data}` 包装）。

---

## 二、分期计划

### 第一期：基础修复（当前已完成）

| # | 任务 | 状态 | 说明 |
|---|------|------|------|
| 1.1 | 应用列表页数据格式修复 | ✅ 已完成 | `appApi.list()` 返回 `{code, data}`，前端适配 |
| 1.2 | 详情页数据格式修复 | ✅ 已完成 | `appApi.detail()` / `envConfigs.list()` 返回格式对齐 |
| 1.3 | 编辑弹窗空白修复 | ✅ 已完成 | `fetchFormData` 中 `blRes?.data` 解包 |
| 1.4 | 业务线/负责人显示数字 | ✅ 已完成 | 改为使用 `business_line_name` / `owner_name` |

### 第二期：镜像管理模块（新增）

| # | 任务 | 优先级 | 工作量 | 说明 |
|---|------|--------|--------|------|
| 2.1 | 后端 ImageRegistry 模型 + migration | P0 | ~30min | 按语言管理的镜像注册表 |
| 2.2 | 后端 CRUD API（`/api/v1/images/`） | P0 | ~30min | 含种子数据接口 |
| 2.3 | 前端镜像管理列表页 | P0 | ~1h | 表格展示 + 增删改 |
| 2.4 | 前端菜单项 + 路由注册 | P0 | ~10min | 侧边栏新增"镜像管理" |
| 2.5 | seed 数据中初始化镜像注册表 | P0 | ~15min | 每种语言预设默认镜像对 |

### 第三期：UI/交互优化

| # | 任务 | 优先级 | 工作量 | 文件 |
|---|------|--------|--------|------|
| 3.1 | 应用列表页去掉"编辑"按钮 | P0 | ~10min | `apps/index.tsx` |
| 3.2 | 应用详情页改为环境类型 Tab 展示 | P0 | ~2h | `apps/detail.tsx` |
| 3.3 | 应用详情页去掉"添加环境"按钮 | P0 | ~5min | `apps/detail.tsx` |
| 3.4 | 应用详情页返回按钮修正 | P1 | ~5min | `apps/detail.tsx` |

### 第四期：镜像编辑联动

| # | 任务 | 优先级 | 工作量 | 说明 |
|---|------|--------|--------|------|
| 4.1 | 应用编辑弹窗补充两个镜像字段 | P0 | ~1h | `apps/detail.tsx` |
| 4.2 | 仅允许编辑两个镜像，其他只读 | P0 | ~20min | 详情页信息展示区 |
| 4.3 | 应用创建时按语言自动填充默认镜像 | P1 | ~30min | 调用 ImageRegistry 默认值 |
| 4.4 | 应用详情页展示当前镜像 + 来源说明 | P1 | ~30min | 显示来自镜像注册表或自定义 |

### 第五期：配置模板（后续迭代）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 5.1 | 应用级别配置模板 CRUD | P2 | 存放应用特性配置 |
| 5.2 | 环境类型级别配置模板 CRUD | P2 | 存放环境差异配置 |
| 5.3 | 配置渲染引擎 | P2 | base + overlay 合并渲染 |
| 5.4 | 审批模板绑定到环境类型维度 | P2 | 当前模型已支持，仅需页面入口 |

---

## 三、详细设计

### 3.1 镜像注册表模型

```python
class ImageRegistry(models.Model):
    """镜像注册表 - 按开发语言管理默认的双镜像配置"""
    language = models.CharField(max_length=16, choices=LANGUAGES, unique=True)
    builder_image = models.CharField(max_length=128, verbose_name="环境基础镜像",
                                     help_text="CI 编译阶段使用，含编译器/工具链")
    base_image = models.CharField(max_length=128, verbose_name="应用基础镜像",
                                  help_text="CD 运行阶段使用，预装运行环境")
    description = models.TextField(blank=True, verbose_name="说明")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "image_registry"
        verbose_name = "镜像注册表"
        verbose_name_plural = "镜像注册表"
```

**种子数据**（参考 Spug 映射规则）：

| 语言 | 环境基础镜像 (builder) | 应用基础镜像 (base) |
|------|----------------------|--------------------|
| Go | `golang:1.23-alpine` | `alpine:3.20` |
| Python | `python:3.11-slim` | `python:3.11-slim` |
| Node.js | `node:20-alpine` | `node:20-alpine` |
| Java | `maven:3.9-eclipse-temurin-21` | `eclipse-temurin:21-jre-alpine` |
| 其他 | `alpine:3.20` | `alpine:3.20` |

### 3.2 镜像管理页面

```
侧边栏菜单：
  ── 发布管理 ──
     应用列表
     发布知识库
  ── 制品管理 ──
  ── 镜像管理 ──        ← 新增
     镜像注册表
  ── 配置管理 ──
```

```
┌─ 镜像注册表 ──────────────────────────────────┐
│  [+ 新增镜像配置]                              │
│                                                │
│  开发语言  │ 环境基础镜像         │ 应用基础镜像  │ 操作 │
│  ─────────┼─────────────────────┼──────────────┼──────│
│  Go       │ golang:1.23-alpine  │ alpine:3.20  │ 编辑  │
│  Python   │ python:3.11-slim    │ python:3.11  │ 编辑  │
│  Node.js  │ node:20-alpine      │ node:20-alp  │ 编辑  │
│  Java     │ maven:3.9-...       │ temurin:21   │ 编辑  │
│  其他     │ alpine:3.20         │ alpine:3.20  │ 编辑  │
└──────────────────────────────────────────────────┘
```

### 3.3 应用创建/编辑时镜像联动

- 新建应用时，选择语言后自动从 `ImageRegistry` 获取默认镜像值填入表单
- 应用详情页展示当前使用的两个镜像及其来源说明
- 编辑时仅允许修改 `builder_image` 和 `base_image`，其余信息只读展示

```
┌─ 编辑镜像配置 ─────────────────────────────────┐
│  应用：支付核心服务 (payment-api)              │
│  开发语言：Go                                  │
│                                                │
│  环境基础镜像（CI 构建用）                     │
│  ┌──────────────────────────────────────────┐  │
│  │ golang:1.23-alpine                       │  │
│  └──────────────────────────────────────────┘  │
│  ℹ️ 编译器/工具链，编译阶段使用，用完即销毁     │
│                                                │
│  应用基础镜像（CD 运行用）                     │
│  ┌──────────────────────────────────────────┐  │
│  │ alpine:3.20                              │  │
│  └──────────────────────────────────────────┘  │
│  ℹ️ 预装运行环境，编译产物 COPY 后推送到 ECR   │
│                                                │
│              [取消]  [保存]                     │
└─────────────────────────────────────────────────┘
```

### 3.4 应用详情页改造

```
┌─ 支付核心服务 ─────────────────────────────────┐
│  ┌─ 基本信息 ───────────────────────────────┐  │
│  │  应用名称：支付核心服务                    │  │
│  │  编码：payment-api                        │  │
│  │  开发语言：Go                             │  │
│  │  环境基础镜像：golang:1.23-alpine  [编辑]  │  │
│  │  应用基础镜像：alpine:3.20         [编辑]  │  │
│  │  ...                                      │  │
│  └───────────────────────────────────────────┘  │
│                                                │
│  ┌─ 环境配置 ───────────────────────────────┐  │
│  │  [开发]  [测试]  [预发]  [生产]  ← Tab   │  │
│  │                                           │  │
│  │  环境    集群    命名空间  部署策略  副本数  │  │
│  │  ──────────────────────────────────────── │  │
│  │  开发环境  dev-clus  dev-ns  滚动更新  1   │  │
│  │  (仅展示，不可编辑)                        │  │
│  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 3.5 响应格式统一

所有后端 API 统一返回 `{"code": 200, "data": ...}` 格式，前端统一使用 `res?.data` 解包。

---

## 四、影响范围

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/apps/applications/models.py` | 新增 | `ImageRegistry` 模型 |
| `backend/apps/applications/migrations/` | 新增 | 镜像注册表 migration |
| `backend/apps/applications/views.py` | 新增 | `image_registry_list` / `_detail` 视图 |
| `backend/apps/applications/urls.py` | 新增 | 镜像注册表路由 |
| `backend/apps/accounts/management/commands/init_seed.py` | 修改 | 初始化镜像注册表种子数据 |
| `frontend/src/pages/apps/index.tsx` | 修改 | 去掉编辑按钮 |
| `frontend/src/pages/apps/detail.tsx` | 重写 | Tab 展示环境 + 编辑镜像弹窗 |
| `frontend/src/pages/images/index.tsx` | 新增 | 镜像注册表管理页面 |
| `frontend/src/api/index.ts` | 修改 | 新增 imageApi |
| `frontend/src/App.tsx` | 修改 | 注册路由和菜单 |

---

## 五、不在此版本的范围

- 配置模板/变量模板（后续迭代）
- 审批模版的环境类型维度配置（后续迭代）
- 应用的其他字段编辑（只编辑镜像）
- 环境配置的编辑功能（仅展示）
