# 统一认证中心（Authentication）— 统一门户 + SSO 单点登录

> 还原真实工作中「统一门户 + 登录认证 + SSO 多系统统一访问」经验的 Demo 系统。
> 基于真实项目：EAA → Okta 认证 → 统一门户 → 下发跨系统共用 JWT。

## 核心能力

- **统一门户**：React 19 + Ant Design 门户，登录后展示「应用广场」，点击即可无感访问各业务系统
- **认证中心**：Python + FastAPI，校验用户名/密码，签发 **RS256 统一 JWT**
- **SSO 单点登录**：一次登录，多系统统一访问
- **身份源抽象 + 降级链**（核心亮点）：`LocalAuthenticator` / `LdapAuthenticator` / `OktaAuthenticator`（预留），身份源不可用时自动降级，认证失败不降级（安全边界）
- **统一网关 forwardAuth**：Traefik 网关统一鉴权，业务系统配置级接入（`mock-app` 演示）
- **JWKS 公钥发布**：`/.well-known/jwks.json`，异构系统共享公钥验签

## 架构总览

```
用户 ──▶ 统一门户 Portal(React19) ──▶ 认证中心 Auth(FastAPI) ──▶ 身份源降级链
              │ 登录下发 JWT                              Local / LDAP / Okta
              ▼
         应用广场 ──▶ 点击应用(带JWT) ──▶ 统一网关(Traefik forwardAuth) ──▶ 业务系统
                                             校验JWT+注入X-Auth-*头
```

详细设计见 [`docs/`](docs/)：

| 文档 | 内容 |
|------|------|
| [01-需求与背景](docs/01-需求与背景.md) | 背景、真实项目参考、约束 |
| [02-系统架构设计](docs/02-系统架构设计.md) | 分层架构、关键技术决策 |
| [03-认证与SSO流程](docs/03-认证与SSO流程.md) | 登录 / SSO / OIDC / 登出 / forwardAuth 流程 |
| [04-身份源与认证降级](docs/04-身份源与认证降级.md) | **核心设计**：身份源抽象 + 降级链（回答「没有 Okta/LDAP 怎么办」） |
| [05-数据库与接口设计](docs/05-数据库与接口设计.md) | 表结构、JWT 载荷、API 清单 |
| [06-面试准备](docs/06-面试准备.md) | 面试叙事线、高频问题与应答 |
| [07-开发计划](docs/07-开发计划.md) | **后续路线图**：应用管理 / 两种接入 / OIDC / 打磨 |
| [08-演示脚本](docs/08-演示脚本.md) | **5 分钟面试演示稿**：分幕操作 + 讲解词 + 预期画面 |
| [09-云端部署迁移](docs/09-云端部署迁移.md) | **本地 OrbStack → 阿里云 Docker 迁移**：两种跳转地址域、DNS 泛解析、Traefik + HTTPS、环境变量化清单 |
| [📖 应用接入指南（图文版）](app-onboarding-guide.html) | **浏览器打开**：应用接入完整路径、两种接入方式、凭证机制图解 |
| [📖 SSO 凭证机制详解（图文版）](sso-credentials-guide.html) | **浏览器打开**：JWT 生命周期、token 跳转 vs OIDC、URL vs 请求头、两层身份 |

## 快速开始

### 方式一：本地开发（推荐，改代码热更新）

```bash
# 1. 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010

# 2. 前端（另开终端）
cd frontend
npm install
npm run dev        # http://localhost:5173
# 开发模式 /api 已代理到 http://127.0.0.1:8010
```

### 方式二：Docker Compose 全栈（OrbStack）

```bash
cp .env.example .env
docker compose up -d --build
```

| 服务 | 地址 | 说明 |
|------|------|------|
| 统一门户 | http://localhost:5175 | 登录 / 应用广场 / 个人中心 |
| 认证中心 API | http://localhost:8002/docs | Swagger 文档 |
| 统一网关（forwardAuth） | http://localhost:8001 | 受保护演示应用入口 |
| Traefik Dashboard | http://localhost:8080 | 网关面板 |
| OpenLDAP（可选） | ldap://localhost:389 | 演示目录树（`--profile ldap` 启用） |

