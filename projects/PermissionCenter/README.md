# 权限中心（Permission Center / IAM Demo）

现代化权限中心 demo：**API 层面 + 数据层面**权限管控，下游经网关统一接入。

> 背景叙事（面试用）：真实工作中开发过一套权限中心，因强耦合 CMDB、数据膨胀、权限配置繁琐、未调研业界方案而难用；本 demo 按"重构后的现代化方案"实现。

## 核心架构

```
控制面（低 QPS，管理）       数据面（高 QPS，鉴权执行）
  PAP 管理控制台 (Vue3)  ──▶  iam-server (PDP)
  Sync Connector         ──▶    Casbin（动作级 RBAC/ABAC）
                              OpenFGA（实例级 ReBAC：Check/ListObjects）
                              Redis（策略/决策缓存 + 事件流）
                              PostgreSQL（主存储）
下游接入 PEP：Traefik（forwardAuth → PDP） / mock-cmdb / mock-identity
```

关键设计：

- **PEP/PDP/PAP/PIP 外部化授权**，控制面/数据面分离，PDP 无状态可水平扩展
- **数据源解耦**：CMDB 事件同步 + 本地资源索引投影，CMDB 宕机仍可鉴权（stale-but-available）
- **双引擎授权**：动作级 Casbin + 实例级 OpenFGA（CNCF/Zanzibar），自研层收缩为翻译/适配
- **策略即数据**：策略版本化（policy_versions）+ 回滚 + 审计；数据策略 → OpenFGA 关系
- **策略分发**（借鉴 OPA bundle）：bundle 快照 + checksum + agent 本地动作级决策 + 状态上报
- **程序授权（M2M）**：OAuth2 Client Credentials，主体 service 与用户共用 PDP
- **开放自服务/弱管理员**：应用自注册 + owner 模型 + 权限市场 + 申请-审批-开通-回收（IGA）
- **身份同步**：mock-identity（SCIM 风格）+ Identity Connector + JML

## 快速开始（OrbStack 全栈部署，统一管理）

```bash
# 1. 构建镜像并启动全栈（基础设施 + iam-server/mock-cmdb/mock-identity/iam-agent/frontend）
#    后端：宿主机交叉编译 Linux/arm64 → alpine 最小运行时（golang 镜像源不可用）
#    前端：宿主机构建 dist → nginx 运行时（容器内 npm install 网络不稳定）
make up

# 2. 写入种子数据（容器内执行，Go 程序零 SQL）
make seed

# 3. 验证
curl localhost:18080/healthz

# 其它管理命令
make ps     # 查看全部服务状态
make logs   # 跟踪日志
make down   # 停止全部
```

OrbStack 中项目 `permission-center` 统一管理全部服务；`dev.orbstack.domains` 提供自动 DNS + 反代：

| 域名 | 服务 |
|------|------|
| `frontend.permission-center.orb.local` | 管理控制台（nginx 同源反代 /api /v1 → iam-server，无 CORS） |
| `api.permission-center.orb.local` | iam-server（管理 API + PDP） |
| `cmdb.permission-center.orb.local` | Traefik 网关（mock-cmdb 受保护业务 API） |

### 本地开发模式（可选）

容器外开发调试：`make up` 已启动基础设施后，先 `docker compose -f deploy/docker-compose.yml stop iam-server` 释放端口，
再 `make run` / `make run-cmdb` / `make run-id` / `make run-agent` / `make web` 本地运行。

### 网关 PEP（Traefik）

网关监听 `:19080`，`PathPrefix(/api/v1)` 路由 → forwardAuth 中间件链：
`pep-token`（注入共享密钥）→ `iam-authz`（整体转发到 iam-server `/v1/gateway/check`）。
PDP 侧完成"请求 → action 映射"（PEP 职责，对应 APISIX ext-authz 行为），deny-by-default。

```bash
# 业务侧身份头 X-User（用户用户名 / client:client_id）；X-App 可选，默认 cmdb
curl localhost:19080/api/v1/hosts -H "X-User: alice"
```

### 演示账号

| 类型 | 凭据 |
|------|------|
| 用户 | `admin` / `admin123`、`alice` / `pass123`、`bob` / `pass123` |
| 程序身份 (M2M) | `cloud-mgmt` / `cloud-mgmt-secret` |

### 一键演示

```bash
bash scripts/demo.sh
```

覆盖：动作级鉴权 → 无权限拦截 → 数据级 check-instance/filter → 程序身份(M2M) →
网关 PEP 链路（Traefik forwardAuth，allow/deny）→ CMDB 宕机降级 → 策略发布即时生效
（决策缓存失效）→ 本地 agent 决策。

### 数据管理与备份恢复（Seed / Backup / Restore）

**数据位置**：业务数据在 Docker 命名卷 `permission-center_pgdata`（PostgreSQL，含 IAM + OpenFGA）、
`permission-center_redisdata`（Redis），**不在容器内**。⚠️ 严禁 `docker compose down -v`
（`-v` 会删除命名卷导致数据直接丢失）。

**两条数据防线（推荐分工）**：

1. **Seed 初始化脚本（主）**：演示基准数据（应用 / 权限点 / 数据模型 / 能力包 / 授权）由
   `backend/cmd/iam-server/seed.go` 定义，版本化、幂等、可一键重建，随代码演进。
2. **数据库备份（补充）**：保留 seed 不覆盖的运行时痕迹——审批单（审批人/评论/流转）、
   审计日志、决策日志、OpenFGA 元组、token 等；适合还原某个演示现场或历史操作状态。

