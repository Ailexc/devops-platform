# 权限中心（IAM）项目实施计划

> 版本：v0.1（待评审）
> 日期：2026-08-03
> 前置文档：`docs/architecture.md`（架构设计）
> 本文档定位：**可指导实施的项目级计划**——包含数据模型、接口设计、关键流程、分阶段任务清单、验收标准、工作量估算与开放决策点。

---

## 0. 文档说明

### 0.1 目的

- 将架构设计（`docs/architecture.md`）细化为**可直接照着做的实施计划**；
- 每个阶段都有：目标 → 任务清单（可勾选）→ 验收标准 → 工作量估算 → 面试叙事点；
- 明确列出需要你**拍板的决策点**（见 §12），读完本文档后逐条确认即可开工。

### 0.2 如何使用

1. 先通读 §1–§11 了解全貌；
2. 重点阅读 §12「决策点清单」，逐条给出选择（可直接在文档里批注）；
3. 确认后按 §9 的 P0→P6 顺序实施，每阶段结束用「验收标准」自检；
4. §14 是面试叙事素材对照表，随实施进度持续填充。

---

## 1. 项目概述

### 1.1 一句话背景

真实工作中开发过一套权限中心，因**强耦合 CMDB、数据膨胀、权限配置繁琐、未调研业界方案**而难用；本 demo 按"重构后的现代化方案"实现，用于回忆知识点与面试展示。

### 1.2 目标

- API 层面权限管控：OpenAPI → 权限模板（板块式）→ 角色/组/用户授权；
- 数据层面权限管控：CMDB 数据模型 + 实例级勾选授权（check / filter）；
- 下游经 APISIX 网关统一接入鉴权；
- 体现现代实践：外部化授权（PEP/PDP/PAP/PIP）、控制面/数据面分离、数据源解耦与降级、策略即数据、策略分发与本地决策、审计与可观测。

### 1.3 非目标

- 不做完整 IDaaS（无 OAuth2/OIDC/SAML 联邦，仅轻量 JWT 登录）；
- 不做多租户（单租户，模型预留 tenant_id 字段）；
- 不实现真实 CMDB（用内置 mock-cmdb 模拟）。

### 1.4 关键术语

| 术语 | 说明 |
|------|------|
| 权限点 Action | 规范化权限标识 `{app}:{resource}:{operation}`，如 `cmdb:host:create` |
| 权限模板 Template | 由 OpenAPI 按资源/板块生成的权限点分组 |
| 资源索引 Resource Index | 从 CMDB 同步到 IAM 本地的权限判断投影（非全量业务数据） |
| Bundle | 策略快照包（模型+策略+元数据+版本），下发给本地 agent |
| PEP/PDP/PAP/PIP | 执行点/决策点/管理点/信息点（XACML 外部化授权） |

---

## 2. 总体架构（回顾）

```
┌─────────────────────────────────────────────────────────────┐
│ 控制面 Control Plane（低 QPS，管理操作）                        │
│  PAP 管理控制台 (Vue3+Element Plus)                           │
│  Sync Service（OpenAPI Connector / CMDB Connector）           │
├─────────────────────────────────────────────────────────────┤
│ 数据面 Data Plane（高 QPS，无状态可水平扩展）                    │
│  中心 PDP (iam-server)：Casbin + 自研策略模型层                 │
│  本地 PDP agent (iam-agent, sidecar)：内嵌 Casbin，本地决策     │
│  Redis（策略缓存/决策缓存/资源热索引） / PostgreSQL（主存储）      │
├─────────────────────────────────────────────────────────────┤
│ 下游接入 PEP                                                    │
│  APISIX（ext-authz → 中心 PDP / 本机 agent）                   │
│  mock-cmdb（模拟数据源：OpenAPI + 模型 + 实例 + 事件）            │
└─────────────────────────────────────────────────────────────┘
```

**组件清单**：

| 组件 | 角色 | 说明 |
|------|------|------|
| iam-server | 中心 PDP + PAP API + Sync | 控制面+数据面主体服务 |
| iam-agent | 本地 PDP（sidecar） | 内嵌 Casbin，动作级 bundle 本地决策（P6） |
| OpenFGA | 实例级关系引擎 | Check/ListObjects，自有 datastore（P4 引入） |
| mock-cmdb | 外部数据源模拟 | OpenAPI 文档 + 模型/实例 CRUD + 变更事件 webhook |
| mock-identity | 身份源模拟 | 用户/组织（SCIM 风格 API + 变更事件），演示身份同步与 JML |
| APISIX | PEP 网关 | ext-authz 插件对接 PDP |
| web | 管理控制台 | Vue3 + Element Plus |

---

## 3. 技术选型明细

| 组件 | 选型 | 版本（建议） | 用途 | 替代方案 |
|------|------|------|------|----------|
| 语言 | Go | 1.24+ | 后端主语言 | - |
| Web 框架 | Gin | v1.10+ | HTTP 路由/中间件 | chi（更轻）、echo |
| 授权引擎（动作级） | Casbin | v2.x | RBAC/ABAC 核心引擎 | OPA/自研（已评估） |
| 授权引擎（实例级） | OpenFGA | 1.x | 数据级 ReBAC：Check / ListObjects | SpiceDB（性能更强）、自研 |
| ORM/数据库访问 | GORM | v1.25+ | 全 ORM 开发，不手写 SQL | pgx+手写 SQL（性能）、sqlc（类型安全） |
| 建表/迁移 | GORM AutoMigrate | 随 GORM | 由 Model struct 自动建表，零手写 SQL | goose（需 SQL 迁移文件） |
| 主存储 | PostgreSQL | 16+ | 全部业务数据 | - |
| 缓存 | Redis | 7.x | 策略缓存/决策缓存/热索引 | - |
| 网关 | APISIX | 3.x (docker) | PEP 执行点 | Kong、Traefik |
| 前端 | Vue3 + Vite + TS + Pinia + Element Plus | 最新稳定 | 管理控制台 | React + AntD |
| 认证 | JWT (access+refresh) | 自研轻量 | 管理台与 API 鉴权 | 完整 OIDC（非目标） |
| 程序授权 (M2M) | OAuth 2.0 Client Credentials | 自研轻量 | 下游应用身份：client_id+secret → access token | 完整 OIDC（非目标） |
| 审批流 | 自研轻量状态机 | 薄 | 申请-审批-开通-回收闭环 | Flowable/Temporal（重） |
| 身份同步 | SCIM 2.0 风格（自研轻量） | 从身份源同步用户/组织 + 事件 | 完整 SCIM 服务（重） |
| 部署 | Docker Compose | - | 本地一键起 pg/redis/apisix | k8s（过度） |

