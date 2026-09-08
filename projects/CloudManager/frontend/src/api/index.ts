import api from './request'
import type {
  User, PaginatedResponse, CloudAccount, Resource, TicketOrder, TicketApproval,
  TicketTask, ResourceStats, GraphData, AppSummary, ImpactResult, Scenario, SyncJob,
  Environment, OrgTreeNode, AppDetail,
  OptimizationRule, OptimizationSuggestion, OptimizationReport, CostOverview,
} from '@/types'

// ===== 认证 =====
export const authApi = {
  login(data: { username: string; password: string }) {
    return api.post<{ access: string; refresh: string; user: User }>('/auth/login/', data)
  },
  getProfile() {
    return api.get<User>('/auth/profile/')
  },
  changePassword(data: { old_password: string; new_password: string }) {
    return api.post('/auth/change-password/', data)
  },
}

// ===== 用户 =====
export const userApi = {
  list(params?: any) {
    return api.get<PaginatedResponse<User>>('/auth/users/', { params })
  },
  get(id: number) {
    return api.get<User>(`/auth/users/${id}/`)
  },
  create(data: any) {
    return api.post<User>('/auth/users/', data)
  },
  update(id: number, data: any) {
    return api.put<User>(`/auth/users/${id}/`, data)
  },
  delete(id: number) {
    return api.delete(`/auth/users/${id}/`)
  },
}

// ===== 角色 =====
export const roleApi = {
  list() {
    return api.get('/auth/roles/')
  },
}

// ===== 部门 =====
export const departmentApi = {
  list() {
    return api.get('/auth/departments/')
  },
}

// ===== 云账号 =====
export const cloudAccountApi = {
  list(params?: any) {
    return api.get<PaginatedResponse<CloudAccount>>('/cmdb/accounts/', { params })
  },
  get(id: number) {
    return api.get<CloudAccount>(`/cmdb/accounts/${id}/`)
  },
  create(data: any) {
    return api.post('/cmdb/accounts/', data)
  },
  sync(id: number) {
    return api.post(`/cmdb/accounts/${id}/sync/`)
  },
}

// ===== 资源 =====
export const resourceApi = {
  list(params?: any) {
    return api.get<PaginatedResponse<Resource>>('/cmdb/resources/', { params })
  },
  get(id: number) {
    return api.get<Resource>(`/cmdb/resources/${id}/`)
  },
  stats() {
    return api.get<ResourceStats[]>('/cmdb/resources/stats/')
  },
  changes(id: number) {
    return api.get(`/cmdb/resources/${id}/changes/`)
  },
  securityRules(id: number) {
    return api.get(`/cmdb/resources/${id}/security_rules/`)
  },
  services(appId: number) {
    return api.get(`/cmdb/applications/${appId}/services/`)
  },
  endpoints(appId: number) {
    return api.get(`/cmdb/applications/${appId}/endpoints/`)
  },
}

// ===== 工单 =====
export const ticketApi = {
  list(params?: any) {
    return api.get<PaginatedResponse<TicketOrder>>('/ticket/orders/', { params })
  },
  get(id: number) {
    return api.get<TicketOrder>(`/ticket/orders/${id}/`)
  },
  create(data: any) {
    return api.post<TicketOrder>('/ticket/orders/', data)
  },
  approve(id: number, data: { action: number; comment?: string }) {
    return api.post(`/ticket/orders/${id}/approve/`, data)
  },
  cancel(id: number) {
    return api.post(`/ticket/orders/${id}/cancel/`)
  },
  getApprovals(id: number) {
    return api.get<TicketApproval[]>(`/ticket/orders/${id}/approvals/`)
  },
  getTasks(id: number) {
    return api.get<TicketTask[]>(`/ticket/orders/${id}/tasks/`)
  },
}

// ===== 操作日志 =====
export const auditApi = {
  list(params?: any) {
    return api.get('/auth/audit-logs/', { params })
  },
}

