# DevOps 平台合集 —— 整体架构图

> 本文档是 DevOpsPlatform 全家桶的逻辑架构总览，含多层视图。
> 动态交互版见 [showcase/index.html](../showcase/index.html)。

---

## 1. 系统全景（总览视图）

```mermaid
flowchart TB
    USER["👤 用户 / 面试官 / 访问者"]

    subgraph PORTAL["统一接入层"]
        P["🚪 统一门户<br/>Authentication Portal<br/>(React 19 · 应用广场)"]
        GW["🛡 统一网关 Traefik<br/>forwardAuth 统一鉴权"]
        AUTH["🔐 认证中心 FastAPI<br/>RS256 JWT · JWKS · 身份源降级链"]
    end

    subgraph SYS["业务系统矩阵（7 个全栈系统）"]
        S1["🔐 认证中心<br/>Authentication"]
        S2["⚙️ 权限中心<br/>PermissionCenter<br/>Go + Casbin + OpenFGA"]
        S3["🚀 发布系统<br/>ReleaseManager<br/>Django + React + kind"]
        S4["🧩 工作流平台<br/>WorkFlowCenter<br/>Django + LogicFlow"]
        S5["☁️ 多云管理<br/>CloudManager<br/>Vue3 + Django"]
        S6["� 任务编排平台<br/>TaskManager<br/>Django + Celery"]
        S7["⚡ 事件管理<br/>EventManager<br/>Python + Go 双栈"]
    end

    subgraph INFRA["基础设施 & 数据层"]
        DB[("PostgreSQL / SQLite / MySQL")]
        CACHE[("Redis")]
        MQ[("RabbitMQ")]
        WORKER["Celery Worker"]
        K8S["kind 本地 K8s 集群"]
    end

    USER --> P
    P --> GW
    P --> AUTH
    GW --> AUTH
    AUTH --> SYS
    GW --> SYS
    SYS --> INFRA
```

---

## 2. 认证与统一访问视图

```mermaid
sequenceDiagram
    participant U as 用户
    participant P as 统一门户 Portal
    participant A as 认证中心 Auth
    participant G as 网关 Traefik
    participant B as 业务系统

    U->>P: 访问门户
    P->>A: 登录（账号密码）
    A->>A: 身份源降级链校验 (Local/LDAP/Okta)
    A-->>P: 签发 RS256 JWT + 发布 JWKS 公钥
    P->>G: 携带 JWT 点击业务系统
    G->>A: forwardAuth 校验 JWT
    A-->>G: 200 + 注入 X-Auth-* 身份头
    G->>B: 放行，业务系统无感进入
```

---

## 3. 权限中心（IAM）外部化授权视图

```mermaid
flowchart LR
    subgraph CP["控制面 Control Plane"]
        PAP["PAP 管理控制台 (Vue3)"]
        SYNC["同步服务 Sync Service"]
    end
    subgraph DP["数据面 Data Plane（无状态可水平扩展）"]
        PDP["PDP 授权决策 (Go)"]
        RBAC["Casbin 动作级 RBAC/ABAC"]
        REBAC["OpenFGA 实例级 ReBAC"]
        CACHE[("Redis 决策缓存")]
        PG[("PostgreSQL 主存储")]
    end
    subgraph PEP["下游接入 PEP"]
        GW["Traefik forwardAuth"]
        CMDB["CloudManager<br/>资源视图 Mock"]
    end

    PAP --> PDP
    SYNC --> PG
    SYNC --> CACHE
    PDP --> RBAC
    PDP --> REBAC
    PDP --> CACHE
    PDP --> PG
    GW -- 远程决策 --> PDP
    CMDB --> PDP
```

---

## 4. 多云管理（CloudManager）操作治理视图

```mermaid
flowchart LR
    UI["前端 Portal<br/>仿 AWS 控制台"] --> SVC["后端服务层"]
    SVC -->|不直接执行，转发| TICKET["工单系统<br/>流程编排 + 审批流转"]
    TICKET -->|审批通过| EXEC["自动化执行器"]
    EXEC -->|云 SDK| AWS["AWS"]
    EXEC -->|云 SDK| ALIYUN["阿里云"]
    EXEC --> OTHER["其他云 Provider"]
    TICKET -->|状态变更| MQ[("消息队列")]
    SVC -->|订阅| MQ
    SVC -->|所有展示数据| CMDB[("CMDB 配置管理数据库")]
    EXEC -->|执行结果回写| CMDB
```

> 核心设计：**前端/后端不直接调云 API**，所有资源变更先走工单审批，保证合规与留痕；**CMDB（云管资源视图）为系统内唯一数据源**，保证多页面数据一致。

> **平台数据边界原则**：各业务系统**数据自治**——共享同一 PostgreSQL 实例、**逻辑库隔离**（devops_event / devops_cmdb / …），互不直读直写；系统间只通过平台网关 API 交互，调用方身份由统一认证中心 JWT 标识。资源管理内置在 CloudManager 内（本图及各技术梳理文档中的 “CMDB” 均指**云管资源视图**，Demo 以多态资源表模拟）；**不引入独立 CMDB 系统**——生产权威 CMDB 为独立平台（如蓝鲸配置平台，一云一模型集分组管理），云管在其之上做汇聚读模型，**读写分离：云管拥有视图，权威源拥有真相**。

---

## 5. 部署形态视图

```mermaid
flowchart TB
    subgraph DEV["本地开发（OrbStack）"]
        DC["Docker Compose 全栈"]
        DOM["orb.local 自动域名，无端口冲突"]
    end
    subgraph SHOW["作品展示（静态托管）"]
        HTML["showcase/index.html<br/>滚动画卷式介绍页"]
        GH["GitHub Pages / Cloudflare Pages / Render"]
    end
    subgraph CLOUD["公网演示（Render 免费）"]
        R1["统一门户 demo-portal.onrender.com"]
        R2["各系统服务 .onrender.com"]
        DB2["SQLite 文件库"]
    end

    DOM --> DC
    GH --> HTML
    R1 --> R2
    R2 --> DB2
```

---

## 6. 技术栈矩阵

| 层级 | 技术选型 |
|------|----------|
| 前端 | React 19 / React 18 / Vue 3 · Ant Design / Element Plus · Vite · LogicFlow |
| 后端 | Python（FastAPI / Django / DRF / Ninja）+ Go（Gin / GORM）+ Celery |
| 网关 | Traefik（forwardAuth 统一鉴权） |
| 认证 | RS256 JWT + JWKS · SSO · OIDC · 身份源降级链（Local / LDAP / Okta） |
| 授权 | Casbin（RBAC/ABAC）· OpenFGA（ReBAC）· PEP/PDP 外部化授权 |
| 数据库 | SQLite / PostgreSQL / MySQL |
| 缓存/消息 | Redis · RabbitMQ · Celery Beat |
| 容器编排 | Docker Compose · OrbStack · kind（本地 K8s） |

---

## 7. 各系统详情入口

| 系统 | 架构文档 |
|------|----------|
| Authentication | [docs/02-系统架构设计.md](../Authentication/docs/02-系统架构设计.md) |
| CloudManager | [docs/02-系统架构设计.md](../CloudManager/docs/02-系统架构设计.md) |
| EventManager | [README](../EventManager/README.md) |
| PermissionCenter | [docs/architecture.md](../PermissionCenter/docs/architecture.md) |
| ReleaseManager | [SPEC.md](../ReleaseManager/SPEC.md) |
| TaskManager | [README](../TaskManager/README.md) |
| WorkFlowCenter | [docs/03-系统设计方案.md](../WorkFlowCenter/docs/03-系统设计方案.md) |
