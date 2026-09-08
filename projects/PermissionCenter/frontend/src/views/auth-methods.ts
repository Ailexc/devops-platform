// 鉴权方式知识库：每个方式讲清「机制 / 谁签发 / 怎么用 / 与权限中心关系 / 生命周期 / 风险」
// 点击鉴权方式卡片 → 右侧抽屉渲染（AppMarket / AppDetail 共用）

export interface AuthFlowStep { step: string; desc: string }

export interface AuthKnowledge {
  mechanism: string
  issuer: string
  usage: string[]
  relation: string
  lifecycle: string
  risk: string
  flow: AuthFlowStep[]
}

const BASE_FLOW: AuthFlowStep[] = [
  { step: '① 发起接入申请', desc: '在「应用市场」选择目标应用与鉴权方式，并确认网络打通（并入本次申请）' },
  { step: '② 提供方审批', desc: '目标应用 Owner 确认 + 平台复核（SoD：申请人 ≠ 审批人）' },
  { step: '③ IAM 签发凭证', desc: '权限中心 IAM 生成程序凭证（client_id/secret 或 Token），明文仅展示一次，库中只存哈希' },
  { step: '④ 能力包申请追加授权', desc: '凭证 = 身份（一次）；每次能力包申请通过后向该身份追加 scope（多次），凭证不变' },
  { step: '⑤ 调用与校验', desc: '使用方携带凭证换取访问令牌 → 网关（PEP）验签 + 校验已授权 scope → 放行 / 拒绝' },
]

export const AUTH_KNOWLEDGE: Record<string, AuthKnowledge> = {
  oauth2_client_credentials: {
    mechanism: '应用以自身身份（client_id + client_secret）向 IAM 的 OAuth2 端点换取短期 access_token（JWT）。令牌无状态，网关验签即可放行；它只代表「这个程序」，不携带用户身份。',
    issuer: '由权限中心 IAM 在「接入申请」审批通过后签发：生成 client_id 与 client_secret，明文仅展示一次，数据库只存哈希。',
    usage: [
      '接入申请通过后拿到 client_id / client_secret（妥善保存，仅展示一次）',
      '调用 POST /v1/oauth/token（client_credentials grant）换取 JWT',
      '请求头携带 Authorization: Bearer <token> 调用目标应用接口',
      '网关（PEP）验签 + 校验 scope 后放行',
    ],
    relation: '凭证 = 程序身份（一次签发、长期有效）；能力包申请 = 向该身份追加 scope（多次）；每次换取 JWT 只含已授权 scope——这就是「凭证与授权分离」的典型形态。',
    lifecycle: 'secret 可随时轮换；access_token 短 TTL（如 15 分钟），过期自动重取。',
    risk: 'secret 泄漏 = 身份被冒充。对策：只存哈希、定期轮换、全链路审计。',
    flow: BASE_FLOW,
  },
  static_token: {
    mechanism: 'IAM 签发一个固定字符串 Token，使用方在请求头 X-Auth-Token 携带；网关/PDP 按 Token 关联的授权范围放行。无状态性弱于 JWT（需查签发记录），适合轻量 / 内网 / 低频调用。',
    issuer: '由权限中心 IAM 在「接入申请」审批通过后签发（一次性展示），可按能力包限定范围，默认有效期 90 天。',
    usage: [
      '接入申请通过后拿到 Token（一次性展示）',
      '请求头携带 X-Auth-Token: <token> 调用目标应用接口',
      '网关映射 Token → 授权范围后放行',
    ],
    relation: '凭证 = 身份；能力包申请同样向该 Token 追加范围；到期轮换后身份不变、授权继续生效。',
    lifecycle: '默认 90 天，到期前提醒轮换；可随时吊销。',
    risk: '固定 Token 泄漏面较大 → 仅限内网 / 低风险接口，生产建议迁移到 OAuth2 Client Credentials。',
    flow: BASE_FLOW,
  },
  api_key: {
    mechanism: 'IAM 生成固定 API Key，请求头 X-API-Key 携带；适合工具脚本 / SDK 直连，机制与静态 Token 类似但更轻。',
    issuer: '由权限中心 IAM 在接入审批通过后签发，支持按接口前缀限定范围。',
    usage: ['拿到 Key → 请求头 X-API-Key: <key> → 网关映射授权范围放行'],
    relation: '凭证 = 身份；能力包申请追加接口/范围授权。',
    lifecycle: '可吊销与轮换；建议绑定 IP 白名单。',
    risk: '适合轻量场景；高权限操作不建议使用。',
    flow: BASE_FLOW,
  },
  oauth2_auth_code: {
    mechanism: '人工访问场景：用户经企业 SSO 登录授权页，换取访问令牌；令牌代表「某个用户」，支持用户级审计。',
    issuer: '由企业统一身份（SSO / OIDC Provider）签发，本系统对接校验。',
    usage: ['跳转授权页登录 → 回调换取 token → 请求头 Bearer 携带'],
    relation: '凭证绑定用户身份；能力包申请以该用户为 grantee。',
    lifecycle: '登录态短期有效，可刷新续期。',
    risk: '需回调地址白名单，防授权码截获。',
    flow: BASE_FLOW,
  },
  mtls: {
    mechanism: '双向 TLS：调用方与服务端互验证书，身份在 TLS 层建立，不依赖 token 字符串。',
    issuer: '企业 CA 签发客户端证书（演进方向，本期仅作信息声明，暂不自动签发）。',
    usage: ['申请证书 → 配置到调用方 → TLS 握手完成身份校验'],
    relation: '证书 = workload 身份；能力包 scope 授权体系不变。',
    lifecycle: '证书有效期较长，到期换发。',
    risk: '演进中：证书管理（轮换/吊销）成本高，本期不承诺自动签发。',
    flow: BASE_FLOW,
  },
  oidc: {
    mechanism: 'OIDC 单点登录：应用对接企业身份提供方，登录后获取 ID Token / Access Token，身份与组织信息标准化。',
    issuer: '企业统一身份平台签发（演进方向，本期仅声明）。',
    usage: ['浏览器跳转 SSO → 回调获取 token → 携带调用'],
    relation: '身份来自企业 IdP；授权仍由权限中心决策。',
    lifecycle: '登录态短期有效。',
    risk: '依赖企业 IdP 可用性；本期不承诺自动接入。',
    flow: BASE_FLOW,
  },
  _default: {
    mechanism: '应用声明支持的接入方式：使用方申请后由权限中心 IAM 签发程序凭证，调用时经网关校验放行。',
    issuer: '权限中心 IAM（接入申请审批通过后签发）。',
    usage: ['发起接入申请 → 审批通过 → 获取凭证 → 携带调用'],
    relation: '凭证 = 身份（一次）；能力包申请 = 追加 scope（多次）。',
    lifecycle: '按声明配置（有效期 / 轮换）。',
    risk: '请查看具体方式的说明。',
    flow: BASE_FLOW,
  },
}

export function authKnowledge(type: string): AuthKnowledge {
  return AUTH_KNOWLEDGE[type] || AUTH_KNOWLEDGE._default
}