### 3.1 关键选型说明

- **Casbin + OpenFGA 双引擎**：动作级（Casbin：RBAC/ABAC）与实例级（OpenFGA：关系引擎）职责分离、互不重叠。自研层承担策略管理、资源范围翻译、版本化、审计、bundle——把数据策略翻译为 OpenFGA 授权模型与关系。
- **OpenFGA 选型叙事**：与 SpiceDB 对比，OpenFGA 是 CNCF 项目、原生支持授权模型版本化（与自研策略版本化对齐），故选之；SpiceDB 适合超大规模极致性能场景。
- **版本化/审计组件化**：策略快照/业务审计自写（很薄）；模型版本与关系变更白嫖 OpenFGA；事件异步用 Redis Streams（与 CMDB webhook 两用）；进阶 GitOps 策略仓库。
- **申请/审批轻量状态机**：评估过重型工作流引擎（Flowable/Temporal），demo 自建薄状态机足够；复杂多分支流程可演进到 Temporal/Flowable。
- **身份同步（SCIM 风格）**：用户/组织来自 mock-identity 身份源，IAM 同步副本、不手工建主数据；组织组只读、自建组 IAM 管理；JML 演示见 P6。
- **GORM**：全程 ORM 开发，不手写 SQL。理由：① 权限系统的查询以关系模型 CRUD 为主，GORM 的 Model/预加载/事务/钩子完全够用；② 规避面试中"手写 SQL"被连环追问的风险。
- **面试话术建议**：不要强调"不写 SQL"，改为主动表述——"权限中心的查询以结构化 CRUD 为主，我选用 GORM 提升迭代效率、用事务与钩子保证策略变更一致性；复杂统计靠索引与预加载即可满足"。
- **APISIX 用 docker 部署**：本地 demo 无需安装，`docker compose up` 即可。

---

## 4. 详细数据模型

> 全部表位于 PostgreSQL，主键统一 BIGSERIAL；时间字段统一 `TIMESTAMPTZ`；软删除统一 `deleted_at`（可空）。

### 4.1 表结构

#### users（用户）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| username | VARCHAR(64) | UNIQUE NOT NULL | 登录名 |
| display_name | VARCHAR(128) | | 显示名 |
| email | VARCHAR(128) | UNIQUE | |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt |
| status | SMALLINT | NOT NULL DEFAULT 1 | 1=启用 0=停用 |
| attributes | JSONB | DEFAULT '{}' | ABAC 属性（部门/级别等） |
| source | SMALLINT | NOT NULL DEFAULT 2 | 1=identity 同步(只读) 2=manual 手工 |
| token_version | INT | NOT NULL DEFAULT 1 | 停用/改密时 +1，旧 token 即时失效 |
| created_at / updated_at | TIMESTAMPTZ | | |

#### groups（组织架构树 + 自建组）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| name | VARCHAR(128) | NOT NULL | |
| parent_id | BIGINT | FK→groups.id | 树父节点 |
| type | SMALLINT | NOT NULL | 1=org 组织架构 2=custom 自建组 |
| path | VARCHAR(255) | 索引 | 物化路径（如 `/1/2/3/`），应用层维护 |
| source | SMALLINT | DEFAULT 2 | 1=identity 同步(只读) 2=manual |
| created_at / updated_at | TIMESTAMPTZ | | |

> 物化路径由**应用层维护**（GORM 内完成，增删节点时更新），子树查询用 `path LIKE 'prefix%'`（GORM 生成），不依赖数据库扩展、不写裸 SQL。

#### user_group（用户-组）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| user_id | BIGINT | FK NOT NULL | |
| group_id | BIGINT | FK NOT NULL | |
| role | SMALLINT | NOT NULL DEFAULT 1 | 1=member 2=admin |
| UNIQUE(user_id, group_id) | | | |

#### apps（应用）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| code | VARCHAR(64) | UNIQUE NOT NULL | 如 `cmdb`、`order` |
| name | VARCHAR(128) | NOT NULL | |
| type | SMALLINT | NOT NULL | 1=api 2=data(cmbd) |
| openapi_url | VARCHAR(512) | | OpenAPI 文档地址 |
| status | SMALLINT | DEFAULT 1 | |
| owner_id | BIGINT | FK→users | 应用所有者（注册者） |
| owner_group_id | BIGINT | FK→groups 可空 | 组织兜底锚点 |
| created_at / updated_at | TIMESTAMPTZ | | |

#### clients（程序身份，M2M）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| app_id | BIGINT | FK NOT NULL | 归属应用 |
| client_id | VARCHAR(64) | UNIQUE NOT NULL | 应用凭证 ID |
| client_secret_hash | VARCHAR(255) | NOT NULL | 应用凭证密钥（哈希存储） |
| status | SMALLINT | DEFAULT 1 | 1=启用 0=停用 |
| created_at / updated_at | TIMESTAMPTZ | | |

#### app_owners（应用负责人）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| app_id | BIGINT | FK NOT NULL | |
| user_id | BIGINT | FK NOT NULL | 负责人（≥2 个，失联时组织树向上兜底） |
| is_primary | BOOLEAN | DEFAULT true | 主负责人 |
| UNIQUE(app_id, user_id) | | | |

#### actions（权限点）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| app_id | BIGINT | FK NOT NULL | |
| code | VARCHAR(128) | UNIQUE(app_id,code) | `cmdb:host:create` |
| name | VARCHAR(128) | | 展示名"创建主机" |
| resource | VARCHAR(128) | | 资源 `host` |
| operation | VARCHAR(32) | | create/read/update/delete |
| method | VARCHAR(16) | | HTTP 方法 |
| path | VARCHAR(256) | | API 路径 |

#### permission_templates（权限板块）+ template_actions
| 表 | 字段 | 说明 |
|----|------|------|
| permission_templates | id, app_id FK, name, sort | 板块，如"主机管理" |
| template_actions | template_id FK, action_id FK, PK(template_id,action_id) | 板块→权限点 |

#### roles（角色）+ role_actions
| 表 | 字段 | 说明 |
|----|------|------|
| roles | id, app_id FK(可空=全局), name, code UNIQUE, description, is_system | |
| role_actions | role_id FK, action_id FK, PK(role_id,action_id) | |

