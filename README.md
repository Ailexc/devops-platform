# DevOps 平台合集（DevOpsPlatform）

> 一个由 **7 个独立开发的全栈系统** 组成的企业级 DevOps 内部系统全家桶 —— 统一认证、多云管理、事件治理、权限中心、发布流水线、CMDB 数据平台、流程自动化。
>
> 每一个子项目都是完整的可运行 Demo（前端 + 后端 + 数据库 + 网关），既可独立演示，也可串成一条「多云 DevOps 平台」的完整故事线。
> 该合集作为个人技术作品集，用于面试展示与复盘。

[🚀 在线展示页（showcase）](./docs/showcase/index.html) · [📖 统一门户说明](./projects/Authentication/README.md) · [🧭 免费部署计划](./免费部署计划.md)

---

## 一、项目定位

| 视角 | 说明 |
|------|------|
| **合集本质** | 7 个完整全栈系统，覆盖企业内部平台开发的高频场景 |
| **技术纵深度** | 前端（React / Vue3）+ 后端（Python / Go）+ 网关（Traefik）+ 数据库（SQLite / PostgreSQL）+ 消息（Redis / RabbitMQ）+ 容器编排（Docker Compose / OrbStack / kind） |
| **面试叙事线** | 从「登录认证 → 权限管控 → 业务系统」一层层讲，每个系统都有明确的业务价值与技术亮点 |
| **演示方式** | 各系统独立 Docker Compose 一键启动；统一门户（Authentication Portal）作为总入口 |

---

## 二、全家桶架构总览

```
                         ┌─────────────────────────────────────────┐
                         │          🌐 用户 / 面试官 / 访问者        │
                         └───────────────────┬─────────────────────┘
                                             │
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │   🚪 统一门户  Authentication Portal      │
                         │   (React 19 · 应用广场 · 一键登录)         │
                         └───────────────────┬─────────────────────┘
                                             │ RS256 JWT (SSO 单点登录)
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │   🛡 统一网关 Traefik (forwardAuth 鉴权)   │
                         │   认证中心 FastAPI · JWKS 公钥 · 身份源降级  │
                         └───────┬──────────────┬───────────────────┘
                                 │              │
          ┌──────────────────────┼──────────────┼──────────────────────┐
          │                      │              │                      │
          ▼                      ▼              ▼                      ▼
 ┌────────────────┐  ┌────────────────┐ ┌────────────────┐  ┌────────────────┐
 │ 认证中心        │  │ 权限中心        │ │ 发布系统        │  │ 工作流平台       │
 │ Authentication │  │ Permission     │ │ ReleaseManager │  │ WorkFlowCenter  │
 │ React+FastAPI  │  │ Go+Casbin+OpenFGA│ │ Django+React   │  │ Django+LogicFlow│
 └────────────────┘  └────────────────┘ └────────────────┘  └────────────────┘
          │                      │              │                      │
          ▼                      ▼              ▼                      ▼
 ┌────────────────┐  ┌────────────────┐ ┌────────────────┐  ┌────────────────┐
 │ 多云管理        │  │ CMDB 数据平台   │ │ 事件管理        │  │                │
 │ CloudManager   │  │ TaskManager    │ │ EventManager   │  │  业务系统矩阵    │
 │ Vue3+Django    │  │ Django+Celery  │ │ Python+Go 双栈  │  │  (可继续扩展)    │
 └────────────────┘  └────────────────┘ └────────────────┘  └────────────────┘
          │                      │              │
          └──────────────────────┼──────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │   基础设施 & 数据层        │
                    │  PostgreSQL/SQLite/Redis  │
                    │  RabbitMQ · Celery · kind │
                    └──────────────────────────┘
```

> 详细架构图见 [docs/overall-architecture.md](./docs/overall-architecture.md)；动态版见 [showcase/index.html](./docs/showcase/index.html)。

---

## 三、系统速览