// ===== 服务目录 =====
export const catalogApi = {
  categories() {
    return api.get('/catalog/categories/')
  },
  items(params?: any) {
    return api.get('/catalog/items/', { params })
  },
  myQuota() {
    return api.get('/catalog/quotas/my_quota/')
  },
}

// ===== 成本中心 =====
export const costApi = {
  bills(params?: any) {
    return api.get('/cost/bills/', { params })
  },
  summary(months?: number, extra?: any) {
    return api.get('/cost/bills/summary/', { params: { months, ...extra } })
  },
  byDepartment(params?: any) {
    return api.get('/cost/bills/by_department/', { params })
  },
  byApplication(params?: any) {
    return api.get('/cost/bills/by_application/', { params })
  },
  shareFilters() {
    return api.get('/cost/bills/share_filters/')
  },
  globalFilters() {
    return api.get('/cost/bills/global_filters/')
  },
  applicationCostList() {
    return api.get('/cost/application-cost/')
  },
  applicationCost(appId: number) {
    return api.get('/cost/application-cost/', { params: { app_id: appId } })
  },
  environmentCost(params: any) {
    return api.get('/cost/application-cost/', { params })
  },
  environmentCostItems(params: any) {
    return api.get('/cost/application-cost/', { params: { ...params, items: 1 } })
  },
  applyBudget(data: any) {
    return api.post('/cost/application-cost/', data)
  },
  shareSummary(params?: any) {
    return api.get('/cost/bills/share_summary/', { params })
  },
  shareItems(params?: any) {
    return api.get('/cost/bills/share_items/', { params })
  },
  shareExport(params?: any) {
    return api.get('/cost/bills/share_export/', { params, responseType: 'blob' })
  },
  generateMock(month: string) {
    return api.post('/cost/bills/generate_mock/', { month })
  },
  budgets(params?: any) {
    return api.get('/cost/budgets/', { params })
  },
  budgetAlerts(month?: string) {
    return api.get('/cost/budgets/alerts/', { params: { month } })
  },
  // ===== 优化建议 =====
  suggestions(params?: any) {
    return api.get<PaginatedResponse<OptimizationSuggestion>>('/cost/suggestions/', { params })
  },
  resolveSuggestion(id: number) {
    return api.post(`/cost/suggestions/${id}/resolve/`)
  },
  // ===== 规则 =====
  rules(params?: any) {
    return api.get<PaginatedResponse<OptimizationRule>>('/cost/rules/', { params })
  },
  createRule(data: any) {
    return api.post<OptimizationRule>('/cost/rules/', data)
  },
  updateRule(id: number, data: any) {
    return api.put<OptimizationRule>(`/cost/rules/${id}/`, data)
  },
  deleteRule(id: number) {
    return api.delete(`/cost/rules/${id}/`)
  },
  runRule(id: number) {
    return api.post(`/cost/rules/${id}/run/`)
  },
  runAllRules() {
    return api.post<{ message: string; report: OptimizationReport }>('/cost/rules/run_all/')
  },
  ruleCloudGroups() {
    return api.get<Record<string, any[]>>('/cost/rules/cloud_groups/')
  },
  // ===== 报告 =====
  reports(params?: any) {
    return api.get<OptimizationReport[]>('/cost/reports/', { params })
  },
  reportDetail(id: number) {
    return api.get<OptimizationReport>(`/cost/reports/${id}/`)
  },
  exportReport(id: number) {
    return api.get(`/cost/reports/${id}/export/`, { responseType: 'blob' })
  },
  // ===== 总览 =====
  overview() {
    return api.get<CostOverview>('/cost/overview/summary/')
  },
}

// ===== 资源拓扑 =====
export const topologyApi = {
  get(type?: string, region?: string) {
    return api.get('/cmdb/topology/', { params: { type, region } })
  },
}