#### policies（统一策略表：API + 数据）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | |
| name | VARCHAR(128) | NOT NULL | |
| version | INT | DEFAULT 1 | 版本号 |
| effect | SMALLINT | NOT NULL | 1=allow 2=deny |
| subject_type | SMALLINT | NOT NULL | 1=user 2=group 3=role 4=service |
| subject_id | BIGINT | NOT NULL | 主体 ID |
| app_id | BIGINT | FK NOT NULL | |
| action_ids | JSONB | NOT NULL | 权限点 ID 数组（[]=全部） |
| resource_scope | JSONB | | 数据策略范围（见下） |
| conditions | JSONB | DEFAULT '{}' | ABAC 条件 |
| force_remote | BOOLEAN | DEFAULT false | 风险分级：强制回源 |
| status | SMALLINT | DEFAULT 1 | 1=active 0=disabled |
| created_by | BIGINT | | |
| created_at / updated_at | TIMESTAMPTZ | | |

> `resource_scope` 三种表达（JSONB）：
> ```json
> // 集合式：勾选实例
> {"model_id": 1, "instance_ids": [101, 102]}
> // 关系式（ReBAC）
> {"model_id": 1, "relation": "owner", "value": "current_user"}
> // 属性式（ABAC）
> {"model_id": 1, "condition": {"field": "status", "op": "eq", "value": "active"}}
> ```

#### policy_versions（策略历史）
| 字段 | 说明 |
|------|------|
| id, policy_id FK, version, content JSONB（快照）, changed_by, reason, created_at | 支持回滚与审计 |

#### access_requests / approval_tasks（申请与审批）
| 表 | 字段 | 说明 |
|----|------|------|
| access_requests | id, applicant_id, app_id, content JSONB（角色/权限点/数据范围）, risk_level(1低/2中/3高), status(0草稿 1审批中 2通过 3拒绝 4已回收), expires_at（可空=JIT）, created_at | 自助申请 |
| approval_tasks | id, request_id, step, approver_id, action(1通过 2驳回), comment, created_at | 多级审批节点 |

> 开通动作复用策略发布链路；到期回收由定时任务扫描 expires_at。

#### resource_models / resource_instances（资源索引投影）
| 表 | 字段 | 说明 |
|----|------|------|
| resource_models | id, source_id UNIQUE(CMDB 侧), name, code UNIQUE, attributes_schema JSONB, synced_at | 模型=表概念 |
| resource_instances | id, model_id FK, external_id, name, attributes JSONB（投影）, owner_id（可空，关系锚点）, synced_at, UNIQUE(model_id,external_id) | 只存权限判断所需字段 |

#### sync_jobs（同步任务）
| 字段 | 说明 |
|------|------|
| id, type(1=openapi 2=cmdb-model 3=cmdb-instance 4=identity), status, started_at, finished_at, result JSONB | 同步进度与统计 |

#### bundles（策略分发版本）
| 字段 | 说明 |
|------|------|
| id, app_id, revision BIGINT, content JSONB, checksum VARCHAR(64), published_by, created_at, UNIQUE(app_id,revision) | 全量策略快照 |

#### agent_status（agent 上报）
| 字段 | 说明 |
|------|------|
| id, agent_id UNIQUE, app_id, current_revision, last_seen_at, decision_count, hit_rate | 升级率/存活监控 |

#### audit_logs / decision_logs（审计与决策日志）
| 表 | 关键字段 | 说明 |
|----|------|------|
| audit_logs | actor_id, action, resource_type, resource_id, detail JSONB, ip, created_at | 管理操作审计，**按月分区** |
| decision_logs | user_id, app_id, action, resource, decision(1=allow 2=deny), reason, channel(1=remote 2=local), latency_ms, context JSONB, created_at | 鉴权决策，**按月分区** |

### 4.2 ER 概览

```mermaid
erDiagram
    USERS ||--o{ USER_GROUP : ""
    GROUPS ||--o{ USER_GROUP : ""
    GROUPS ||--o{ GROUPS : "parent"
    APPS ||--o{ ACTIONS : ""
    APPS ||--o{ PERMISSION_TEMPLATES : ""
    PERMISSION_TEMPLATES ||--o{ TEMPLATE_ACTIONS : ""
    ACTIONS ||--o{ TEMPLATE_ACTIONS : ""
    APPS ||--o{ ROLES : ""
    ROLES ||--o{ ROLE_ACTIONS : ""
    ACTIONS ||--o{ ROLE_ACTIONS : ""
    APPS ||--o{ POLICIES : ""
    POLICIES ||--o{ POLICY_VERSIONS : ""
    USERS ||--o{ POLICIES : "subject(user)"
    GROUPS ||--o{ POLICIES : "subject(group)"
    ROLES ||--o{ POLICIES : "subject(role)"
    RESOURCE_MODELS ||--o{ RESOURCE_INSTANCES : ""
```

---

## 5. 模块划分与职责

| 包（internal/） | 职责 | 关键文件（示例） |
|-----------------|------|------------------|
| api | HTTP handler：管理 API + 鉴权 API | `api/router.go`, `api/handler_user.go`, `api/handler_authz.go` |
| authz | 授权核心：Casbin enforcer 封装 + 策略模型层（scope 翻译/check/filter） | `authz/enforcer.go`, `authz/checker.go`, `authz/policy_builder.go` |
| openfga | OpenFGA 客户端适配：授权模型/关系写入、Check/ListObjects 封装 | `openfga/client.go`, `openfga/mapper.go` |
| bundle | bundle 生成/校验/拉取 API | `bundle/builder.go`, `bundle/handler.go` |
| sync | 同步连接器：openapi / cmdb | `sync/openapi_parser.go`, `sync/cmdb_connector.go`, `sync/runner.go` |
| model | 领域模型与枚举 | `model/user.go`, `model/policy.go` |
| store | 数据访问（GORM）/ Redis | `store/user_repo.go`, `store/policy_repo.go`, `store/cache.go` |
| audit | 审计与决策日志写入 | `audit/writer.go` |
| auth | JWT + OAuth Client Credentials（程序身份签发） | `auth/jwt.go`, `auth/oauth.go`, `auth/middleware.go` |
| governance | 申请/审批/开通/到期回收（自研轻量状态机） | `governance/request.go`, `governance/approval.go` |

---

## 6. 详细目录结构