| # | 系统 | 一句话定位 | 技术栈 | 核心亮点 |
|---|------|-----------|--------|----------|
| 1 | **Authentication** 统一认证中心 | 统一门户 + SSO 单点登录 + 统一网关 | React 19 + FastAPI + Traefik + OpenLDAP | 身份源抽象与降级链 · RS256 JWT + JWKS · forwardAuth 网关鉴权 |
| 2 | **CloudManager** 多云管理系统 | 仿 AWS 控制台的多云资源管理 | Vue 3 + Django + MySQL/Redis + RabbitMQ | 操作走工单系统（流程治理）· CMDB 唯一数据源 · 多云适配层 |
| 3 | **EventManager** (EventFlow) | 多事件源统一接入与监控 | Python Django + Go 双栈 + PostgreSQL + RabbitMQ | Python/Go 双栈同构 · AWS/GitHub/内部事件源 · DLQ 监控 |
| 4 | **PermissionCenter** 权限中心 | 现代化 IAM（API 级 + 数据级鉴权） | Go + Vue 3 + Casbin + OpenFGA + Redis | PEP/PDP/PAP/PIP 外部化授权 · 双引擎 · 策略分发 · M2M · IGA |
| 5 | **ReleaseManager** 发布系统 | CI/CD 发布流水线全链路 | Django DRF + React 18 + FastAPI + kind K8s | 灰度/蓝绿/滚动发布 · 回滚 · 复杂权限模型 · 配置中心 |
| 6 | **TaskManager** CMDB 数据平台 | 多云资产自动采集与调度大盘 | Django + Celery + Vue 3 + PostgreSQL（含 Go 重写版） | 任务树编排 · Celery Beat 动态调度 · 关系编排 · 运维大盘 |
| 7 | **WorkFlowCenter** 工作流平台 | 流程驱动的业务自动化 | Django 5 + Vue 3 + LogicFlow + PostgreSQL 16 | 自研流程引擎 · 会签/或签 · 能力注册中心 · 自动办理 · 事件总线 |

---

## 四、Monorepo 目录结构

```
DevOpsPlatform/
├── README.md                # 👈 本文件：合集说明
├── Makefile                 # 统一管理入口（make / make start / make reset ...）
├── docs/
│   ├── overall-architecture.md  # 整体架构图（Mermaid）
│   ├── showcase/                # 🚀 项目介绍展示页（静态可部署，滚动画卷式）
│   └── ...                      # 治理规范 / 部署方案 / 端口分配等
├── deploy/                  # 多环境变量（local / cloud / server）
├── infra/                   # 统一基础设施（PG/Redis/RabbitMQ）+ 统一网关（Traefik）
├── scripts/                 # 平台编排脚本（start / reset 契约调用 / deploy / ports...）
├── 免费部署计划.md           # Render 免费部署方案
└── projects/                # ← 业务项目层（7 个真实系统）
    ├── Authentication/      # 统一认证中心（统一门户 + SSO）
    ├── CloudManager/        # 多云管理系统
    ├── EventManager/        # 事件管理系统（EventFlow，Python + Go 双栈）
    ├── PermissionCenter/    # 权限中心（IAM）
    ├── ReleaseManager/      # 发布系统（含 executor / demo-apps / k8s）
    ├── TaskManager/         # CMDB 数据维护平台（Django + Go 双栈）
    └── WorkFlowCenter/      # 工作流平台
```

---

## 五、快速开始

### 统一管理入口（推荐，根目录 Makefile）

7 个系统已统一接入根目录管理的 PostgreSQL/Redis 数据层，用一套命令管理全部：

```bash
# 1. 启动统一基础设施（PostgreSQL + Redis）并创建 10 个业务库
make bootstrap

# 2. 启动全部 / 单个系统
make start                 # 全部 7 个系统
make start P=auth          # 只启动 Authentication

# 3. 演示前快速恢复干净环境（先重置出厂态再启动）
RESET_ON_START=true make start P=cmdb
RESET_ON_START=true make start    # 全量重置 + 全量启动

# 4. 其他常用
make status                # 查看状态
make reset P=release       # 单系统数据重置（出厂态）
make reset                 # 全量重置（10 库重建 + 逐系统重置）
make backup                # 统一备份
make portal                # 打开统一门户
make gateway-up            # 启动统一网关（Traefik 聚合 7 系统）
```