OrbStack 域名（`dev.orbstack.domains` 自动解析）：`portal.authentication.orb.local`、`api.authentication.orb.local`、`mock.authentication.orb.local`。

### 演示账号

| 用户名 | 密码 | 身份源 | 说明 |
|--------|------|--------|------|
| `admin` | `admin1234` | 本地用户库 | 管理员（可管理用户/应用） |
| `zhangsan` | `demo1234` | 本地用户库 | 普通用户 |
| `lisi` / `wangwu` | `demo1234` | 本地用户库 | 普通用户 |

> LDAP 演示用户（`zhangsan`/`lisi`/`wangwu`，密码 `demo1234`）见 [`ldap/seed.ldif`](ldap/seed.ldif)。

## 切换 / 演示 LDAP 认证

OpenLDAP 是**可选服务**（compose profile `ldap`），默认全栈不依赖它。演示 LDAP：

```bash
# 1. .env 中开启并调整降级链
AUTH_PROVIDER_ORDER=ldap,local
AUTH_PROVIDER_LDAP_ENABLED=true

# 2. 启用 LDAP 服务并重建认证后端
docker compose --profile ldap up -d --build
```

然后用 `zhangsan / demo1234` 登录，个人中心的「认证来源」会显示 **LDAP**；查看 `http://localhost:8002/api/system/health` 可看到降级链中各身份源可用性。

> 💡 OpenLDAP 使用 `osixia/openldap:1.5.0` 镜像，`ldap/seed.ldif` 在首次启动（数据卷为空）时自动导入演示目录树（`dc=devops,dc=com` / `ou=people`）。若需重置数据：`docker compose --profile ldap down -v` 后重新 up。

## 数据库重置

项目提供一键重置脚本 `reset.sh`，可将数据库恢复到初始状态（删除数据库文件 + 重启服务）：

```bash
# 基本重置（仅重置认证中心数据库）
./reset.sh

# 完全重置（同时重置 LDAP 数据卷）
./reset.sh --full
```

**重置内容：**
- ✅ 删除 `auth.db` / `data/auth.db`（认证中心数据库）
- ✅ 重启所有服务（表结构 + 种子数据将自动重建）
- ❌ 保留 JWT 密钥（保持 token 有效性，避免其他系统 token 失效）
- ❌ 保留 LDAP 数据卷（除非使用 `--full` 参数）

**使用场景：**
- 面试前恢复干净的演示环境
- 开发中遇到数据异常需要重置
- 测试种子数据初始化逻辑

**注意事项：**
- 重置后首次访问时，系统会自动重建表结构和种子数据（4个用户 + 10个应用）
- 如果之前启用了 LDAP，重置后需要重新启动 LDAP 服务：`docker compose --profile ldap up -d`
- 脚本会自动执行 `docker compose down` 和 `docker compose up -d --build`

## 目录结构

```
Authentication/
├── backend/          # FastAPI 认证中心（JWT/JWKS/身份源抽象/SSO/应用注册表）
├── frontend/         # 统一门户（React19 + antd）
├── gateway/          # Traefik forwardAuth 统一网关
├── ldap/             # OpenLDAP 演示目录树
├── mock-app/         # 受网关保护的演示业务应用
├── docs/             # 设计文档与面试准备
├── reset.sh          # 数据库一键重置脚本
└── docker-compose.yml
```

## 面试亮点速览

1. **身份源抽象 + 降级链**：策略模式 + failover，区分「认证失败」与「身份源不可用」
2. **RS256 JWT + JWKS**：非对称签名、公钥发布、异构系统本地验签
3. **统一网关 forwardAuth**：鉴权下沉，业务系统零代码接入
4. **统一门户 + 应用注册表**：注册即上架，门户由数据驱动

## 内置演示板块（登录门户后可访问）

| 板块 | 地址 | 说明 |
|------|------|------|
| 🎬 系统宣讲 | `portal.authentication.orb.local/presentation` | 5 个场景图文宣讲（Hub + 播放器，`←→`/`Space`/`ESC`） |
| 🧪 SSO 测试流程 | `portal.authentication.orb.local/dev/e2e-test` | 7 个场景一键跑通，每步展示真实请求/响应小黑窗 |

> 参考 WorkFlowCenter 工单系统的「系统宣讲 / 流程测试」板块，以同样的可视化方式演示本项目能力。