```
permission_center/
├── docs/architecture.md          # 架构设计（已存在）
├── plans/implementation-plan.md  # 本文档
├── cmd/
│   ├── iam-server/main.go        # 中心 PDP + 管理 API 入口
│   ├── iam-agent/main.go         # 本地 PDP agent 入口（P6）
│   ├── mock-cmdb/main.go         # mock 数据源入口（P2）
│   └── mock-identity/main.go     # mock 身份源入口（P4，SCIM 风格）
├── internal/
│   ├── api/                      # HTTP 层
│   ├── authz/                    # 授权核心
│   ├── openfga/                  # OpenFGA 客户端适配（P4）
│   ├── bundle/                   # 策略分发（P6）
│   ├── sync/                     # 同步连接器
│   ├── model/                    # 领域模型
│   ├── store/                    # GORM/Redis 数据访问
│   ├── auth/                     # JWT
│   ├── governance/               # 申请/审批/回收（P5）
│   └── audit/                    # 审计日志
├── web/                          # Vue3 管理控制台（P5）
├── deploy/
│   ├── docker-compose.yml        # postgres/redis/openfga/apisix
│   ├── apisix/                   # apisix config + 路由
│   └── .env.example
├── scripts/
│   ├── seed/                    # Go 种子数据程序（不写 SQL）
│   └── demo.sh                   # 一键演示脚本（P6）
├── Makefile
├── go.mod
└── README.md
```

---

## 7. 接口设计草案

### 7.1 管理 API（`/api/v1`，JWT 保护）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 登录，返回 access+refresh |
| GET/POST | /users | 用户列表/创建 |
| PATCH | /users/:id | 更新用户（含状态） |
| GET/POST | /groups | 组织/组树、创建 |
| PATCH | /groups/:id | 改节点 |
| POST | /groups/:id/members | 组内加成员 |
| GET/POST | /apps | 应用列表/注册 |
| POST | /apps/register | 应用注册申请（demo 简化自审批；真实走工单+网络打通） |
| POST | /apps/:id/owners | 应用负责人管理（≥2） |
| GET/POST | /apps/:id/clients | 程序身份管理（client_id/secret） |
| POST | /apps/:id/clients/:cid/rotate | 轮换 secret |
| POST | /apps/:id/grants | 出方向：为自家应用申请访问其他应用 |
| GET | /apps/:id/inbound | 入方向：自家应用暴露的权限点与待批申请 |
| POST | /apps/:id/sync | 触发 OpenAPI 同步 |
| GET | /apps/:id/actions | 权限点树（按板块） |
| GET/POST | /apps/:id/templates | 模板管理 |
| GET/POST | /roles | 角色管理 |
| POST | /roles/:id/actions | 角色挂权限点 |
| GET/POST | /policies | 策略列表/创建（API+数据） |
| PATCH | /policies/:id | 编辑策略 |
| POST | /policies/:id/publish | 发布（version++，生成 bundle） |
| POST | /requests | 提交权限申请（自助/业务系统对接） |
| GET | /requests | 我的申请 / 待我审批列表 |
| POST | /requests/:id/approve | 审批（通过/驳回，按风险走多级） |
| GET | /policies/:id/versions | 历史版本 |
| GET | /resource-models | 数据模型列表（来自索引） |
| GET | /resource-models/:id/instances | 模型实例列表 |
| POST | /sync/cmdb | 手动触发 CMDB 同步 |
| POST | /sync/identity | 手动触发身份源同步 |
| GET | /audit-logs | 审计查询 |

### 7.2 鉴权 API（`/v1/authz`，供网关/下游）

**token（程序身份签发，M2M）**
```http
POST /v1/oauth/token
{
  "grant_type": "client_credentials",
  "client_id": "cloud-mgmt",
  "client_secret": "..."
}
→ 200 {"access_token":"eyJ...","token_type":"Bearer","expires_in":3600}
```

**check（API 鉴权）**
```http
POST /v1/authz/check
{
  "user": "alice",
  "app": "cmdb",
  "action": "cmdb:host:create",
  "resource": null,
  "context": {"ip": "10.0.0.1", "time": "2026-08-03T10:00:00Z"}
}
→ 200 {"decision":"allow"}  /  403 {"decision":"deny","code":"NO_PERMISSION","message":"..."}
```

**check-instance（数据点操作）**
```http
POST /v1/authz/check-instance
{
  "user": "alice",
  "action": "cmdb:host:update",
  "instance_id": "host-101"
}
```

**filter（数据列表）**
```http
POST /v1/authz/filter
{
  "user": "alice",
  "model": "host",
  "action": "cmdb:host:read",
  "query": {"page":1,"size":20}
}
→ 200 {"instance_ids":["host-101","host-102"], "total": 2, "scope_condition": "..."}
```

> `filter` 由 OpenFGA `ListObjects` 实现，返回显式实例 ID 列表；可拼入下游查询的条件片段（`owner_id = 'alice' OR group_id IN (...)`）列为加分项。

### 7.3 Bundle API（P6）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /v1/bundles/:app?rev=N | agent 拉取（带当前版本，无更新返回 304） |
| POST | /v1/agents/status | agent 状态上报 |

---

## 8. 关键流程详细设计

### 8.1 API 鉴权流程（远程，P3 交付）

```mermaid
sequenceDiagram
    participant C as 前端/下游
    participant G as APISIX
    participant P as iam-server (PDP)
    participant R as Redis
    participant PG as PostgreSQL
    C->>G: 请求(带 user 信息)
    G->>P: ext-authz POST /v1/authz/check
    P->>R: 决策缓存查 (user+app+action+resource)
    alt 缓存命中
        P-->>G: 200 allow / 403 deny
    else 未命中
        P->>PG: 加载用户→组/角色→策略(版本缓存)
        P->>P: Casbin 求值 + conditions 校验
        P->>R: 写决策缓存(TTL)
        P-->>G: 结果
    end
    G-->>C: 放行 / 拦截+错误
```

### 8.2 数据鉴权流程（P4 交付）

```mermaid
sequenceDiagram
    participant D as 下游(CMDB等)
    participant P as iam-server (PDP)
    participant C as Casbin(动作级)
    participant O as OpenFGA(实例级)
    D->>P: check-instance / filter
    P->>C: 动作级判断(有该 API 权限?)
    alt 无动作权限
        P-->>D: deny（短路，不查 OpenFGA）
    else 有动作权限
        P->>O: Check(实例) / ListObjects(列表)
        O-->>P: allow/deny 或 允许实例集
        P-->>D: 结果
    end
```

### 8.3 OpenAPI 同步流程（P2 交付）

```mermaid
flowchart LR
    A[注册 app + openapi_url] --> B[触发同步]
    B --> C[拉取 OpenAPI 文档]
    C --> D[解析 paths → actions 规范化]
    D --> E[按 tag/资源分组 → 生成模板]
    E --> F[写 sync_jobs 记录]
```

### 8.4 CMDB 数据同步流程（P4 交付）

