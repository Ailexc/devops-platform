/** 可视化 E2E 测试 —— 场景与步骤定义（真实调用认证中心 API）。 */

export interface RunCtx {
  token: string | null
  setToken: (t: string | null) => void
}

export interface StepOutput {
  request: unknown
  response: unknown
}

export interface E2eInput {
  label: string
  value: string
  kind?: 'text' | 'secret' // secret 显示为打码
}

export interface E2eOutput {
  label: string
  value: string
  kind?: 'text' | 'secret' | 'ok' | 'warn'
}

export interface E2eStepDef {
  name: string
  method: string
  api: string
  principle: string // 这一步背后怎么运作（文字说明）
  inputs?: E2eInput[] // 关键输入（输入框形式展示）
  withoutAuth?: boolean
  run: (ctx: RunCtx, prev?: StepOutput) => Promise<StepOutput>
  extract?: (resp: unknown) => E2eOutput[] // 从响应提取关键输出
}

export interface E2eSceneDef {
  id: string
  name: string
  description: string
  intro: string // 场景说明（运行前展示）
  steps: E2eStepDef[]
}

// ---------- 请求辅助 ----------
async function jsonCall(
  ctx: RunCtx,
  method: string,
  url: string,
  opts?: { body?: unknown; withoutAuth?: boolean },
): Promise<StepOutput> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (ctx.token && !opts?.withoutAuth) headers.Authorization = `Bearer ${ctx.token}`
  const request = { method, url, headers, body: opts?.body ?? undefined }
  try {
    const res = await fetch(url, {
      method,
      headers,
      body: opts?.body ? JSON.stringify(opts.body) : undefined,
    })
    let data: unknown = null
    try {
      data = await res.json()
    } catch {
      data = await res.text()
    }
    return { request, response: { status: res.status, data } }
  } catch (e) {
    return { request, response: { error: String(e) } }
  }
}

async function formCall(
  url: string,
  form: Record<string, string>,
): Promise<StepOutput> {
  const request = { method: 'POST', url, form }
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(form).toString(),
    })
    let data: unknown = null
    try {
      data = await res.json()
    } catch {
      data = await res.text()
    }
    return { request, response: { status: res.status, data } }
  } catch (e) {
    return { request, response: { error: String(e) } }
  }
}

const DEMO_USER = { username: 'zhangsan', password: 'demo1234' }
const OIDC = {
  clientId: 'oidc-demo-app',
  clientSecret: 'oidc-demo-secret-123456', // 演示应用固定凭证
  redirectUri: 'http://localhost:8005/callback',
}

// 占位：运行时若已有 token 则展示
const ctxTokenPlaceholder = '<统一JWT（登录后自动获取）>'

// 从响应取 data
const dataOf = (resp: unknown): any => (resp as { data?: unknown })?.data
const statusOf = (resp: unknown): number | undefined => (resp as { status?: number })?.status