// ===== 图谱 =====
export const graphApi = {
  applications() {
    return api.get<AppSummary[]>('/cmdb/graph/applications/')
  },
  appDetail(id: number) {
    return api.get<AppDetail>(`/cmdb/applications/${id}/`)
  },
  organization() {
    return api.get<OrgTreeNode[]>('/cmdb/graph/organization/')
  },
  application(id: number) {
    return api.get<GraphData>(`/cmdb/graph/applications/${id}/`)
  },
  applicationEnvs(appId: number) {
    return api.get<Environment[]>(`/cmdb/applications/${appId}/environments/`)
  },
  environment(id: number) {
    return api.get<GraphData>(`/cmdb/graph/environments/${id}/`)
  },
  envDetail(id: number) {
    return api.get<Environment>(`/cmdb/environments/${id}/`)
  },
  envServices(id: number) {
    return api.get(`/cmdb/environments/${id}/services/`)
  },
  envEndpoints(id: number) {
    return api.get(`/cmdb/environments/${id}/endpoints/`)
  },
  appServices(appId: number) {
    return api.get(`/cmdb/applications/${appId}/services/`)
  },
  appEndpoints(appId: number) {
    return api.get(`/cmdb/applications/${appId}/endpoints/`)
  },
  pendingChanges(envId: number) {
    return api.get<any[]>('/cmdb/graph/pending-changes/', { params: { environment_id: envId } })
  },
  neighbors(resourceId: number, depth = 1) {
    return api.get<GraphData>(`/cmdb/graph/resources/${resourceId}/neighbors/`, { params: { depth } })
  },
  impact(resourceId: number) {
    return api.get<ImpactResult>(`/cmdb/graph/resources/${resourceId}/impact/`)
  },
  path(sourceId: number, targetId: number) {
    return api.get<GraphData & { reachable: boolean }>(`/cmdb/graph/resources/${sourceId}/path/`, { params: { target: targetId } })
  },
  connectivity(sourceId: number, targetId: number) {
    return api.get<{ reachable: boolean; verdict: string; reason: string }>(
      `/cmdb/graph/resources/${sourceId}/connectivity/`,
      { params: { target: targetId } },
    )
  },
  relationChanges(data: {
    title: string
    application_id?: number
    environment_id?: number
    changes: Record<string, any>[]
  }) {
    return api.post<{ message: string; ticket_id: number; ticket_no: string }>(
      '/cmdb/graph/relation-changes/',
      data,
    )
  },
}

// ===== 场景编排 =====
export const scenarioApi = {
  list(params?: any) {
    return api.get<PaginatedResponse<Scenario>>('/scenario/scenarios/', { params })
  },
  get(id: number) {
    return api.get<Scenario>(`/scenario/scenarios/${id}/`)
  },
  apply(id: number, data: { title: string; request_content: Record<string, any> }) {
    return api.post<{ message: string; ticket_id: number; ticket_no: string }>(
      `/scenario/scenarios/${id}/apply/`,
      data,
    )
  },
}

// ===== 同步服务 =====
export const syncApi = {
  jobs() {
    return api.get<SyncJob[]>('/cmdb/sync-jobs/')
  },
  runManual() {
    return api.post<SyncJob>('/cmdb/sync-jobs/', { job_type: 'manual' })
  },
}

// ===== 系统知识库 =====
export interface DocCategoryNode {
  id: number
  code: string
  name: string
  icon: string
  sort: number
  doc_count: number
  docs: DocSummary[]
}

export interface DocSummary {
  id: number
  slug: string
  title: string
  summary: string
  tags: string
  category: number
  category_name: string
  sort: number
  updated_at: string
}

export interface DocDetail extends DocSummary {
  html_content: string
}

export const knowledgeApi = {
  /** 文档目录（分类 + 每类文档摘要） */
  categories() {
    return api.get<PaginatedResponse<DocCategoryNode>>('/knowledge/categories/')
  },
  /** 文档摘要列表（可按 category 过滤） */
  docs(params?: { category?: number }) {
    return api.get<PaginatedResponse<DocSummary>>('/knowledge/docs/', { params })
  },
  /** 文档详情（含 HTML 正文） */
  detail(slug: string) {
    return api.get<DocDetail>(`/knowledge/docs/${slug}/`)
  },
}