```mermaid
flowchart LR
    A[mock-cmdb 模型/实例] -- 全量+增量拉取 --> B[CMDB Connector]
    B --> C[写 resource_models/instances 索引]
    A -- 变更事件 webhook --> D[IAM 事件入口]
    D --> C
    C --> E[更新 synced_at 水位 + 告警阈值]
    C -- 实例变更 --> F[同步关系到 OpenFGA(Write)]
```

**降级演示**：停掉 mock-cmdb → IAM 仍可用最后同步索引鉴权；重新启动后增量追平。

### 8.5 策略发布 / bundle 分发流程（P6 交付）

```mermaid
flowchart LR
    A[编辑策略] --> B[publish: version++]
    B --> C[API 策略 → 生成 bundle]
    C --> D[agent 轮询 /v1/bundles/:app?rev]
    D --> E[校验 checksum → 原子激活]
    E --> F[agent 本地动作级决策 + 状态上报]
    E -- 校验失败 --> G[保留 last-known-good]
    B --> H[数据策略 → OpenFGA 授权模型/关系(Write)]
    H --> I[实例级 Check/ListObjects 生效]
```

### 8.6 降级矩阵

| 场景 | 行为 | 语义 |
|------|------|------|
| CMDB 不可用 | 用最后同步索引 | 数据源降级（stale-but-available） |
| agent 拉包失败/过期 | fail-closed 拒绝，可配置回源中心 | 下发降级 |
| 高风险写（force_remote） | 强制回源中心 | 一致性保证 |
| Redis 不可用 | 直查 PG（跳过缓存） | 缓存降级 |
| OpenFGA 不可用 | 数据级请求 fail-closed（或降级为索引兜底） | 关系引擎降级 |

### 8.7 程序授权流程（M2M，P3 起）

```mermaid
sequenceDiagram
    participant S as 下游服务(云管/工单/事件)
    participant T as IAM /v1/oauth/token
    participant G as APISIX
    participant P as PDP
    S->>T: client_id + client_secret
    T-->>S: access token(JWT, sub=client:xxx, scope)
    S->>G: 请求 + token
    G->>P: 校验 token + check(subject=service)
    alt 工单审批后写操作
        S->>T: 持审批受限令牌(scoped+TTL)
        T-->>S: 受限 token
        S->>G: 写请求 + 受限 token
        G->>P: 校验 scope/时效 → 放行
    end
    P-->>G: allow/deny
    G-->>S: 放行 / 拦截
```

### 8.8 身份源同步流程（SCIM 风格 + JML）

```mermaid
flowchart LR
    A[mock-identity 用户/组织] -- 全量+增量拉取 --> B[Identity Connector]
    B --> C[写 users/groups(org) 投影 source=identity]
    A -- 变更事件 webhook --> D[IAM 事件入口]
    D --> C
    C --> E[入职→加入部门→自动得角色 / 调岗→跟随 / 离职→停用回收]
    E --> F[JML 演示（P6）]
```

### 8.9 应用注册与权限市场（开放自服务）

```mermaid
flowchart LR
    A[用户提交应用注册(OpenAPI)] --> B[demo 简化自审批 / 真实走工单+网络打通]
    B --> C[成为 owner + 绑定≥2 负责人]
    C --> D[OpenAPI 同步生成权限点 入方向暴露]
    D --> E[他人申请访问 → owner 审批]
    D --> F[owner 为自家应用申请访问他人资源 出方向]
    E --> G[审批通过 → 策略发布 自动生效]
    F --> G
```

---

## 9. 分阶段实施计划

> 每阶段：目标 → 任务清单 → 验收标准 → 工作量 → 面试叙事点。
> 工作量按"人日"（1 人全职）估算，仅供参考。

### P0 — 项目骨架（0.5 天）

**目标**：可运行的最小骨架 + 基础设施就绪。

任务：
- [ ] `go mod init`（模块名见 D1）
- [ ] `cmd/iam-server/main.go`：Gin 启动 + `/healthz`
- [ ] 配置加载（env + yaml，`deploy/.env.example`）
- [ ] `deploy/docker-compose.yml`：postgres/redis/openfga/apisix 四件套
- [ ] GORM 接入（含 AutoMigrate 初始化）
- [ ] Makefile：`make up / down / run / build`（建表随启动 AutoMigrate 自动完成）
- [ ] README 初始化

**验收**：`make up && make run` 后 `curl localhost:8080/healthz` 返回 200；启动时 AutoMigrate 自动建表成功。

**面试叙事**：无（基础设施）。

### P1 — 基础域（2 天）

**目标**：用户/组织/组/应用 + 登录认证。

任务：
- [ ] GORM Model 定义（users/groups/user_group/apps，含 source 标记）+ AutoMigrate 建表
- [ ] users CRUD + bcrypt 密码
- [ ] JWT 登录（access 15min / refresh 7d）+ **token_version**（停用/改密即时失效旧 token）
- [ ] 管理面角色模型（user/owner/审计管理员只读）雏形 + 管理 API 按角色鉴权
- [ ] groups 树 CRUD（应用层维护 path 物化路径，子树用 LIKE 前缀查询）+ user_group 成员管理
- [ ] apps CRUD
- [ ] 种子数据（Go 程序写入）：admin 用户、示例组织树、cmdb 应用
- [ ] 鉴权中间件 + 管理 API 保护

**验收**：能登录拿 token；能建用户/组织/应用；组织树能查子树成员。

**面试叙事**：组织架构树用物化路径（应用层维护）替代递归查询——"权限系统组织树高并发查询的优化"。

### P2 — OpenAPI → 权限模板（2 天）

**目标**：mock-cmdb 提供 OpenAPI，IAM 自动生成权限点 + 板块模板。

任务：
- [ ] `cmd/mock-cmdb`：模型种子 + `/openapi.json`（OpenAPI 3 格式，覆盖 host/network/disk 三个资源板块）
- [ ] OpenAPI 解析器：paths → 规范化 action（method+path+tag → `cmdb:host:create` 等）
- [ ] 模板生成：按 tag 分组 → permission_templates + template_actions（**新增权限点默认不授权，deny-by-default**）
- [ ] 同步任务表 sync_jobs + 同步状态查询
- [ ] 管理 API：actions 树 + 模板查询

**验收**：注册 cmdb app → 触发同步 → 管理 API 返回 3 个板块、约 12 个权限点（host/network/disk × CRUD）。

**面试叙事**："从 OpenAPI 自动生成权限模板，避免手工维护权限点"——这是旧系统的亮点保留并规范化。

