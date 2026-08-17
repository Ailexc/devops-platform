# ============================================================
# DevOpsPlatform —— 统一命令手册
# 目标：一套命令管理 7 个系统（统一构建 / 部署 / 数据重置）
# ============================================================

## 快速开始

```bash
# 1. 启动统一基础设施（PostgreSQL + Redis）并创建 10 个业务库
make bootstrap

# 2. 查看状态
make status

# 3. 启动单个项目（短名：auth/cloud/event/iam/release/cmdb/workflow）
make start P=auth

# 4. 打开统一门户（Authentication Portal）
make portal
```

## 命令一览

| 命令 | 作用 | 示例 |
|------|------|------|
| `make help` | 显示帮助 | `make help` |
| `make bootstrap` | 启动统一 PG+Redis，创建 `devops_*` 10 库 | `make bootstrap` |
| `make status` | 查看基础设施与业务容器状态 | `make status` |
| `make build [P=]` | 构建镜像（单项目/全部） | `make build P=iam` |
| `make up [P=]` | 启动（单项目/全部，不重置数据） | `make up P=auth` |
| `make start [P=]` | 统一启动入口（支持 `RESET_ON_START`） | `make start P=auth` |
| `make down [P=]` | 停止（保留数据卷） | `make down` |
| `make seed [P=]` | 初始化数据 | `make seed P=event` |
| `make reset [P=]` | 数据重置（回到出厂态） | `make reset P=workflow` |
| `make reset` | 删除重建统一 10 库 + 逐项目重置 | `make reset` |
| `make logs P=xxx` | 查看单项目日志 | `make logs P=release` |
| `make portal` | 打开统一门户 | `make portal` |
| `make gateway-up` | 启动统一网关（Traefik，入口 `*.devops.orb.local`） | `make gateway-up` |
| `make gateway-down` | 停止统一网关 | `make gateway-down` |
| `make gateway-ps` | 查看统一网关状态 | `make gateway-ps` |

## 统一网关（Phase 3）

Traefik 把 7 个系统聚合到统一入口 `*.devops.orb.local`（本地 OrbStack 自动 DNS + 端口 8088）。

| 统一入口 | 目标 |
|----------|------|
| `portal.devops.orb.local` | 统一认证门户 |
| `cloud.devops.orb.local` | CloudManager |
| `event.devops.orb.local` | EventManager |
| `iam.devops.orb.local` | PermissionCenter |
| `release.devops.orb.local` | ReleaseManager |
| `cmdb.devops.orb.local` | TaskManager |
| `workflow.devops.orb.local` | WorkFlowCenter |
| `api.auth.devops.orb.local` | 认证 API 直连 |
| `traefik.devops.orb.local` | Traefik Dashboard |

- 网关工程：`infra/gateway/`（docker-compose + traefik.yml + dynamic/routes.yml）
- 路由按 Host 规则分发到各系统 frontend 容器（均已在 `devops-net`）
- 非 OrbStack 环境（如 ECS）：`http://<host>:8088` + Host 头（或 DNS 泛解析）
- 前端 `/api` 仍由各系统自身 nginx 同源反代到各自 backend，网关只做 Host 转发


## 统一启动与 RESET_ON_START（Phase 2）

`make start` 是统一启动入口，语义：

- **普通启动**：`make start P=auth` —— 幂等启动（保留现有数据）
- **先重置再启动**：`RESET_ON_START=true make start P=auth` —— 启动前先走统一 reset
  （drop schema → migrate → 幂等种子），数据回到出厂态
- 支持值：`true / 1 / yes / on`（大小写均可）
- 不带 `P=` 时作用于全部 7 个项目；`RESET_ON_START=true` 时先全量重置再全量启动

> 对比：`make up` = 纯启动（不重置）；`make reset` = 纯重置（不启动）。
> `make start` 把两者按需组合，适合演示前快速恢复干净环境。

## 统一基础设施约定

- **PostgreSQL**：容器 `devops-postgres`，一实例多库：
  `devops_auth / devops_cloud / devops_event / devops_event_go / devops_iam / devops_openfga / devops_release / devops_cmdb / devops_cmdb_go / devops_workflow`
- **Redis**：容器 `devops-redis`，各项目按 db index 隔离（0~8）：缓存 + Celery 结果存储
- **RabbitMQ**：容器 `devops-rabbitmq`，统一消息队列（Celery broker，AMQP）：
  - 账号 `devops/devops`（vhost `/`）；管理台 `http://localhost:25673`
  - 队列规范：各系统用专属队列（`event` / `aws,connector,inspection,default`），互不干扰
- **网络**：`devops-net`（业务容器加入后可用主机名直连）
- **宿主机调试口**：PostgreSQL `localhost:25432`、Redis `localhost:26379`、RabbitMQ `localhost:25672`（刻意避开现有端口）

## 连接串

```bash
# 容器内（业务容器加入 devops-net 后）
DATABASE_URL=postgresql://devops:devops@devops-postgres:5432/devops_<项目>
REDIS_URL=redis://devops-redis:6379/<index>
CELERY_BROKER_URL=amqp://devops:devops@devops-rabbitmq:5672//

# 宿主机调试
postgresql://devops:devops@localhost:25432/devops_<项目>
redis://localhost:26379/<index>
amqp://devops:devops@localhost:25672//
```

## 项目短名对照

| 短名 | 目录 | 库 | Redis index |
|------|------|----|-------------|
| auth | Authentication | devops_auth | 0 |
| cloud | CloudManager | devops_cloud | 1 |
| event | EventManager | devops_event | 2 |
| iam | PermissionCenter | devops_iam | 3 |
| release | ReleaseManager | devops_release | 4 |
| cmdb | TaskManager | devops_cmdb | 5 |
| workflow | WorkFlowCenter | devops_workflow | 6 |
