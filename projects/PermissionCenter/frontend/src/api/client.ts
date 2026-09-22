// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
const BASE = ''

// 约定：request(url, method = 'GET', body?)
export async function request<T = any>(url: string, method: string = 'GET', body?: any): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  // 无需注入 Authorization 头，网关 Session Cookie 自动随请求发送
  const res = await fetch(BASE + url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401) {
    // 网关会话已过期/未建立 → 跳转门户登录
    localStorage.removeItem('iam_token')
    window.location.href = `${window.location.protocol}//${window.location.hostname}:8088/login`
    throw new Error('未登录')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = (data as any).error || (data as any).message || res.statusText
    throw new Error(msg)
  }
  return data as T
}

export const api = {
  login: (username: string, password: string) =>
    request('/api/v1/auth/login', 'POST', { username, password }),

  // demo 登录：人员列表 + 一键登录（免密码）
  people: () => request('/api/v1/auth/people'),
  demoLogin: (username: string) =>
    request('/api/v1/auth/demo-login', 'POST', { username }),

  me: () => request('/api/v1/users/me'),
  users: () => request('/api/v1/users'),
  createUser: (u: any) => request('/api/v1/users', 'POST', u),

  // ---- 我的视图（以我为中心）----
  meOverview: () => request('/api/v1/me/overview'),
  mePermissions: () => request('/api/v1/me/permissions'),
  meCapabilityPermissions: () => request('/api/v1/me/capability-permissions'),
  meCapabilityPresets: (cid: number) => request(`/api/v1/me/capabilities/${cid}/presets`),
  meRevokePreset: (cid: number, pid: string, body?: any) => request(`/api/v1/me/capabilities/${cid}/presets/${pid}/revoke`, 'POST', body),
  meOrgPermissions: () => request('/api/v1/me/org/permissions'),
  meGroups: () => request('/api/v1/me/groups'),

  groups: () => request('/api/v1/groups'),
  createGroup: (g: any) => request('/api/v1/groups', 'POST', g),
  addMember: (gid: number, uid: number) => request(`/api/v1/groups/${gid}/members`, 'POST', { user_id: uid }),
  removeMember: (gid: number, uid: number) => request(`/api/v1/groups/${gid}/members/${uid}`, 'DELETE'),

  // 组权限（组即角色）：发起授权申请单（组长申请，其他应用负责人审批）
  setGroupPermissions: (gid: number, action_ids: number[], reason?: string) =>
    request(`/api/v1/groups/${gid}/permissions`, 'POST', { action_ids, reason }),
  getGroupPermissions: (gid: number) =>
    request(`/api/v1/groups/${gid}/permissions`),
  getGroupCapabilityPermissions: (gid: number) =>
    request(`/api/v1/groups/${gid}/capability-permissions`),

  apps: () => request('/api/v1/apps'),
  appDetail: (id: number) => request(`/api/v1/apps/${id}`),
  registerApp: (a: any) => request('/api/v1/apps', 'POST', a),
  syncApp: (id: number) => request(`/api/v1/apps/${id}/sync`, 'POST'),
  actions: (id: number) => request(`/api/v1/apps/${id}/actions`),
  validateApp: (id: number) => request(`/api/v1/apps/${id}/validate`, 'POST'),

  // 能力声明（L1）
  capabilities: (id: number) => request(`/api/v1/apps/${id}/capabilities`),
  createCapability: (id: number, cap: any) => request(`/api/v1/apps/${id}/capabilities`, 'POST', cap),
  updateCapability: (id: number, cid: number, cap: any) =>
    request(`/api/v1/apps/${id}/capabilities/${cid}`, 'PUT', cap),
  deleteCapability: (id: number, cid: number) =>
    request(`/api/v1/apps/${id}/capabilities/${cid}`, 'DELETE'),
  publishCapability: (id: number, cid: number, body: any) =>
    request(`/api/v1/apps/${id}/capabilities/${cid}/publish`, 'POST', body),
  capabilityAuthz: (id: number, cid: number) =>
    request(`/api/v1/apps/${id}/capabilities/${cid}/authz`),
  syncCapabilities: (id: number) => request(`/api/v1/apps/${id}/sync-capabilities`, 'POST'),

  // 策略模板（L3）
  templates: (id: number) => request(`/api/v1/apps/${id}/templates`),
  createTemplate: (id: number, t: any) => request(`/api/v1/apps/${id}/templates`, 'POST', t),
  updateTemplate: (id: number, tid: number, t: any) =>
    request(`/api/v1/apps/${id}/templates/${tid}`, 'PUT', t),
  deleteTemplate: (id: number, tid: number) =>
    request(`/api/v1/apps/${id}/templates/${tid}`, 'DELETE'),
  publishTemplate: (id: number, tid: number, status: string) =>
    request(`/api/v1/apps/${id}/templates/${tid}/publish`, 'POST', { status }),

  // 双向账本（FR-7）
  accessors: (id: number, type?: string) =>
    request(`/api/v1/apps/${id}/accessors${type ? `?type=${type}` : ''}`),
  accessorGrants: (id: number, sid: number) =>
    request(`/api/v1/apps/${id}/accessors/${sid}/grants`),
  upstreams: (id: number) => request(`/api/v1/apps/${id}/upstreams`),
  // 回收（走审批）
  revokeGrant: (gid: number, reason?: string) =>
    request(`/api/v1/grants/${gid}/revoke`, 'POST', { reason: reason || '' }),
  revokeRequests: (role?: string) =>
    request(`/api/v1/revoke-requests${role ? `?role=${role}` : ''}`),
  approveRevoke: (id: number, action: number, comment: string) =>
    request(`/api/v1/revoke-requests/${id}/approve`, 'POST', { action, comment }),

  // 权限市场（FR-3）
  marketplaceCapabilities: (params?: { q?: string; app?: string; model?: string; tag?: string }) => {
    const qs = new URLSearchParams()
    if (params?.q) qs.set('q', params.q)
    if (params?.app) qs.set('app', params.app)
    if (params?.model) qs.set('model', params.model)
    if (params?.tag) qs.set('tag', params.tag)
    const s = qs.toString()
    return request(`/api/v1/marketplace/capabilities${s ? `?${s}` : ''}`)
  },
  marketplaceTemplates: () => request('/api/v1/marketplace/templates'),
  capabilityPrereqs: (cid: number) => request(`/api/v1/marketplace/capabilities/${cid}/prereqs`),
  // 应用市场公开目录（申请接入用：网络/鉴权公开，不含管理信息）
  marketplaceApps: () => request('/api/v1/marketplace/apps'),
  marketplaceAppDetail: (id: number) => request(`/api/v1/marketplace/apps/${id}`),

  // 能力打包申请（能力包向导）：范围选项（预设×模型粒度，v12）+ 申请单预览
  presetScopeOptions: (cid: number, pid: string, mc: string) =>
    request(`/api/v1/capabilities/${cid}/presets/${pid}/models/${mc}/options`),
  savePresetScopeOptions: (cid: number, pid: string, mc: string, options: any[]) =>
    request(`/api/v1/capabilities/${cid}/presets/${pid}/models/${mc}/options`, 'POST', { options }),
  presetScopeMeta: (cid: number, pid: string) =>
    request(`/api/v1/capabilities/${cid}/presets/${pid}/scope-meta`),
  validateScopeOptions: (cid: number, pid: string, modelCode: string, options: any[]) =>
    request(`/api/v1/capabilities/${cid}/presets/${pid}/scope-options/validate`, 'POST', {
      model_code: modelCode,
      options,
    }),
  previewRequest: (r: any) => request('/api/v1/requests/preview', 'POST', r),

  policies: () => request('/api/v1/policies'),
  createPolicy: (p: any) => request('/api/v1/policies', 'POST', p),
  publishPolicy: (id: number) => request(`/api/v1/policies/${id}/publish`, 'POST', { reason: '控制台发布' }),

  requests: () => request('/api/v1/requests'),
  requestDetail: (id: number) => request(`/api/v1/requests/${id}`),
  requestsByRole: (role: string) => request(`/api/v1/requests?role=${role}`),
  submitRequest: (r: any) => request('/api/v1/requests', 'POST', r),
  // A8 定制需求卡：非目录请求（创建）与 owner 处置（grant 直授带 TTL / package 转为能力包）
  customRequest: (appId: number, body: any) => request(`/api/v1/apps/${appId}/custom-requests`, 'POST', body),
  fulfillRequest: (id: number, body: any) => request(`/api/v1/requests/${id}/fulfill`, 'POST', body),
  approveRequest: (id: number, action: number, comment: string) =>
    request(`/api/v1/requests/${id}/approve`, 'POST', { action, comment }),

  // 审计三视图（FR-8）
  auditMyRequests: () => request('/api/v1/audit/my-requests'),
  auditMyApprovals: () => request('/api/v1/audit/my-approvals'),
  auditMyPublishes: () => request('/api/v1/audit/my-publishes'),

  clients: () => request('/api/v1/clients'),
  rotateClientSecret: (clientId: string) => request(`/api/v1/clients/${clientId}/reveal`, 'POST'),

  resourceModels: () => request('/api/v1/resource-models'),
  instances: (mid: number) => request(`/api/v1/resource-models/${mid}/instances`),

  auditLogs: () => request('/api/v1/audit-logs'),
  decisionLogs: (traceId?: string) =>
    request(`/api/v1/decision-logs${traceId ? `?trace_id=${traceId}` : ''}`),

  // ---- 系统观测（黑盒显性化）----
  debugResolve: (r: any) => request('/api/v1/debug/resolve', 'POST', r),
  debugPip: (user: string) => request(`/api/v1/debug/pip/${encodeURIComponent(user)}`),
  debugCache: () => request('/api/v1/debug/cache'),
  debugCacheClear: () => request('/api/v1/debug/cache/clear', 'POST'),
  debugMetrics: () => request('/api/v1/debug/metrics'),
  debugOfga: () => request('/api/v1/debug/ofga'),
  debugOwners: () => request('/api/v1/debug/owners'),
  ownerCheck: () => request('/api/v1/owner-check', 'POST'),
  agents: () => request('/api/v1/agents'),
  bundles: (id: number) => request(`/api/v1/apps/${id}/bundles`),
  syncJobs: () => request('/api/v1/sync-jobs'),

  // ---- 系统知识库（复盘文档）----
  knowledgeDocs: () => request('/api/v1/knowledge/docs'),
  knowledgeDoc: (id: string) => request(`/api/v1/knowledge/docs/${encodeURIComponent(id)}`),
}
