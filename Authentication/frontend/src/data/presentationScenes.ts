/** 系统宣讲 —— 场景数据（配置驱动，与 WorkFlowCenter 的 presentation 同理念）。 */

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
    description: '统一门户 + 认证中心 + 统一网关，三种接入方式',
    themeColor: '#1d5fd6',
    duration: '~2 分钟',
    steps: [
      {
        title: '项目定位',
        narration:
          '这是还原真实工作经验的企业级统一认证体系：统一门户、登录认证、SSO 多系统统一访问。' +
          '真实场景中用户通过 EAA 进入统一门户，Okta 认证后签发跨系统共用的 JWT，即可无感访问所有已授权应用。',
        highlight: '一次登录，多系统统一访问',
        points: ['统一门户：应用广场，数据驱动', '认证中心：签发统一 JWT', '三种业务系统接入方式'],
      },
      {
        title: '整体架构',
        narration:
          '前端是统一门户（React+antd），后端是认证中心（FastAPI）。' +
          '认证中心负责登录、签发 RS256 JWT、发布 JWKS 公钥、维护应用注册表；' +
          '统一网关（Traefik）负责对业务 API 做 forwardAuth 统一鉴权；' +
          '业务系统通过三种方式接入：经网关、直连自验签、OIDC 授权码。',
        highlight: '门户 · 认证中心 · 网关 三层清晰分工',
        flow: ['👤 用户', '🏠 统一门户', '🔑 认证中心', '🛡️ 统一网关', '📦 业务系统'],
        points: ['统一凭证：RS256 JWT + JWKS 公钥', '统一网关：forwardAuth 验票 + 注入身份', '身份源：Local / LDAP / Okta 可降级'],
      },
    ],
  },
  {
    id: 'architecture',
    title: '架构设计',
    description: '分层架构 · 技术选型 · 关键数据流 · 部署与演进',
    themeColor: '#0ea5e9',
    duration: '~3 分钟',
    steps: [
      {
        title: '四层架构',
        narration:
          '系统按职责分为四层：接入层（统一门户 + 统一网关）负责入口与统一鉴权；' +
          '认证层（认证中心）负责登录、签发统一 JWT、维护应用注册表；' +
          '数据层（SQLite）存用户、应用注册、认证日志；身份源层（Local/LDAP/Okta）是可插拔的用户来源。',
        highlight: '接入 / 认证 / 数据 / 身份源 四层清晰解耦',
        flow: ['接入层 门户·网关', '认证层 认证中心', '数据层 用户·应用·日志', '身份源层 Local·LDAP·Okta'],
        points: ['接入层：统一入口 + forwardAuth 统一鉴权', '认证层：登录 / 签发 JWT / 应用注册表', '身份源层：策略模式可插拔、可降级'],
      },
      {
        title: '技术选型',
        narration:
          '门户用 React 19 + antd（应用广场 / 管理 / 演示板块）；认证中心用 Python FastAPI（异步、自动 OpenAPI）；' +
          '统一凭证用 RS256 + JWKS（非对称，公钥可分发给所有异构系统）；' +
          '网关用 Traefik forwardAuth（配置即接入）；数据用 SQLite（Demo 零依赖，可换 PostgreSQL）。',
        highlight: '异构友好 · 零依赖可跑 · 生产可替换',
        points: ['门户 React19+antd / 认证中心 FastAPI', '凭证 RS256+JWKS（异构系统共享验签）', '网关 Traefik forwardAuth / 数据 SQLite'],
      },
      {
        title: '关键数据流',
        narration:
          '一条统一 JWT 贯穿全程：登录后签发 → 门户与业务系统持有 → 三种接入方式校验' +
          '（网关转发验签 / 直连本地验签 / OIDC 换 token）→ 业务系统读到身份。',
        highlight: '统一凭证一条链路，接入方式可插拔',
        flow: ['登录签发 JWT', '网关 forwardAuth', '直连 JWKS 验签', 'OIDC 授权码', '业务系统读身份'],
        points: ['网关：验票 + 注入 X-Auth-* 头', '直连：本地验签不回源', 'OIDC：code + client_secret 换 token'],
      },
      {
        title: '部署与演进',
        narration:
          'Docker Compose + OrbStack 一键编排：认证中心 / 门户 / 网关 / 演示应用各一个容器，域名自动解析。' +
          '演进方向：JWKS 密钥轮换、refresh token 入库、对接真实 Okta 身份源、真实业务系统按 pilot-app 方式接入。',
        highlight: '容器化部署 · 演进有清晰路径',
        points: ['一键 docker compose up 全栈', '密钥轮换（JWKS kid 多公钥共存）', '按 pilot-app 方式接入真实系统'],
      },
    ],
  },
  {
    id: 'auth',
    title: '统一认证',
    description: '登录 → 身份源降级链 → 签发统一 JWT',
    themeColor: '#10b981',
    duration: '~2 分钟',
    steps: [
      {
        title: '登录认证流程',
        narration:
          '用户输入用户名密码后，认证中心通过"身份源降级链"校验身份：' +
          '优先 Okta，不可用降级到 LDAP，再降级到本地用户库。' +
          '身份源抽象为统一接口（Authenticator），校验通过后返回标准化的用户信息。',
        highlight: '身份源抽象 + 降级链（failover）',
        flow: ['输入用户名密码', 'Okta（不可用则降级）', 'LDAP（不可用则降级）', '本地用户库 bcrypt', '签发统一 JWT'],
        points: ['策略模式：Local / LDAP / Okta 可插拔', '身份源不可用自动降级', '认证失败不降级（安全边界）'],
      },
      {
        title: '统一凭证 JWT',
        narration:
          '认证通过后签发统一 JWT（RS256 非对称签名）：私钥在认证中心，公钥通过 /.well-known/jwks.json 发布。' +
          '任何系统用公钥即可验签，无需回源认证中心——这是它能被多系统共用的关键。',
        highlight: 'RS256 非对称签名 · JWKS 公钥发布',
        points: ['JWT 载荷：sub/uid/name/source 等', 'aud 标识 token 归属应用', '公钥公开，谁都能验、又没人能伪造'],
      },
    ],
  },
  {
    id: 'sso',
    title: '单点登录与三种接入',
    description: '网关 forwardAuth · 直连 JWKS · OIDC 授权码',
    themeColor: '#8b5cf6',
    duration: '~3 分钟',
    steps: [
      {
        title: 'SSO 单点跳转',
        narration:
          '门户登录后点击应用，认证中心返回带统一 JWT 的跳转地址（home_url?token=xxx），' +
          '业务系统 SPA 读取 token 后，调 API 时携带 Authorization: Bearer <JWT>。',
        highlight: '一次登录，凭证全程复用',
        points: ['URL 带 token 仅用于跳转瞬间（Demo 简化）', '进入系统后走 Authorization 请求头', '生产建议 Cookie 或 OIDC'],
      },
      {
        title: '方式一：经统一网关',
        narration:
          '业务 API 挂在统一网关后面，网关用 forwardAuth 把 JWT 转发给认证中心 /api/auth/verify 校验，' +
          '通过后注入 X-Auth-* 头再放行。业务后端零鉴权代码，直接读头就知道是谁。',
        highlight: '网关统一验票 · 业务零鉴权',
        flow: ['请求带 JWT', '网关 forwardAuth', '/api/auth/verify 验签', '注入 X-Auth-* 头', '业务后端读头'],
        points: ['无 token → 401 拦截', '带 token → 200 + 注入身份', '适合网关能覆盖的应用'],
      },
      {
        title: '方式二：直连 JWKS 自验签',
        narration:
          '不经网关的应用（外部部署/内部服务），自己拉取认证中心公钥本地验签统一 JWT，' +
          '不用每次回源、认证中心挂了已发 token 仍可验。direct-app 里就有个 20 行的验签中间件。',
        highlight: '本地验签 · 无状态 · 高可用',
        points: ['从 /.well-known/jwks.json 拉公钥缓存', '本地验 RS256 签名与有效期', '适合网关覆盖不到的应用'],
      },
      {
        title: '方式三：OIDC 授权码',
        narration:
          '企业标准 OIDC 授权码流程：前端跳 /authorize（带 client_id）→ 认证中心发一次性 code →' +
          '应用后端用 code + client_secret 换 token → 调 /userinfo 拿用户。' +
          'token 不进浏览器、client_secret 只存后端——这是它最安全的点。',
        highlight: '两阶段 · client 凭证 · 标准协议',
        flow: ['前端', '/authorize + client_id', '一次性 code', '后端 code+secret 换 token', '/userinfo', '用户信息'],
        points: ['一阶段给票 vs 两阶段先换券再换票', 'client_id 公开标识 / client_secret 机密', 'oauth-demo 已完整演示授权码流'],
      },
    ],
  },
  {
    id: 'lifecycle',
    title: '应用生命周期',
    description: '注册 → 发放凭证 → 上架 → 用户 SSO 进入',
    themeColor: '#f59e0b',
    duration: '~1.5 分钟',
    steps: [
      {
        title: '开发者控制台',
        narration:
          '门户提供「应用管理」，通过注册向导可视化接入新应用：填基本信息 → 系统自动发放 client_id/client_secret →' +
          '给出接入配置说明 → 应用立即上架到应用广场（数据驱动，无需重启）。',
        highlight: '可视化接入 · 注册即上架',
        flow: ['填写基本信息', '自动发放凭证', '接入配置说明', '上架应用广场', '用户 SSO 进入'],
        points: ['四步向导：基本信息/凭证/配置/完成', 'client_secret 一次性展示 + 保密提示', '广场数据驱动，注册即出现'],
      },
      {
        title: '应用凭证模型',
        narration:
          '每个应用注册后获得 client_id（公开标识）和 client_secret（机密，仅应用后端持有）。' +
          'token 跳转模式用不到它俩，OIDC 模式用于应用后端换取 token——这是"应用身份凭证"，与用户 JWT 是两层身份。',
        highlight: '两层身份：用户凭证 vs 应用凭证',
        points: ['用户凭证 JWT：证明哪个用户', '应用凭证 client_id/secret：证明哪个应用', 'OIDC 里二者配合完成授权'],
      },
    ],
  },
  {
    id: 'security',
    title: '安全设计',
    description: '降级安全边界 · 凭证传递 · 审计',
    themeColor: '#ef4444',
    duration: '~1.5 分钟',
    steps: [
      {
        title: '认证失败不降级',
        narration:
          '降级链只在"身份源不可用"（连接超时/宕机）时触发；用户不存在或密码错误是明确失败，绝不降级——' +
          '防止攻击者穿透到弱身份源。每次登录来源与结果都写入认证日志审计。',
        highlight: '安全边界 + 全量审计',
        points: ['区分"认证失败"与"身份源不可用"', '认证失败直接 401，不降级', '认证日志记录来源/结果/IP'],
      },
      {
        title: '凭证传递安全',
        narration:
          '统一 JWT 是 RS256 签名，传输走 HTTPS；API 请求用 Authorization 头（RFC 6750）传递，' +
          '而非 URL。URL 带 token 只是 Demo 跳转简化，生产用 HttpOnly Cookie 或 OIDC 授权码。',
        highlight: 'Authorization 头传递 · 避免 URL 泄露',
        points: ['Bearer Token 标准传递方式', 'URL token 有日志/历史泄露风险', 'Demo 简化需在生产替换'],
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