// ---------- 场景 ----------
export const e2eScenes: E2eSceneDef[] = [
  {
    id: 'login',
    name: '① 登录认证',
    description: '用户名密码 → 身份源降级链校验 → 签发统一 JWT',
    intro: '演示用户登录：认证中心通过「身份源降级链」（Local→LDAP→Okta）校验用户名密码，校验通过后签发统一 JWT——这张票就是后续所有系统的"通行证"。',
    steps: [
      {
        name: '登录并获取统一 JWT',
        method: 'POST',
        api: '/api/auth/login',
        principle:
          '认证中心把用户名/密码交给身份源降级链：优先 Okta，不可用降级 LDAP，再降级本地用户库（LocalAuthenticator 用 bcrypt 比对密码哈希）。' +
          '校验通过后，认证中心用 RSA 私钥签发 RS256 JWT（含用户标识、姓名、来源），返回给前端。拿到这张 JWT，第一步就成功了。',
        inputs: [
          { label: '用户名', value: DEMO_USER.username },
          { label: '密码', value: DEMO_USER.password, kind: 'secret' },
        ],
        run: async (ctx) => {
          const out = await jsonCall(ctx, 'POST', '/api/auth/login', { body: DEMO_USER })
          const data = dataOf(out.response)
          if (data?.access_token) ctx.setToken(data.access_token)
          return out
        },
        extract: (resp) => {
          const d = dataOf(resp) || {}
          return [
            { label: 'access_token（统一 JWT）', value: d.access_token || '—', kind: 'secret' },
            { label: '签发用户', value: d.user ? `${d.user.display_name}（${d.user.username}）` : '—' },
            { label: '认证来源', value: d.user?.source || '—' },
          ]
        },
      },
    ],
  },
  {
    id: 'credentials',
    name: '② 统一凭证与公钥',
    description: 'JWKS 公钥发布 + 携带 JWT 访问受保护接口',
    intro: '统一 JWT 是非对称签名（RS256）：认证中心私钥签发、公钥公开。本场景演示"公钥从哪来"以及"前端如何带着 JWT 访问受保护接口"。',
    steps: [
      {
        name: '获取 JWKS 公钥',
        method: 'GET',
        api: '/.well-known/jwks.json',
        principle:
          '认证中心把 RSA 公钥发布成 JWKS（JSON Web Key Set），公开地址 /.well-known/jwks.json。' +
          '任何业务系统拉取后即可对统一 JWT 验签——因为公钥是公开的，谁都能验、又没人能伪造。',
        inputs: [{ label: '端点', value: '/.well-known/jwks.json' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/.well-known/jwks.json'),
        extract: (resp) => {
          const keys = dataOf(resp)?.keys || []
          const first = keys[0] || {}
          return [
            { label: '密钥数量', value: String(keys.length) },
            { label: '算法 alg', value: first.alg || '—' },
            { label: '密钥 ID kid', value: first.kid || '—' },
          ]
        },
      },
      {
        name: '获取当前登录用户',
        method: 'GET',
        api: '/api/auth/me',
        principle:
          '前端在请求头带上 Authorization: Bearer <统一JWT>，认证中心解码验证签名和有效期后，返回当前用户信息。' +
          '这就是"带着票去办事"的标准姿势——凭证放请求头，而不是 URL。',
        inputs: [{ label: 'Authorization', value: 'Bearer <统一JWT>', kind: 'secret' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/api/auth/me'),
        extract: (resp) => {
          const u = dataOf(resp) || {}
          return [
            { label: '当前用户', value: `${u.display_name}（${u.username}）` },
            { label: '部门', value: u.department || '—' },
            { label: '认证来源', value: u.source || '—' },
          ]
        },
      },
    ],
  },
  {
    id: 'sso',
    name: '③ SSO 单点跳转',
    description: '门户获取某应用的 SSO 跳转地址（携带统一 JWT）',
    intro: '用户从门户点击某个应用时，门户向认证中心申请该应用的 SSO 跳转地址——地址里带着统一 JWT，跳过去就能免登录。',
    steps: [
      {
        name: '获取应用 SSO 跳转地址',
        method: 'GET',
        api: '/api/auth/sso-url?app_id=pilot-app',
        principle:
          '认证中心为已登录用户生成该应用的跳转地址。' +
          '方式一（网关会话）：返回干净 URL（无 token），浏览器通过网关会话 Cookie 自动认证。' +
          '方式二（一次性授权码）：返回 URL 带一次性 code（非 JWT，60s 过期），业务后端用 code 换 JWT。' +
          '方式三（OIDC）：返回 /oauth/login 跳转授权端点。',
        inputs: [{ label: '应用标识 app_id', value: 'pilot-app' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/api/auth/sso-url?app_id=pilot-app'),
        extract: (resp) => {
          const d = dataOf(resp) || {}
          return [
            { label: '目标应用', value: d.app || '—' },
            { label: 'SSO 跳转地址', value: d.url || '—', kind: 'secret' },
          ]
        },
      },
    ],
  },
  {
    id: 'gateway',
    name: '④ 统一网关校验',
    description: 'forwardAuth 验票：无 token 拦截 / 带 token 放行并注入身份',
    intro: '业务 API 挂在统一网关后面，网关用 forwardAuth 把 JWT 转发给认证中心校验：没票拦截（401），有票放行并注入身份头（X-Auth-*）。业务系统零鉴权。',
    steps: [
      {
        name: '无 token 访问受保护接口（应 401）',
        method: 'GET',
        api: '/api/auth/verify',
        principle:
          '网关 forwardAuth 场景：请求没带 JWT，认证中心返回 401 拦截。' +
          '这证明网关确实在"验票"——没票的请求根本到不了业务系统。',
        inputs: [{ label: 'Authorization', value: '（无）' }],
        withoutAuth: true,
        run: (ctx) => jsonCall(ctx, 'GET', '/api/auth/verify', { withoutAuth: true }),
        extract: (resp) => [
          { label: 'HTTP 状态', value: String(statusOf(resp)), kind: statusOf(resp) === 401 ? 'ok' : 'warn' },
          { label: '结果', value: statusOf(resp) === 401 ? '已拦截（符合预期）' : '未按预期拦截', kind: statusOf(resp) === 401 ? 'ok' : 'warn' },
        ],
      },
      {
        name: '带统一 JWT 校验（应 200 + X-Auth-* 头）',
        method: 'GET',
        api: '/api/auth/verify',
        principle:
          '请求带统一 JWT，认证中心验签通过返回 200，并通过 X-Auth-User / X-Auth-Name 等响应头把身份回传，' +
          '网关再把这些头注入下游请求——业务后端读头就知道是谁，自己一行鉴权代码都不用写。',
        inputs: [{ label: 'Authorization', value: 'Bearer <统一JWT>', kind: 'secret' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/api/auth/verify'),
        extract: (resp) => {
          const u = dataOf(resp)?.user || {}
          return [
            { label: 'HTTP 状态', value: String(statusOf(resp)) },
            { label: '放行用户', value: u.display_name ? `${u.display_name}（${u.username}）` : '—' },
            { label: '注入身份头', value: 'X-Auth-User / X-Auth-Name / X-Auth-Source' },
          ]
        },
      },
    ],
  },
  {
    id: 'direct',
    name: '⑤ 直连 JWKS 验签',
    description: '不经网关，用公钥本地验统一 JWT（等价 verify 验签）',
    intro: '不经网关的应用（外部部署/内部服务）自己当"验票员"：用认证中心公钥本地验 JWT 签名，不用每次回源。',
    steps: [
      {
        name: '携带统一 JWT 本地验签（应 200）',
        method: 'GET',
        api: '/api/auth/verify?token=<JWT>',
        principle:
          '直连模式：应用从 /.well-known/jwks.json 拉取公钥后，本地验证 JWT 的 RS256 签名与有效期——' +
          '不需要请求认证中心（等价于业务系统自己用公钥验票）。direct-app 里就有这个 20 行的验签中间件。',
        inputs: [{ label: '统一 JWT', value: ctxTokenPlaceholder, kind: 'secret' }],
        run: (ctx) =>
          ctx.token
            ? jsonCall(ctx, 'GET', `/api/auth/verify?token=${encodeURIComponent(ctx.token)}`)
            : Promise.resolve({ request: { note: '请先运行①登录' }, response: { error: '无 token' } }),
        extract: (resp) => {
          const u = dataOf(resp)?.user || {}
          return [
            { label: 'HTTP 状态', value: String(statusOf(resp)) },
            { label: '验签通过用户', value: u.display_name ? `${u.display_name}（${u.username}）` : '—' },
          ]
        },
      },
    ],
  },
  {
    id: 'oidc',
    name: '⑥ OIDC 授权码模式',
    description: 'authorize → 一次性 code → code+client_secret 换 token → userinfo',
    intro: '企业标准 OIDC 授权码流程：前端拿一次性 code，应用后端用 code + client_secret 换真正的 token（client_secret 是机密，只在后端），再拿 token 取用户信息。',
    steps: [
      {
        name: '① 授权端点：拿一次性 code',
        method: 'GET',
        api: '/oauth/authorize?response_mode=json&client_id=oidc-demo-app',
        principle:
          '业务前端跳认证中心授权端点，带上 client_id（应用身份）。认证中心校验统一 JWT 后，' +
          '签发一个一次性授权码 code（短期有效、用完即废）。注意：这一步只给"兑换券"，不给真票。',
        inputs: [
          { label: 'client_id（应用身份）', value: OIDC.clientId },
          { label: '统一 JWT', value: ctxTokenPlaceholder, kind: 'secret' },
        ],
        run: async (ctx) => {
          const params = new URLSearchParams({
            response_type: 'code',
            client_id: OIDC.clientId,
            redirect_uri: OIDC.redirectUri,
            scope: 'openid profile',
            response_mode: 'json',
          })
          return jsonCall(ctx, 'GET', `/oauth/authorize?${params.toString()}`)
        },
        extract: (resp) => [
          { label: '一次性授权码 code', value: dataOf(resp)?.code || '—', kind: 'secret' },
        ],
      },
      {
        name: '② 令牌端点：code + client_secret 换 access_token',
        method: 'POST',
        api: '/oauth/token',
        principle:
          '业务后端用 code + client_secret 换真正的 access_token。client_secret 是机密凭证、只存在应用后端——' +
          '所以这一步必须由后端发起，token 不经过浏览器 URL，这就是 OIDC 比直接传 token 安全的原因。',
        inputs: [
          { label: 'code（上一步）', value: '…', kind: 'secret' },
          { label: 'client_secret（后端持有）', value: OIDC.clientSecret, kind: 'secret' },
        ],
        run: async (_ctx, prev?: unknown) => {
          const code = (prev as { response?: { data?: { code?: string } } } | undefined)?.response?.data?.code
          if (!code) return { request: { note: '上一步未拿到 code' }, response: { error: '缺少 code' } }
          return formCall('/oauth/token', {
            grant_type: 'authorization_code',
            code,
            client_id: OIDC.clientId,
            client_secret: OIDC.clientSecret,
            redirect_uri: OIDC.redirectUri,
          })
        },
        extract: (resp) => {
          const d = dataOf(resp) || {}
          return [
            { label: 'access_token', value: d.access_token || '—', kind: 'secret' },
            { label: 'token 类型', value: d.token_type || '—' },
            { label: '有效期（秒）', value: String(d.expires_in ?? '—') },
          ]
        },
      },
      {
        name: '③ UserInfo：Bearer access_token 拿用户信息',
        method: 'GET',
        api: '/oauth/userinfo',
        principle:
          '业务后端凭 access_token 调 userinfo 端点，认证中心返回用户信息（张三/研发部），' +
          '完成"我是谁"的身份确认——整个授权码流程到此闭环。',
        inputs: [{ label: 'Authorization', value: 'Bearer <access_token>', kind: 'secret' }],
        run: async (_ctx, prev?: unknown) => {
          const token = (prev as { response?: { data?: { access_token?: string } } } | undefined)?.response?.data?.access_token
          if (!token) return { request: { note: '上一步未拿到 access_token' }, response: { error: '缺少 token' } }
          const headers: Record<string, string> = { Authorization: `Bearer ${token}` }
          const request = { method: 'GET', url: '/oauth/userinfo', headers }
          try {
            const res = await fetch('/oauth/userinfo', { headers })
            return { request, response: { status: res.status, data: await res.json() } }
          } catch (e) {
            return { request, response: { error: String(e) } }
          }
        },
        extract: (resp) => {
          const d = dataOf(resp) || {}
          return [
            { label: '用户名', value: d.preferred_username || '—' },
            { label: '姓名', value: d.name || '—' },
            { label: '部门', value: d.department || '—' },
            { label: '认证来源', value: d.source || '—' },
          ]
        },
      },
    ],
  },
  {
    id: 'platform',
    name: '⑦ 应用广场与身份源',
    description: '应用注册表驱动广场 + 身份源降级链健康状态',
    intro: '应用广场由应用注册表驱动（注册即上架）；身份源降级链展示当前各身份源（Local/LDAP/Okta）的可用性。',
    steps: [
      {
        name: '应用广场（需登录）',
        method: 'GET',
        api: '/api/apps',
        principle:
          '门户请求应用列表，认证中心返回应用注册表中"已启用"的应用。数据驱动——在应用管理里注册一个新应用，广场立即出现，无需改代码。',
        inputs: [{ label: 'Authorization', value: 'Bearer <统一JWT>', kind: 'secret' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/api/apps'),
        extract: (resp) => {
          const apps = (dataOf(resp) || []) as { name?: string; access_mode?: string }[]
          return [
            { label: '应用数量', value: String(apps.length) },
            { label: '接入方式分布', value: `网关 ${apps.filter(a => a.access_mode === 'gateway').length} 个 / 直连 ${apps.filter(a => a.access_mode === 'direct').length} 个` },
          ]
        },
      },
      {
        name: '身份源降级链健康状态',
        method: 'GET',
        api: '/api/system/health',
        principle:
          '健康检查返回身份源降级链中每个身份源的可用性。当前 Local 可用；LDAP/Okta 为预留（未启用）。' +
          '身份源不可用时自动降级到下一个——这是高可用的关键。',
        inputs: [{ label: '端点', value: '/api/system/health' }],
        run: (ctx) => jsonCall(ctx, 'GET', '/api/system/health'),
        extract: (resp) => {
          const providers = dataOf(resp)?.providers || []
          const line = providers
            .map((p: { name: string; available: boolean }) => `${p.name}${p.available ? '✓' : '✕'}`)
            .join(' · ')
          return [{ label: '降级链状态', value: line || '—' }]
        },
      },
    ],
  },
]

