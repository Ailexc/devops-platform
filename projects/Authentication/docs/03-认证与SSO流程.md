# 统一认证中心 — 认证与 SSO 流程

## 一、登录认证流程（用户名 / 密码）

```mermaid
sequenceDiagram
    participant U as 用户
    participant P as 门户 Portal
    participant A as 认证中心 Auth
    participant S as 身份源(降级链)

    U->>P: 输入用户名/密码
    P->>A: POST /api/auth/login
    A->>S: 依次尝试 Local/LDAP/Okta
    S-->>A: 校验通过，返回标准化 UserProfile
    A->>A: 签发 RS256 JWT（含 sub/uid/name/roles）
    A-->>P: { access_token, user, expires_in }
    P->>P: 存储 token（内存/HttpOnly Cookie）
    P-->>U: 跳转应用广场
```

要点：
- 密码只发给认证中心，各业务系统**不接触密码**
- JWT 携带最小必要信息（用户标识、姓名、角色），不敏感
- 认证中心可签发 `refresh_token`，避免频繁登录

## 二、SSO 单点登录流程（Demo 实现）

```mermaid
sequenceDiagram
    participant U as 用户(已登录门户)
    participant P as 门户应用广场
    participant A as 认证中心
    participant B as 业务系统(SPA)
    participant G as 统一网关(forwardAuth)

    U->>P: 点击「MockApp」应用
    P->>P: 调 /api/auth/sso-url 获取带统一JWT的跳转地址
    P->>B: 新窗口打开 homeUrl?token=JWT
    B->>B: SPA 前端读取 URL token，存入本地存储
    B->>G: 携 Authorization: Bearer JWT 调用业务 API
    G->>A: forwardAuth → /api/auth/verify 校验 JWT
    A-->>G: 200 + 注入 X-Auth-User / X-Auth-Username 等响应头
    G->>B: 放行，X-Auth-* 头转发给业务后端
    B-->>U: 返回业务数据（免登录）
```

要点（Demo）：
- 门户点击应用 → 经 `sso-url` 获取带统一 JWT 的跳转 URL（`home_url?token=xxx`）
- 业务系统 **SPA 首页免鉴权**加载，前端读取 URL token 后存入本地
- 调用受保护业务 API 时前端携带 `Authorization: Bearer <JWT>`，**统一网关 forwardAuth 校验**
- 网关放行时注入 `X-Auth-*` 请求头，业务后端无需解析 JWT，直接读头取身份
- `verify` 端点 Demo 兼容从 query `token` 读取（SSO 直开场景）；真实生产应仅用 Authorization 头

> ⚠️ Demo 简化：JWT 直接携带跳转。**真实生产**绝不在 URL 传 token，而是走 **OIDC 授权码流程**（见下节），或使用 HttpOnly + Secure Cookie + CSRF 防护。

## 三、真实生产 SSO：OIDC 授权码流程（文档说明）

真实项目中，业务系统通过标准 OIDC 与认证中心对接：

```mermaid
sequenceDiagram
    participant U as 用户
    participant B as 业务系统
    participant A as 认证中心(IdP)
    participant O as Okta(外部身份源)

    U->>B: 访问业务系统(未登录)
    B->>A: 302 → /oauth2/authorize?client_id&redirect_uri&scope
    A->>O: 若门户未登录，先做 Okta 认证
    O-->>A: Okta 登录成功
    A-->>U: 302 → redirect_uri?code=授权码
    U->>B: 携带 code 回到业务系统
    B->>A: POST /oauth2/token?code + client_secret
    A-->>B: { access_token, id_token }
    B->>A: GET /oauth2/userinfo (可选)
    A-->>B: 用户信息
    B-->>U: 建立会话，正常访问
```

对应知识点：
- **OAuth2 授权码模式**：`authorize` → `code` → `token` 三步
- **OIDC**：在 OAuth2 之上增加 `id_token`（JWT），携带身份断言
- **client_id / client_secret**：业务系统注册时发放，即「应用注册表」管理的内容
- Demo 中该流程由 `OktaAuthenticator` 预留实现，可对接自建 mock OIDC Provider

## 四、登出流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant P as 门户
    participant A as 认证中心
    participant B as 业务系统

    U->>P: 点击退出登录
    P->>A: POST /api/auth/logout
    A->>A: 撤销 refresh_token / 会话（JWT 本身无状态）
    P-->>U: 清除本地 token，回到登录页
    Note over U,B: 各业务系统 token 仍有效直至过期<br/>(单点登出 SLO 为扩展项)
```

- JWT 是无状态凭证，无法服务端主动作废；登出 = 客户端删除 token + 认证中心撤销 refresh token
- 面试点：JWT 无状态 vs 会话化（黑名单/Redis 白名单）的取舍

## 五、统一网关 forwardAuth 鉴权流程

```
请求 → Traefik → [forwardAuth 中间件] → /api/auth/verify
                                           │
                           200(带X-Auth-*)  │  401/403
                         放行→业务后端       │  302 → 门户登录页
```

- `/api/auth/verify` 校验 `Authorization: Bearer <JWT>`，返回 `200` + 用户头，或 `401`
- 网关在放行时注入 `X-Auth-User`、`X-Auth-Username` 等头，业务后端直接从请求头取身份，**无需再解析 JWT**
- 该模式把鉴权下沉到网关，业务系统零改动接入（改配置即可）
