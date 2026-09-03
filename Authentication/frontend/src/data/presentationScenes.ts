/** 系统宣讲 —— 场景数据（配置驱动，对齐 OIDC 标准改造后的现状）。
 *  高层演讲叙事；概念细节请见「系统文档」板块（后端 /system-docs 提供）。
 */

export interface PStep {
  title: string
  narration: string
  highlight?: string
  points?: string[]
  flow?: string[] // 流程可视化节点（横向流程）
}

export interface PScene {
  id: string
  title: string
  description: string
  themeColor: string
  duration: string
  steps: PStep[]
}

export const scenes: PScene[] = [
  {
    id: 'overview',
    title: '系统概览',
    description: '统一门户 SPA+BFF · 标准 OIDC Provider · 三种业务接入方式',
    themeColor: '#1d5fd6',
    duration: '~2 分钟',
    steps: [
      {
        title: '项目定位',
        narration:
          '这是还原真实工作经验的企业级统一认证体系：统一门户、登录认证、SSO 多系统统一访问。' +
          '真实场景中用户通过统一门户进入，认证中心按 OIDC 标准协议完成登录，签发跨系统可验证的凭证，即可无感访问所有已授权应用。',
        highlight: '一次登录，多系统统一访问',
        points: ['统一门户：SPA 前端 + BFF 后端（OIDC 客户端）', '认证中心：标准 OIDC Provider', '三种业务系统接入方式'],
      },
      {
        title: '整体架构',
        narration:
          '前端是统一门户（React 单页应用），门户自己不带认证逻辑，登录走 BFF（Backend for Frontend）：' +
          '由 BFF 按 OIDC 授权码 + PKCE 协议与认证中心完成登录，浏览器只拿到 HttpOnly 会话 Cookie。' +
          '认证中心（FastAPI）是标准 OIDC Provider：签发 id_token / access_token / refresh_token，发布 JWKS 公钥，维护应用注册表；' +
          '统一网关（Traefik）对业务 API 做 forwardAuth 统一鉴权。业务系统可通过三种方式接入：经网关、直连验签、OIDC 客户端。',
        highlight: '门户(BFF) · 认证中心(OIDC) · 网关 三层清晰分工',
        flow: ['👤 用户', '🏠 门户 SPA+BFF', '🔑 认证中心 OIDC', '🛡️ 统一网关', '📦 业务系统'],
        points: ['统一协议：OAuth 2.1 授权码 + PKCE + OIDC', '凭证：id_token/access_token/refresh_token', '身份源：Local 默认，LDAP/Okta 可插拔'],
      },
    ],
  },
  {
    id: 'architecture',
    title: '架构设计',
    description: '分层架构 · 技术选型 · OIDC 数据流 · 部署与演进',
    themeColor: '#0ea5e9',
    duration: '~3 分钟',
    steps: [
      {
        title: '四层架构',
        narration:
          '系统按职责分为四层：接入层（统一门户 + 统一网关）负责入口与统一鉴权；' +
          '认证层（认证中心）是标准 OIDC Provider，负责授权码、签发 Token、维护应用注册表；' +
          '数据层（外部共享库 PostgreSQL）存用户、应用注册、授权码、刷新令牌与认证日志；' +
          '身份源层（Local/LDAP/Okta）是可插拔的用户来源，当前默认本地用户库。',
        highlight: '接入 / 认证 / 数据 / 身份源 四层清晰解耦',
        flow: ['接入层 门户BFF·网关', '认证层 OIDC Provider', '数据层 PostgreSQL 共享库', '身份源层 Local·LDAP·Okta'],
        points: ['接入层：SPA+BFF 统一入口，forwardAuth 统一鉴权', '认证层：authorize / token / userinfo / JWKS', '数据层：外部共享 PostgreSQL，含 auth_codes / refresh_tokens'],
      },
      {
        title: '技术选型',
        narration:
          '门户用 React 19 + antd（应用广场 / 管理 / 宣讲 / 系统文档等板块）；' +
          '认证中心用 Python FastAPI（异步、自动 OpenAPI）；' +
          '认证协议用标准 OAuth 2.1 授权码 + PKCE + OIDC（OAuth 2.0 的收敛强化版）；' +
          'Token 用 RS256 非对称签名，公钥经 JWKS 分发给所有异构系统；' +
          '网关用 Traefik forwardAuth（配置即接入）；数据用外部共享库 PostgreSQL。',
        highlight: '标准协议 · 异构友好 · 生产可替换',
        points: ['门户 React19+antd / 认证中心 FastAPI', '协议 OAuth2.1 + PKCE + OIDC（非自研私有协议）', '凭证 RS256+JWKS · 数据 PostgreSQL'],
      },
      {
        title: '关键数据流',
        narration:
          '门户登录不再走"前端直接拿 JWT"，而是标准 OIDC 授权码 + PKCE：' +
          '门户 BFF 生成 PKCE 挑战值并发起 /authorize → 用户在认证中心登录 → 认证中心返回一次性授权码 →' +
          'BFF 用授权码 + code_verifier + client_secret 换 token → 建立 HttpOnly 会话。' +
          'Token 不进浏览器，浏览器只有会话 Cookie；业务系统另走网关验签 / 直连验签 / OIDC 客户端。',
        highlight: '标准授权码流程，Token 不落浏览器',
        flow: ['门户BFF 发起 authorize', '认证中心登录', '一次性授权码', 'BFF code+verifier 换 token', 'HttpOnly 会话', '业务系统接入'],
        points: ['PKCE：code_verifier/challenge 绑定授权码', 'BFF：client_secret 只在后端', '会话：HttpOnly Cookie，SPA 无感'],
      },
      {
        title: '部署与演进',
        narration:
          'Docker Compose + OrbStack 一键编排：认证中心 / 门户 / 网关 / 演示应用各一个容器，数据库用外部共享库 PostgreSQL。' +
          '标准 OIDC 改造（PKCE、id_token、refresh 轮换、授权码入库）已完成并全链路验证。' +
          '演进方向：JWKS 密钥轮换、启用真实 LDAP/Okta 身份源、BFF 独立成服务、真实业务系统按 OIDC 方式接入。',
        highlight: '容器化部署 · 演进有清晰路径',
        points: ['一键 docker compose up 全栈（7 容器）', '外部共享库：devops-postgres', '演进：JWKS 轮换 / 真实 IdP / BFF 拆分'],
      },
    ],
  },
  {
    id: 'auth',
    title: '统一认证',
    description: 'OIDC 授权码 + PKCE 登录 · Token 体系 · 身份源',
    themeColor: '#10b981',
    duration: '~2.5 分钟',
    steps: [
      {
        title: 'OIDC 授权码 + PKCE 登录',
        narration:
          '登录走标准 OIDC 授权码 + PKCE 流程：前端跳 /authorize（带 client_id、state、nonce、PKCE challenge）→' +
          '认证中心校验登录 → 302 回一次性授权码 → 应用后端用授权码 + code_verifier + client_secret 换 token →' +
          '校验 id_token 的 nonce → 完成。PKCE 让即使没有 client_secret 的前端场景也防授权码劫持。',
        highlight: '授权码 + PKCE：企业级标准登录',
        flow: ['/authorize + PKCE', '登录确认', '一次性 code', 'code+verifier+secret 换 token', '校验 nonce', '登录成功'],
        points: ['state 防 CSRF / nonce 防重放', '授权码 5 分钟一次性，哈希入库', 'oidc-demo 已完整演示六步'],
      },
      {
        title: 'Token 体系',
        narration:
          '认证中心签发三种 Token，职责分离：id_token 是身份断言（含 nonce，JWT 签名），证明"你是谁"；' +
          'access_token 是访问凭证，调 /userinfo 或业务 API 用；refresh_token 有效期长，用于无感续期。' +
          'refresh_token 轮换：每次使用即作废旧号、签发新号，检测到旧号复用立即吊销整族会话。',
        highlight: 'id_token / access_token / refresh_token 三权分离',
        points: ['id_token：身份断言，aud 匹配 client', 'access_token：访问凭证，RS256 签名', 'refresh_token：轮换 + 复用检测'],
      },
      {
        title: '身份源',
        narration:
          '身份源抽象为统一接口（Authenticator），当前默认本地用户库（bcrypt 密码校验）。' +
          'LDAP / Okta 作为可插拔身份源，配置启用后可按顺序降级（身份源不可用时切下一个）。' +
          '认证失败（用户不存在 / 密码错误）是明确失败，绝不降级，防止穿透弱身份源。',
        highlight: 'Local 默认 · 可插拔 · 失败不降级',
        flow: ['输入账密', 'Local 本地库 bcrypt', '（可配置）LDAP', '（可配置）Okta', '签发 Token'],
        points: ['当前 Docker 环境：AUTH_PROVIDER_ORDER=local', '策略模式：Local / LDAP / Okta 可插拔', '认证失败直接 401，不降级'],
      },
    ],
  },
  {
    id: 'sso',
    title: '单点登录与三种接入',
    description: 'SSO 会话 · 经网关 · 直连 JWKS · OIDC 客户端',
    themeColor: '#8b5cf6',
    duration: '~3 分钟',
    steps: [
      {
        title: 'SSO 单点登录',
        narration:
          '门户登录后，BFF 建立 HttpOnly 会话 Cookie，SPA 无感恢复用户。应用广场点击应用时，' +
          '门户向认证中心换取带统一 JWT 的跳转地址（sso-url），业务系统用该 JWT 作为内部链路凭证。' +
          '统一 JWT 是内部模拟链路的凭证（RS256 签名、aud 区分应用），与 OIDC 标准登录解耦。',
        highlight: '门户走 OIDC 会话，业务链路走统一 JWT',
        points: ['门户：BFF 会话，SPA 不持有 token', '应用广场：sso-url 统一 JWT 透传', '统一 JWT：内部链路凭证（Demo 模拟）'],
      },
      {
        title: '方式一：经统一网关',
        narration:
          '业务 API 挂在统一网关后面，网关用 forwardAuth 把 JWT 转发给认证中心校验，' +
          '通过后注入 X-Auth-* 头再放行。业务后端零鉴权代码，直接读头就知道是谁。',
        highlight: '网关统一验票 · 业务零鉴权',
        flow: ['请求带 JWT', '网关 forwardAuth', '认证中心验签', '注入 X-Auth-* 头', '业务后端读头'],
        points: ['无 token → 401 拦截', '带 token → 200 + 注入身份', '适合网关能覆盖的应用'],
      },
      {
        title: '方式二：直连 JWKS 自验签',
        narration:
          '不经网关的应用（外部部署 / 内部服务），自己拉取认证中心公钥（JWKS）本地验签统一 JWT，' +
          '不用每次回源、认证中心挂了已发 token 仍可验。direct-app 里就有个 20 行的验签中间件。',
        highlight: '本地验签 · 无状态 · 高可用',
        points: ['从 /.well-known/jwks.json 拉公钥缓存', '本地验 RS256 签名与有效期', '适合网关覆盖不到的应用'],
      },
      {
        title: '方式三：OIDC 客户端接入',
        narration:
          '企业标准 OIDC 授权码 + PKCE 接入：应用注册后获得 client_id / client_secret 与回调地址白名单，' +
          '前端跳 /authorize → 一次性 code → 应用后端用 code + verifier + secret 换 token → /userinfo 拿用户。' +
          'token 不进浏览器、client_secret 只存后端——门户本身就是这个方式的实例（通过 BFF）。',
        highlight: '标准协议接入 · 门户自身即 OIDC 客户端',
        flow: ['注册应用', '/authorize + PKCE', '一次性 code', '后端换 token', '/userinfo', '用户信息'],
        points: ['redirect_uri 精确白名单校验', 'client_secret 机密仅后端持有', 'oidc-demo / portal 均为 OIDC 客户端'],
      },
    ],
  },
  {
    id: 'lifecycle',
    title: '应用生命周期',
    description: '注册 → OIDC 配置 → 发放凭证 → 上架 → SSO 进入',
    themeColor: '#f59e0b',
    duration: '~1.5 分钟',
    steps: [
      {
        title: '开发者控制台',
        narration:
          '门户提供「应用管理」，通过注册向导接入新应用：填基本信息 → 配置接入方式（OIDC 客户端需配 redirect_uri 白名单，PKCE 强制）→' +
          '系统自动发放 client_id / client_secret → 给出接入配置说明 → 应用立即上架到应用广场（数据驱动，无需重启）。',
        highlight: '可视化接入 · 注册即上架',
        flow: ['填写基本信息', '接入方式与回调配置', '自动发放凭证', '接入说明', '上架应用广场', '用户 SSO 进入'],
        points: ['OIDC 客户端：redirect_uri 精确白名单', 'client_secret 一次性展示 + 保密提示', '广场数据驱动，注册即出现'],
      },
      {
        title: '应用凭证模型',
        narration:
          '每个应用注册后获得 client_id（公开标识）和 client_secret（机密，仅应用后端持有）。' +
          'OIDC 客户端还登记 redirect_uri 白名单与 PKCE 要求。' +
          '应用凭证验证"哪个应用"，用户凭证（id_token / access_token）验证"哪个用户"——两层身份配合完成授权。',
        highlight: '两层身份：用户凭证 vs 应用凭证',
        points: ['用户凭证：证明哪个用户', '应用凭证 client_id/secret：证明哪个应用', 'OIDC 里二者配合完成授权'],
      },
    ],
  },
  {
    id: 'security',
    title: '安全设计',
    description: '协议级安全 · Token 安全 · 身份与审计',
    themeColor: '#ef4444',
    duration: '~2 分钟',
    steps: [
      {
        title: '协议级安全',
        narration:
          'OIDC 标准内置多重防护：state 参数防 CSRF（回跳时严格校验）；nonce 防 id_token 重放；' +
          'PKCE 防授权码被截获后冒用（code_verifier 只有申请方知道）；授权码 5 分钟有效、一次性、哈希入库，杜绝数据库泄露直接可用。',
        highlight: 'state / nonce / PKCE / 一次性授权码 四重防护',
        points: ['state 防 CSRF · nonce 防重放', 'PKCE 绑定授权码与申请方', '授权码哈希入库、一次性、短时效'],
      },
      {
        title: 'Token 安全',
        narration:
          'id_token 与 access_token 职责分离，id_token 不用于调 API；' +
          'refresh_token 轮换 + 复用检测：旧号作废、新号签发，检测到旧号复用立即吊销整族会话；' +
          '凭证传递用 Authorization 头或 HttpOnly Cookie，避免 URL 泄露；' +
          '统一 JWT 为 RS256 签名，公钥可分发验签、私钥不落其他系统。',
        highlight: '轮换 + 复用检测 + 分离传递',
        points: ['refresh 轮换：旧号作废新号签发', '复用检测：旧号复用即吊销整族', '凭证传递：Header / HttpOnly Cookie'],
      },
      {
        title: '身份与审计',
        narration:
          '认证失败（用户不存在 / 密码错误）直接 401，绝不降级到弱身份源；' +
          '只有"身份源不可用"才触发降级链。每次登录的来源、结果、IP、时间都写入认证日志，管理员可审计。',
        highlight: '安全边界 + 全量审计',
        points: ['区分"认证失败"与"身份源不可用"', '认证失败直接 401，不降级', '认证日志记录来源/结果/IP'],
      },
    ],
  },
]

export function getSceneById(id: string): PScene | undefined {
  return scenes.find((s) => s.id === id)
}

export function getSceneIndex(id: string): number {
  return scenes.findIndex((s) => s.id === id)
}

export function getNextScene(id: string): PScene | null {
  const idx = getSceneIndex(id)
  return idx >= 0 && idx < scenes.length - 1 ? scenes[idx + 1] : null
}
