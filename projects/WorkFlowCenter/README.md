# 工作流平台 - 流程驱动的业务自动化平台

> 以流程为载体、以原子能力为执行单元、以自动办理为效率手段，帮助用户"把事办成"。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 + Django 5 + DRF |
| 前端 | Vue 3 + Vite + Element Plus |
| 数据库 | PostgreSQL 16 |
| 缓存/队列 | Redis 7 + Celery |
| 流程建模 | LogicFlow |
| 部署 | Docker Compose + OrbStack |

## 快速开始

```bash
# 1. 启动所有服务
docker compose up -d

# 2. 初始化数据（首次 / 全新库，写入基础种子数据）
docker compose exec api python manage.py seed_data

# 3. 访问
# 前端: http://frontend.workflow.orb.local
# API:  http://api.workflow.orb.local/api/v1/docs/
# Admin: http://frontend.workflow.orb.local/admin/
```

> 若希望直接一键还原到「Demo 最佳状态」（含演示运行数据），可跳过第 2 步改用下方的 `reset_demo`。

## 一键重置数据（删除重建，还原 Demo 最佳状态）

### 这个命令解决什么问题

开发 / 演示过程中，数据库会不断积累运行数据（发起的流程、待办任务、审批记录、能力执行日志等），也可能被手动改乱。`reset_demo` 提供一种**强制删除重建**能力：无论数据库当前处于什么状态（已跑过流程、手改过数据、甚至没有数据库文件的全新库），执行后都会还原到发布时的「Demo 最佳状态」——即 `backend/seed/fixtures/demo_full.json` 中记录的完整快照。

### 操作步骤

```bash
# Docker 环境（推荐）
docker compose exec api python manage.py reset_demo

# 本地环境
cd backend
python manage.py reset_demo
```

执行后包含的数据：

- **基础种子数据**：部门 / 用户 / 角色 / 权限 / 能力 / 工单类型 / 发起程序 / 流程定义
- **预置流程实例**：`SRV-2026-001/002/003`（含待办节点任务）
- **演示运行数据**：`WI-*` 流程实例、节点任务、审批记录、能力任务作业、FSM 状态日志
- **演示增强数据**（`seed_demo_data`）：进行中的待办审批（`DM-2026-001~003`）、管理员已办（`DM-2026-011/012`）、抄送记录——保证 admin 等账号登录后**待办 / 已办 / 抄送 / 我发起的**各列表都有内容可演示

默认账号：`admin/admin123`（管理员）、`xiaoming` ~ `xiaozhao`（均 `user123`）。

### 实现原理

`reset_demo` 依次执行四步：

1. `migrate` — 确保表结构就绪（幂等，全新库会自动建表）
2. `flush` — 清空所有数据表并重置自增序列（即删除）
3. `loaddata demo_full` — 恢复完整 Demo 快照（即重建）
4. `seed_demo_data` — 补齐待办 / 已办 / 抄送演示数据（幂等）

### 更新数据快照

当「Demo 最佳状态」需要调整（比如新增了流程定义、跑出了一条更完整的演示数据）时，先调整好数据库，再重新生成快照覆盖旧文件：

```bash
cd backend
python manage.py dumpdata --natural-primary --natural-foreign \
  -e admin.logentry -e sessions.session \
  > seed/fixtures/demo_full.json
```

> 注意：`reset_demo` 与 `seed_data` 定位不同——`seed_data` 只写基础种子数据（面向首次初始化，非幂等）；`reset_demo` 是完整快照删除重建（面向随时重置，且幂等可重复执行）。

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| agent1 | agent123 | 运维代理 |
| user1 | user123 | 普通用户 |
| cfo | cfo123 | CFO |

## 核心功能

1. **流程引擎** - 自研轻量引擎，API 对齐行业标准（start/complete/claim/delegate/suspend/resume/terminate）
2. **会签/或签** - 多实例审批 + 完成条件（全部通过/任一通过/百分比）
3. **条件路由** - 排他网关语义，支持表达式求值 + 默认路径
4. **能力注册中心** - 契约化能力（JSON Schema）+ 同步/异步执行
5. **自动办理** - 策略驱动 + 审计留痕
6. **工单业务** - ITSM 状态机 + 评论 + 通知
7. **事件总线** - 领域事件 + Webhook 投递

## 演示流程

```bash
# 自动演示完整流程
docker compose exec api python scripts/demo.py
```

## 架构概览

```
Vue3 Frontend → Nginx → Django REST API → PostgreSQL
                                  ↓
                            Celery Worker → Redis Streams
                                  ↓
                            能力执行器 (Mock/HTTP)
```

## 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data   # 首次初始化基础种子数据
python manage.py reset_demo  # （可选）一键删除重建回 Demo 最佳状态
python manage.py runserver

# 前端
cd frontend
npm install
npm run dev
```

## 项目结构

```
workflow/
├── docker-compose.yml          # Docker 编排
├── backend/                    # Django 后端
│   ├── config/                 # 项目配置
│   ├── apps/
│   │   ├── accounts/           # 用户/部门/角色
│   │   ├── processes/          # 流程引擎（核心）
│   │   ├── capabilities/       # 能力注册中心
│   │   ├── tickets/            # 工单业务层
│   │   ├── events/             # 事件总线
│   │   └── common/             # 公共工具
│   ├── seed/                   # 种子数据
│   └── scripts/                # 演示脚本
└── frontend/                   # Vue 3 前端
    └── src/
        ├── views/              # 页面组件
        ├── components/         # 公共组件
        │   ├── FlowModeler/    # LogicFlow 流程建模
        │   ├── FormBuilder/    # 表单构建器
        │   ├── FormRenderer/   # 表单渲染器
        │   └── Timeline/       # 流程时间线
        ├── api/                # API 封装
        ├── stores/             # Pinia 状态
        └── router/             # 路由配置
```