### P3 — API 鉴权 + APISIX 集成（3 天）

**目标**：RBAC + 策略引擎 + PDP 接口 + 网关链路全通。

任务：
- [ ] Casbin model 设计（RBAC + domain + ABAC conditions）
- [ ] `authz/policy_builder.go`：从 users/groups/roles/policies 构建 Casbin policy
- [ ] `authz/enforcer.go`：enforcer 封装 + 策略加载缓存（Redis）
- [ ] `/v1/authz/check` 接口 + 决策缓存（TTL）
- [ ] APISIX 配置：路由 + ext-authz 插件指向 iam-server
- [ ] 角色/策略管理 API（roles、policies CRUD + publish）
- [ ] 程序身份：clients 表 + POST /v1/oauth/token（Client Credentials）
- [ ] check 支持 service subject（PDP 按 sub 类型分流）
- [ ] 应用注册自服务：apps.owner_id + app_owners(≥2) + demo 简化注册审批（真实走工单+网络打通，注释说明）
- [ ] PEP→PDP 信任：共享密钥校验（防绕过网关直连 PDP）+ 请求→action 映射（method+path→actions 表）
- [ ] e2e：mock-cmdb 一个受保护接口走 APISIX 验证放行/拦截；云管用 service token 只读放行、写被拦截

**验收**：
- 有权限：`curl` 走 APISIX 带合法用户 → 200 放行；
- 无权限：→ 403 + 错误码；
- 角色变更后决策缓存 TTL 内生效；
- 程序身份：云管 service token 只读放行、写操作 403；事件系统 CRUD 放行。

**面试叙事**：PEP/PDP 分离、外部化授权、策略即数据（版本化）、决策缓存。

### P4 — 数据鉴权 + 同步 + 降级（3 天）

**目标**：CMDB 数据同步进本地索引，实现实例级 check/filter，并演示降级。

任务：
- [ ] docker-compose 增加 OpenFGA 服务 + 自有 datastore
- [ ] mock-cmdb：模型/实例 CRUD API + 变更 webhook
- [ ] CMDB Connector：全量拉取 + 增量（按 synced_at）+ 事件入口
- [ ] mock-identity：用户/组织 SCIM 风格 API + 变更事件
- [ ] Identity Connector：同步 users/groups(org)（source=identity，只读）
- [ ] 资源索引表 resource_models/instances + 投影字段裁剪
- [ ] OpenFGA 授权模型设计（user/group/service/host 等 type + relation）＋ `openfga/mapper.go`：数据策略 scope → OpenFGA 关系（Write）
- [ ] 数据级程序授权：为 service 建立 OpenFGA 关系（如 cloud-mgmt reader on host）
- [ ] 数据策略管理：resource_scope 三种表达（集合/关系/条件）
- [ ] `authz/checker.go`：check-instance（Casbin 动作 + OpenFGA Check）+ filter（OpenFGA ListObjects）
- [ ] 降级：停 mock-cmdb 后 IAM 仍可鉴权；恢复后增量追平 + 关系补写
- [ ] 孤儿清理：删除用户/组/实例时级联清理策略引用 + OpenFGA tuple（防关系图膨胀）
- [ ] 同步水位/告警：synced_at 展示 + 延迟标记

**验收**：
- 给用户勾选 host 实例 → check-instance（Casbin + OpenFGA）allow/deny 正确；
- filter（OpenFGA ListObjects）返回允许实例列表；
- 停掉 mock-cmdb，check/filter 仍正常（关系已物化在 OpenFGA），日志标记资源索引 stale。

**面试叙事**：**解耦数据源**（事件同步 + 优雅降级）——直接回应"CMDB 崩→全崩"旧痛点；**实例级授权引入 OpenFGA（CNCF/Zanzibar）**，check/filter 双接口，讲清"动作级 Casbin + 实例级 OpenFGA"双层叠加与短路。

### P5 — 管理控制台（4 天）

**目标**：Vue3 管理台，全流程 UI 可操作。

任务：
- [ ] 项目初始化（Vite + TS + Pinia + Router + Element Plus）
- [ ] 登录页 + 路由守卫 + 布局
- [ ] 用户/组织/组管理页（含树形控件）
- [ ] 应用管理页（注册 + 触发同步 + 权限点树展示）
- [ ] 角色管理页（角色挂权限点，板块式勾选树）
- [ ] 策略管理页（API 策略 + 数据策略表单：选模型→选实例/关系/条件）
- [ ] 应用注册/权限市场页：注册申请（简化自审批）+ 负责人管理 + 出方向申请/入方向审批 + client 凭证
- [ ] 权限申请页：提交申请（选应用/角色/数据范围）+ 审批页（按风险分级）
- [ ] 审计日志页
- [ ] 联调后端

**验收**：从登录到"配数据权限 + 提交/审批申请"全流程 UI 可完成，无需 curl。

**面试叙事**：权限配置从"逐条勾选"升级为"角色+策略"，演示配置效率。

### P6 — 进阶：策略分发 + 可观测 + 压测（4 天）

**目标**：本地决策 agent、bundle 分发、压测对比、完整演示脚本。

任务：
- [ ] bundle 生成（builder）+ `/v1/bundles/:app` 拉取 + checksum
- [ ] `cmd/iam-agent`：轮询拉包 + 原子激活 + 本地 Casbin 决策 + 状态上报
- [ ] force_remote 风险分级（action 标记 → 回源中心）
- [ ] 数据级决策缓存：Check/ListObjects 结果缓存（TTL）；agent 仅承载动作级本地决策，数据级回源 OpenFGA
- [ ] 审批受限令牌：工单审批通过后签发 scoped+TTL 令牌，凭其执行真实写操作
- [ ] 到期回收：定时任务扫描 expires_at，回收 JIT 权限（写审计）
- [ ] JML 演示：入职自动得权限 / 调岗跟随 / 离职停用回收
- [ ] SoD 冲突检测：申请人与审批人互斥、owner 不能自批自家应用（提为必需）
- [ ] （可选）owner 失联兜底：组织树向上查找处理人，转移/下线走审批流
- [ ] Redis Streams 事件总线：审计事件 + CMDB webhook 事件统一走流（组件两用）
- [ ] （可选）策略仓库 GitOps：策略导出 YAML → Git 审批/回滚演示
- [ ] 决策日志/审计查询接口 + 指标（延迟/命中率/升级率）
- [ ] 压测脚本：远程决策 vs 本地决策延迟/吞吐对比
- [ ] `scripts/demo.sh`：一键演示（正常链路 → 无权限 → CMDB 宕机降级 → 策略发布生效）
- [ ] README 完善 + 面试叙事材料整理