### 统一入口（统一网关）

`make gateway-up` 后，7 个系统统一收敛到 `*.devops.orb.local`（本地 OrbStack 自动 DNS）：

```
portal.devops.orb.local    → 统一认证门户
cloud/event/iam/release/cmdb/workflow.devops.orb.local → 各业务系统
traefik.devops.orb.local   → Traefik Dashboard
```

> 统一命令手册见 [docs/commands.md](./docs/commands.md)；**整体架构设计文档（交互式 HTML）见 [docs/architecture.html](./docs/architecture.html)**；
> 统一部署与数据层方案见
> [docs/统一部署与管理方案.md](./docs/统一部署与管理方案.md)、[docs/统一管理实施计划.md](./docs/统一管理实施计划.md)。

### 总入口：统一门户（推荐先看）

```bash
cd Authentication
docker compose up -d --build
# 访问 http://portal.authentication.orb.local （统一门户 / 应用广场）
```

演示账号：`admin / admin1234`（管理员）、`zhangsan / demo1234`（普通用户）。

### 各系统一键启动

每个系统都是独立完整的 Docker Compose 工程，入口见各子目录 README：

| 系统 | 快速开始 | 本地访问（OrbStack） |
|------|----------|---------------------|
| Authentication | [README](./projects/Authentication/README.md) | `portal.authentication.orb.local` |
| CloudManager | [README](./projects/CloudManager/README.md) | `cloud-manager-nginx.orb.local` |
| EventManager | [README](./EventManager/README.md) | `frontend.event-management.orb.local` |
| PermissionCenter | [README](./PermissionCenter/README.md) | `frontend.permission-center.orb.local` |
| ReleaseManager | [README](./ReleaseManager/README.md) | `frontend.release-system.orb.local` |
| TaskManager | [README](./TaskManager/README.md) | `localhost`（Docker Compose） |
| WorkFlowCenter | [README](./WorkFlowCenter/README.md) | `frontend.workflow.orb.local` |

> 💡 多项目同时开发时遵循 OrbStack 域名约定（不暴露端口、不写死 localhost），详见 [CloudManager/DEV_CONVENTION.md](./projects/CloudManager/DEV_CONVENTION.md)。

---

## 六、面试演示建议

1. **打开展示页** [showcase/index.html](./docs/showcase/index.html) —— 用滚动动画先讲一遍全家桶整体架构
2. **进入统一门户** —— 展示 SSO 登录、应用广场、一键跳转业务系统
3. **逐个系统深挖** —— 按面试官兴趣选择 1~2 个系统演示核心链路（权限中心 / 发布系统 / 工作流平台均有现成 demo 脚本）
4. **技术点收尾** —— 各项目 `docs/` 均有面试准备文档（叙事线 + 高频问题）

---

## 七、部署说明

- **本展示页**：纯静态单文件，可部署到 GitHub Pages / Cloudflare Pages / Render 任意静态托管，见 [docs/showcase/README.md](./docs/showcase/README.md)
- **全套系统**：Render 免费 Hobby 计划（每个系统一个 Web Service + SQLite），详见 [免费部署计划.md](./免费部署计划.md)

---

## 八、技术栈矩阵

| 层级 | 技术选型 |
|------|----------|
| 前端 | React 19 / React 18 / Vue 3 · Ant Design / Element Plus · Vite · LogicFlow |
| 后端 | Python（FastAPI / Django / DRF / Ninja）+ Go（Gin / GORM）+ Celery |
| 网关 | Traefik（forwardAuth 统一鉴权） |
| 认证 | RS256 JWT + JWKS · SSO · OIDC · 身份源降级链（Local/LDAP/Okta） |
| 授权 | Casbin（RBAC/ABAC）· OpenFGA（ReBAC）· PEP/PDP 外部化授权 |
| 数据库 | SQLite / PostgreSQL / MySQL |
| 缓存/消息 | Redis · RabbitMQ · Celery Beat |
| 容器编排 | Docker Compose · OrbStack · kind（本地 K8s） |

---

## License

本合集为个人技术作品集 Demo，仅供学习与面试展示使用。