```bash
# —— Seed 系列（演示基准数据，日常首选）——
make seed          # 幂等补齐 demo 数据（不删已有数据，可重复跑）
make seed-reset    # 一键重置：清空 demo 表（ID 从 1 重排）→ 按最新 seed 重建
make reset-all     # 从零到可用：build 前后端 → 启动 → seed-reset → demo.sh 全链路验证

# —— 备份 / 恢复（运行时痕迹防线）——
make backup        # 备份 IAM 数据库 → backups/iam-<时间戳>.sql（含 --clean 便于直接恢复）
make restore       # 从备份恢复（默认取最新）：make restore [FILE=backups/xxx.sql]
```

> 说明：备份是**快照**，不随代码演进；schema 变更后旧备份恢复的数据与最新 seed 可能不一致
> （必要时恢复后再跑一次 `make seed` 补齐）。演示数据丢失直接 `make seed-reset` 重建即可，
> 无需手工恢复。演示前或大改动前可先 `make backup` 留存现场。

### 管理控制台（P5，Vue3）

```bash
# 容器化部署后直接访问（nginx 同源反代，无需本地 npm）：
#   http://frontend.permission-center.orb.local  或  http://localhost:18088

# 本地开发模式：
cd frontend
npm install
npm run dev     # http://localhost:5173（vite 代理 /api /v1 → :8080）
```

登录页默认 `admin/admin123`。页面：应用管理（注册/同步/权限点板块树）、用户、组织/组、
角色（板块式勾选树）、策略（API+数据级表单）、申请/审批（IGA 闭环）、审计/决策日志。

### 本地 PDP agent（P6）

```bash
# 容器化部署后已作为服务运行（轮询 bundle → checksum 校验 → 原子激活 → 本地动作级决策），
# 本地决策端点 localhost:19090/v1/local/check；demo.sh 步骤 11 自动验证。
# 本地开发模式：make run-agent
```

### 环境说明

- **OpenFGA**：⚠️ `openfga/openfga:v1.8.7` 为 **distroless** 镜像（仅 `/openfga` 二进制，无 `sh`/`curl`/`wget`）：
  不可配 `sh -c` entrypoint，也不可用 curl/wget healthcheck（否则容器起不来）。正确流程（各执行一次、幂等）：
  1. **建库**：postgres 空数据目录首次启动时，`/docker-entrypoint-initdb.d/init-openfga.sh` 自动 `CREATE DATABASE openfga;`
     （若库缺失可手动 `docker exec iam-postgres psql -U iam -c "CREATE DATABASE openfga;"`）；
  2. **迁移**：`docker compose -f deploy/docker-compose.yml run --rm openfga migrate`（手动，幂等，直接跑二进制）；
  3. **启动**：openfga 服务用默认 entrypoint 直接 `run`；iam-server 启动时自动 EnsureSchema（幂等）。
- **seed 与 PEP 映射**：`make seed` 末尾会自动对 cmdb 应用做 OpenAPI 同步（幂等），
  生成权限点 `method/path` + 板块模板，供网关 PEP（Traefik forwardAuth）做"请求→action"映射；
  数据卷重建后无需再手动同步，直接 `make seed` 即可。注意：**授权（策略）非 seed 全量覆盖**，
  bob 等演示用户的数据级只读、M2M 服务的接入授权需按 demo 场景单独配置（见脚本期望）。
- **后端镜像**：`make up` 内部宿主机交叉编译 `GOOS=linux GOARCH=arm64`（macOS 产物为 Mach-O，Linux 容器需 ELF）
  + `alpine` 最小运行时（daocloud 对 `docker.io/library/golang` 拉取缓慢，故本地预编译）。
- **前端镜像**：宿主机构建 dist + `nginx` 运行时（容器内 npm install 网络不稳定，lockfile 锁定 registry 容器内不可达）。
- **网关**：Traefik 镜像来自 `ghcr.io/traefik/traefik`（本机 Docker Hub 不可达、daocloud 镜像源对
  `apache/apisix` 返回 403，故选用 Traefik forwardAuth 等价替代 APISIX ext-authz，且无需 etcd）。
- **PEP→PDP 信任**：Traefik `pep-token` 中间件注入 `X-PEP-Token` 共享密钥，
  forwardAuth 需在 `authRequestHeaders` 中放行该头；直接调 PDP 接口同样需带 `X-PEP-Token`。

## 目录结构

```
backend/            Go 后端
  cmd/iam-server    中心 PDP + 管理 API + Sync（含 seed 子命令）
  cmd/iam-agent     本地 PDP agent（sidecar，内嵌 Casbin）
  cmd/mock-cmdb     模拟 CMDB 数据源（OpenAPI + 模型/实例 + 事件）
  cmd/mock-identity 模拟身份源（SCIM 风格）
  internal/api      HTTP 层（含网关回调 /v1/gateway/check）
  internal/authz    授权核心（Casbin + 策略模型层 + 数据面）
  internal/openfga  OpenFGA 客户端适配
  internal/bundle   策略分发
  internal/sync     同步连接器（OpenAPI/CMDB/Identity）
  internal/model    领域模型（GORM AutoMigrate 建表）
  internal/store    GORM/Redis 数据访问
  internal/auth     JWT + OAuth Client Credentials
  internal/governance 申请/审批/回收
frontend/           Vue3 管理控制台（原 web/）
deploy/             docker-compose + traefik/（file provider 动态路由）
scripts/            种子与演示脚本
```

## 设计文档

- 架构设计：`docs/architecture.md`