**验收**：
- 策略发布 → agent 秒级~分钟级生效（版本号可见）；
- 压测数据产出（如本地决策 P99 < 5ms vs 远程 30ms）；
- demo.sh 全流程可跑通。

**面试叙事**：OPA bundle 思想的落地（版本化快照/原子激活/状态上报/降级回源）+ 风险分级 + 压测数据；版本化/审计三层组件化（OpenFGA 白嫖 + Redis Streams 两用 + GitOps 进阶）；申请-审批-开通-回收治理闭环（IGA 思想）。

---

## 10. 配置与部署

### 10.1 环境变量（`deploy/.env.example`）

```bash
# 服务
IAM_HTTP_ADDR=:8080
IAM_LOG_LEVEL=info
# 数据库
PG_DSN=postgres://iam:iam@localhost:5432/iam?sslmode=disable
# Redis
REDIS_ADDR=localhost:6379
# JWT
JWT_SECRET=change-me
JWT_ACCESS_TTL=15m
JWT_REFRESH_TTL=168h
# OpenFGA
OPENFGA_ADDR=localhost:8081
# mock-cmdb
CMDB_BASE_URL=http://localhost:8090
CMDB_WEBHOOK_TOKEN=...
```

### 10.2 docker-compose 服务

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| postgres | postgres:16 | 5432 | 主存储（业务 + OpenFGA 各自独立库） |
| redis | redis:7 | 6379 | 缓存 |
| openfga | openfga/openfga:1.x | 8081/8082 | 实例级关系引擎 |
| apisix | apache/apisix:3.x | 9080/9180 | 网关 |
| (app 服务) | 本地 go run | 8080/8090/8091 | iam-server / mock-cmdb / mock-identity |

### 10.3 Makefile 目标

```makefile
up        # docker compose up -d (pg/redis/openfga/apisix)
down      # docker compose down
seed      # go run ./cmd/iam-server seed（Go 写入种子数据）
run       # go run ./cmd/iam-server
run-cmdb  # go run ./cmd/mock-cmdb
run-id    # go run ./cmd/mock-identity
test      # go test ./...
build     # go build ./...
```

---

## 11. 测试与验证计划

| 层级 | 内容 | 阶段 |
|------|------|------|
| 单元 | authz 求值（Casbin model 用例）、openapi 解析、scope→OpenFGA 翻译 | P2–P4 随写随测 |
| 集成 | 管理 API + 存储（testcontainers 可选） | P3 起 |
| e2e | 网关链路（放行/拦截）、数据鉴权、降级 | P4/P6 |
| 压测 | 远程 vs 本地决策对比（wrk/hey） | P6 |
| 演示 | `scripts/demo.sh` 一键脚本 | P6 |

---

## 12. 决策点清单（请逐条确认）

| 编号 | 决策点 | 选项 | 我的建议 |
|------|--------|------|----------|
| D1 | Go module 名 | `github.com/xcy/permission-center` / 自定义 | 按你 GitHub 实际地址 |
| D2 | 数据库访问方式 | GORM / pgx+手写 SQL / sqlc | GORM（已按你的意见确定） |
| D3 | 建表/迁移方式 | GORM AutoMigrate / goose(Go) | GORM AutoMigrate（零手写 SQL，随启动执行） |
| D4 | 认证方案 | JWT(access+refresh) / 简化单 token | JWT 双 token |
| D5 | mock-cmdb 协议 | 真实 OpenAPI 3 文档 / 简化自造 | 真实 OpenAPI 3（更真实、可讲） |
| D6 | 是否新增"工单"demo 下游 | 只 cmdb / 加一个工单 app | 只 cmdb（够演示），工单后续可加 |
| D7 | filter 返回形态 | 实例 ID 列表 / 可拼 SQL 条件片段 | 先列表，条件片段为加分项 |
| D8 | 前端语言 | TypeScript / JavaScript | TypeScript |
| D9 | 数据级实现 | 引入 OpenFGA / 自研 / ABAC 条件 | **OpenFGA（已确定）**，自研收缩为翻译/适配层 |
| D10 | 压测数据要求 | 需要量化对比 / 定性即可 | 量化（heys 简单跑出数据） |
| D11 | 是否现在装 Docker 环境 | 本机有 / 需要引导安装 | 确认环境 |
| D12 | P5 前端是否现在就做 | 全部阶段顺序执行 / 先跳过 P5 后补 | 顺序执行（P5 是演示重要部分） |
| D13 | 程序授权（M2M）方式 | OAuth2 Client Credentials / 简化共享密钥 | Client Credentials（已确定） |
| D14 | 工单"审批后写"实现 | 审批受限令牌 / 服务长期写权限 | 审批受限令牌（已确定）；双主体方案暂不实现 |
| D15 | 版本化/审计组件策略 | 全自写 / OpenFGA+事件流+GitOps | OpenFGA 白嫖 + Redis Streams 两用 + GitOps 进阶（已确定） |
| D16 | 权限分配/申请治理 | 纯管理员 / 申请+审批+开通+回收（IGA） | 核心档：自助申请+风险分级审批+自动开通+JIT回收（已确定）；进阶审阅/SoD 仅预留接口 |
| D17 | 身份源/组织架构同步 | 手工建 / mock-identity + SCIM 同步 + JML | mock-identity 独立服务 + Identity Connector + JML（P6）（已确定） |
| D18 | 应用注册模式 | 自动通过 / 工单审批+办理 / demo 简化自审批 | 真实走工单+网络打通；demo 简化自审批（已确定） |
| D19 | 审计管理员边界 | 全局只读 / 只读+最小处置权 | 全局只读，处置走工单审批、无授权能力（已确定） |
| D20 | owner 失联兜底 | 无 / 负责人≥2+组织树向上 | 应用负责人≥2 + 组织树向上查找处理人（已确定） |
| D21 | 自申请边界 | 管理员审批 / 资源 owner 审批 | 资源 owner 审批；经理审批仅限组织内自申请（已确定） |

---

## 13. 里程碑时间线（估算）

| 阶段 | 内容 | 累计（人日） |
|------|------|------|
| P0 | 骨架 | 0.5 |
| P1 | 基础域 | 2.5 |
| P2 | OpenAPI 模板 | 4.5 |
| P3 | API 鉴权+网关+程序身份+应用注册 | 8.5 |
| P4 | 数据鉴权+降级+身份同步 | 11.5 |
| P5 | 管理控制台+申请审批+权限市场 | 16.5 |
| P6 | 进阶+压测+演示 | 22 |

