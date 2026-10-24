# 权限中心（Permission Center / IAM Demo）

现代化权限中心 demo：**API 层面 + 数据层面**权限管控，下游经网关统一接入。

> 背景叙事（面试用）：真实工作中开发过一套权限中心，因强耦合 CMDB、数据膨胀、权限配置繁琐、未调研业界方案而难用；本 demo 按"重构后的现代化方案"实现。

## 核心架构

```
控制面（低 QPS，管理）       数据面（高 QPS，鉴权执行）
  PAP 管理控制台 (Vue3)  ──▶  iam-server (PDP)
  Sync Connector         ──▶    Casbin（动作级 RBAC/ABAC）
  iam-sync (仅 TTL 回收) ─▶    CheckRow（数据级：范围谓词×点查权威行）
   单活锁 + 逐轮 recover            Redis（策略/决策缓存）/ PostgreSQL（主存储）
下游接入 PEP：Traefik（forwardAuth → PDP） / mock-cmdb / mock-identity
```

关键设计：

- **PEP/PDP/PAP/PIP 外部化授权**，控制面/数据面分离，PDP 无状态可水平扩展
- **数据源解耦（1.5）**：判定材料=点查权威行（通用点查约定，行用完即丢）；CMDB 挂=数据级 fail-closed，动作级不受影响
- **授权引擎**：动作级 Casbin（RBAC/ABAC）+ 数据级自研 CheckRow（范围谓词×权威行，无投影无关系引擎）
- **策略即数据**：策略版本化（policy_versions）+ 回滚 + 审计；数据策略=范围谓词（条件/集合/全量）
- **策略分发**（借鉴 OPA bundle）：bundle 快照 + checksum + agent 本地动作级决策 + 状态上报
- **程序授权（M2M）**：OAuth2 Client Credentials，主体 service 与用户共用 PDP
- **开放自服务/弱管理员**：应用自注册 + owner 模型 + 权限市场 + 申请-审批-开通-回收（IGA）
- **身份同步**：mock-identity（SCIM 风格）+ Identity Connector + JML
- **数据契约与点查（1.5）**：数据级发布必填契约（判定字段清单=点查模型白名单）+ 门禁试算自检（按取材声明真取一次行）；观测端点 `/api/v1/sync/contracts`- **接入体检与凭证豁免（1.5 T4）**：应用注册/导入即体检（五类硬校验：缺动作/格式错/重复/配置自洽含裸豁免/导入一致性，报告回执 `GET /apps/:id/onboard-report`）；豁免主语=M2M 凭证非路由（`App.ExemptPaths`，网关凭证匹配才跳过，失配打 `[ALERT][gw403]` 告警）；动作码别名路由显式登记例外
- **预设参数联动+层级编排（1.5 T6）**：场景参数一次选定全域同值（`$key` 引用，shared 模式服务端钉子禁字面值=防域间错位）；`data_model_tree` 层级树（编排不是存储，落底各域独立策略）
- **多包一次性申请（1.5 T7）**：`capability_requests[]` ≥2 包一单一审批（同应用）→ 逐包表达式合并审批视图 → 批量开通一 item 一策略（capability_id 可指认）；共现推荐（`/marketplace/recommend`）
- **deny 治理（1.5 T8）**：deny-overrides（`allow && !deny` 一票否决）+ 治理三钉子（显式 action_ids 禁通配/reason 必填同链留痕/单应用配额 20）；deny≠删除授权——回收解除后 allow 自然恢复（冻结语义）；见 `docs/deny治理规范.md` 与 `docs/兜底接入规范.md`- **进程隔离**：`iam-sync` 仅存 TTL 到期回收循环（单活锁+逐轮 recover+status 守卫）；判定进程 iam-server 无后台循环、可独立多副本；健康探活容器内 `/healthz`；本地开发 `make run-sync`

## 快速开始（OrbStack 全栈部署，统一管理）

```bash
# 1. 构建镜像并启动全栈（基础设施 + iam-server/iam-sync/mock-cmdb/mock-identity/iam-agent/frontend）
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
# 服务器（无 OrbStack 域名）用宿主机端口覆盖：
IAM_DEMO=http://localhost:18080 GW_DEMO=http://localhost:19080 bash scripts/demo.sh
```

覆盖（22 场景）：动作级鉴权 → 无权限拦截 → 数据级点查（条件授权+谓词拒+带体信封两连判）→ 程序身份(M2M) →
网关 PEP 链路（Traefik forwardAuth，allow/deny）→ 动作级不依赖上游 → 策略发布即时生效
（决策缓存失效）→ 本地 agent 决策 → **点查链路三件套（回查配置/契约白名单/取材声明）→
行删除 DATA_MISSING → 点查源不可用 fail-closed+恢复复通** → 定制需求卡 TTL 回收。

### 数据契约配置（1.5：登记面）

| 配置 | 说明 |
|------|------|
| `data_contracts.fields` | 判定字段清单 = 点查模型白名单（seed 自动登记 host/database/disk/public_resource） |
| 应用回查配置 | `PUT /api/v1/apps/:id/perm-query`（回查地址=系统内部地址 + M2M 凭证；demo 场景 4 自动配置） |

> 点查取材/fail-closed 三态与发布门禁的完整语义见 `docs/architecture.md` §5.4 与 §7.6。

### 数据管理与备份恢复（Seed / Backup / Restore）

**数据位置**：业务数据在 Docker 命名卷 `permission-center_pgdata`（PostgreSQL，含 IAM）、
`permission-center_redisdata`（Redis），**不在容器内**。⚠️ 严禁 `docker compose down -v`
（`-v` 会删除命名卷导致数据直接丢失）。

**两条数据防线（推荐分工）**：

1. **Seed 初始化脚本（主）**：演示基准数据（应用 / 权限点 / 数据模型 / 能力包 / 授权）由
   `backend/cmd/iam-server/seed.go` 定义，版本化、幂等、可一键重建，随代码演进。
2. **数据库备份（补充）**：保留 seed 不覆盖的运行时痕迹——审批单（审批人/评论/流转）、
   审计日志、决策日志、token 等；适合还原某个演示现场或历史操作状态。

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

- **OpenFGA（已退役，1.5）**：数据级判定不再依赖关系引擎——compose 中 openfga 服务、`OPENFGA_ADDR` 等环境变量已移除；`devops_openfga` 库留存无引用（可手工清理）。
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
  cmd/iam-server    中心 PDP + 管理 API（含 seed 子命令）
  cmd/iam-sync      同步独立进程（仅 TTL 到期回收 + healthz）
  cmd/iam-agent     本地 PDP agent（sidecar，内嵌 Casbin）
  cmd/mock-cmdb     模拟 CMDB 数据源（OpenAPI + 模型/实例 + 事件）
  cmd/mock-identity 模拟身份源（SCIM 风格）
  internal/api      HTTP 层（含网关回调 /v1/gateway/check）
  internal/authz    授权核心（Casbin + 策略模型层 + 数据面）
  internal/material 通用点查取材（点查客户端/信封与路径提取/回源绑定）
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