> 合计约 **22~24 人日**（业余时间约 3~5 周）。

---

## 14. 面试叙事素材对照表（持续填充）

| 旧痛点 | 重构方案 | 证明/数据（P6 产出） |
|--------|----------|---------------------|
| CMDB 崩→全崩 | 资源索引/关系物化（OpenFGA）+ 事件同步 + 优雅降级 | demo 停 CMDB 仍可用 |
| 数据膨胀 | 投影存储 + 决策缓存 + bundle 本地决策 | 压测吞吐对比 |
| 配置繁琐 | RBAC 角色 + 策略 + 板块模板 | 演示配置路径 |
| 未调研业界 | PEP/PDP/PAP/PIP + 策略即数据 + Casbin(动作)+OpenFGA(实例) + OPA bundle 思想 | 架构图 + 术语 |
| 程序授权缺失 | OAuth2 Client Credentials + 审批受限令牌（最小权限+时效） | 演示云管只读/事件 CRUD/工单审批后写 |
| 权限分配单点 | IGA 式闭环：申请+风险分级审批+自动开通+JIT回收+审计 | 演示申请→审批→生效→回收 |
| 数据手工维护 | 身份源 SCIM 同步 + JML 生命周期（组织组只读/自建组分离） | 演示入职/调岗/离职权限跟随 |
| 集中管理员单点 | 开放自服务 + 弱管理员 + 权限市场（owner 授权/SoD/审计） | 演示注册-暴露-申请-审批闭环 |
| 无审计 | 审计 + 决策日志 + 版本化 | 查询演示 |
| 性能瓶颈 | 控制面/数据面分离 + 本地决策 + 风险分级 | 压测 P99 对比 |

---

## 15. 待办（评审后）

- [x] 你阅读本文档并确认 §12 决策点
- [x] 按确认结果修订本文档
- [x] 开始 P0

---

## 16. 实施进度（2026-08-03 更新）

> 本次会话完成 P0–P4 与 P6 核心 + P5 前端脚手架 + 目录重构（backend/frontend）+ 网关落地（Traefik 替代 APISIX），全部经 e2e 验证；`bash scripts/demo.sh` 全链路通过（含网关步骤）。

| 阶段 | 状态 | 说明 |
|------|------|------|
| P0 骨架 | ✅ | go.mod/配置/docker-compose/GORM AutoMigrate/Makefile/README |
| P1 基础域 | ✅ | users/groups(物化路径)/apps + JWT(token_version) + 种子 |
| P2 OpenAPI 模板 | ✅ | mock-cmdb(OpenAPI3) + 解析器(复数归一化) + 15 权限点/3 板块（含 list 与 read 区分）+ deny-by-default |
| P3 API 鉴权+网关 | ✅ | Casbin(RBAC,域) + 决策缓存(Redis) + PEP 共享密钥 + OAuth Client Credentials + 角色/策略 API + e2e 通过 |
| P4 数据鉴权+降级 | ✅ | OpenFGA 接入(授权模型/关系物化) + check-instance/filter + CMDB 事件同步 + 身份同步 + 孤儿清理留接口 |
| P5 管理控制台 | ✅ | Vue3+Vite+TS+Pinia+Element Plus 脚手架（7 页面），`cd frontend && npm run build` 通过（npm 可用） |
| P6 进阶 | ✅(核心) | bundle(checksum/版本) + iam-agent(本地动作级决策/状态上报/回源) + demo.sh 全链路通过；JML/SoD/压测/Redis Streams 审计为后续迭代项 |
| 网关 | ✅ | Traefik v3（ghcr.io 镜像，file provider 无需 etcd）forwardAuth → `/v1/gateway/check`（请求→action 映射 + deny-by-default）；`demo.sh` 步骤 8 覆盖 allow/deny/无身份/M2M |
| 目录结构 | ✅ | 前后端分离：`backend/`（Go）+ `frontend/`（Vue3，原 web/）+ `deploy/`（docker-compose + traefik/） |
| **OrbStack 全栈部署** | ✅ | 9 个容器统一管理（pg/redis/openfga/traefik + iam-server/mock-cmdb/mock-identity/iam-agent/frontend）；`COMPOSE_PROJECT_NAME=permission-center` + `dev.orbstack.domains`（frontend/api/cmdb 三域名）；`make up` 一键构建启动；容器化 demo.sh 全链路通过 |

**已发现并修复的关键问题（面试可讲）**：
1. Casbin `keyMatch2` 会把权限点 code 中的 `:` 当路径参数通配，导致 `cmdb:host:create` 误匹配 `cmdb:host:read` → 改用精确匹配；
2. OpenFGA v1.8 校验 assignable 关系必须声明 `directly_related_user_types`（metadata），且 `GET /stores` 返回 `{stores:[...]}`（EnsureStore 需按此解析，否则重复建 store）；
3. 决策缓存命中时未返回 matched pids 导致 check-instance/filter 失效 → 缓存值携带 pid；策略发布/变更时清决策缓存，保证"发布即时生效"演示；
4. OpenAPI 解析器对集合 GET 与详情 GET 生成相同 code（`cmdb:host:read`）被幂等 upsert 覆盖 → 确定性区分 `list`（集合）与 `read`（详情），网关 `GET /api/v1/hosts` 命中 `cmdb:host:list`；
5. Traefik forwardAuth 默认把鉴权请求方法转为 GET（`preserveRequestMethod` 默认 false）→ 网关回调用 `gw.Any` 注册；`authRequestHeaders` 白名单需放行 `X-PEP-Token`（否则 pep-token 注入的密钥被过滤）；
6. seed 幂等：角色/策略重复执行时按 code/name 查改，避免重复创建同名策略；`go run` 的 `pkill` 需匹配编译出的二进制（`exe/iam-server`），否则旧进程占用端口。
7. **OrbStack 全栈容器化（2026-08-03）**：macOS 编译产物是 Mach-O，Linux 容器需 ELF → `make up` 内部交叉编译 `GOOS=linux GOARCH=arm64 CGO_ENABLED=0`；daocloud 对 `golang` 镜像拉取缓慢 → 后端用 alpine 最小运行时 + 宿主机预编译二进制；容器内 npm install 网络不稳定（lockfile 锁定 registry 容器内不可达）→ 前端宿主机构建 dist + nginx 运行时；openfga 新 volume 需先建 `openfga` 库再 migrate；iam-server 启动时 OpenFGA 未就绪则 EnsureSchema 失败且不重试（storeID 空 → 数据级鉴权 400），需重启 iam-server。
