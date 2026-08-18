// 通用类型定义

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T = any> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface User {
  id: number
  username: string
  display_name: string
  email: string
  phone: string
  department: number | null
  department_name: string
  roles: Role[]
  permissions: string[]
  is_active: boolean
  date_joined: string
}

export interface Role {
  id: number
  name: string
  code: string
  description: string
  is_active: boolean
  permissions?: Permission[]
}

export interface Permission {
  id: number
  name: string
  code: string
  module: string
  description: string
}

export interface Department {
  id: number
  name: string
  parent: number | null
  sort_order: number
  created_at: string
}

export interface CloudAccount {
  id: number
  account_name: string
  provider_type: string
  provider_display: string
  regions: string
  status: number
  status_display: string
  sync_status: number
  last_sync_time: string | null
  created_at: string
  updated_at: string
}

export interface Resource {
  id: number
  account: number
  account_name: string
  provider_type: string
  resource_type: string
  resource_type_display: string
  resource_name: string
  cloud_resource_id: string
  region: string
  zone: string
  status: string
  spec: string
  department: number | null
  application: number | null
  environment: number | null
  environment_name: string
  metadata: Record<string, any>
  source: number
  managed_by: string
  managed_by_display: string
  source_system: string
  sync_mode: string
  external_id: string
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface TicketOrder {
  id: number
  ticket_no: string
  ticket_type: string
  ticket_type_display: string
  title: string
  status: string
  status_display: string
  applicant: string
  applicant_id: number
  approver: string
  resource_id: string
  resource_name: string
  provider_type: string
  request_content: Record<string, any>
  result_content: Record<string, any>
  fail_reason: string
  created_at: string
  updated_at: string
  finished_at: string | null
}

export interface TicketApproval {
  id: number
  ticket: number
  approver: string
  approver_id: number
  action: number
  action_display: string
  comment: string
  approved_at: string
}

export interface TicketTask {
  id: number
  ticket: number
  task_type: string
  provider_type: string
  status: string
  status_display: string
  retry_count: number
  max_retry: number
  request_id: string
  exec_log: string
  started_at: string | null
  finished_at: string | null
}

export interface ResourceStats {
  resource_type: string
  status: string
  count: number
}

// ===== 图谱 =====
export interface GraphNode {
  id: string
  name: string
  category: string
  meta?: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  relation_type: string
  strength: string
  label?: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface AppSummary {
  id: number
  name: string
  department: string
  owner: string
  description: string
  services_count: number
  environments_count: number
  resources_count: number
  relations_count: number
}

export interface Environment {
  id: number
  application: number
  application_name: string
  name: string
  env_type: string
  env_type_display: string
  account: number | null
  account_name: string
  region: string
  description: string
  enabled: boolean
  services_count: number
  created_at: string
  updated_at: string
}

export interface OrgApp {
  id: number
  name: string
  owner: string
  environments_count: number
}

export interface OrgTreeNode {
  id: number
  name: string
  applications: OrgApp[]
  children: OrgTreeNode[]
}

export interface AppDetail {
  id: number
  name: string
  department: number | null
  department_name: string
  owner: string
  description: string
  app_code: string
  app_name_en: string
  cmdb_ci_id: string
  business_line: string
  app_category: string
  app_category_display: string
  dev_owner: string
  ops_owner: string
  alert_group: string
  creator: string
  language: string
  framework: string
  app_type: string
  app_type_display: string
  git_repo: string
  default_branch: string
  artifact_repo: string
  ci_pipeline: string
  deploy_type: string
  deploy_type_display: string
  default_cluster: string
  importance_level: string
  importance_level_display: string
  sla: string
  dr_level: string
  change_policy: string
  change_policy_display: string
  domain: string
  tags: string[]
  doc_url: string
  created_at: string
  updated_at: string
}

export interface ImpactNode {
  id: string
  resource_id: number
  name: string
  category: string
  resource_type: string
  status: string
  relation_type: string
  strength: string
  severity: string
  depth: number
  path: number[]
}

export interface ImpactResult {
  root: { id: string; name: string; resource_type: string }
  summary: { high: number; medium: number; low: number; spof: string[] }
  nodes: ImpactNode[]
}

// ===== 场景 =====
export interface ScenarioStep {
  id: number
  step_no: number
  name: string
  action_type: string
  action_params_template: Record<string, any>
  depends_on: number[]
  need_approval: boolean
  retry_max: number
  rollback_action_type: string
  enabled: boolean
}

export interface Scenario {
  id: number
  code: string
  name: string
  description: string
  icon: string
  need_approval: boolean
  enabled: boolean
  version: string
  step_count: number
  steps: ScenarioStep[]
  created_at: string
  updated_at: string
}

// ===== 同步任务 =====
export interface SyncJob {
  id: number
  job_type: string
  job_type_display: string
  status: string
  status_display: string
  source_system: string
  total_count: number
  message: string
  created_at: string
  finished_at: string | null
}

// ===== 服务/端点 =====
export interface ServiceInstance {
  id: number
  application: number
  application_name: string
  name: string
  service_type: string
  service_type_display: string
  deploy_type: string
  deploy_type_display: string
  region: string
  status: string
  owner: string
  description: string
}

export interface ServiceEndpoint {
  id: number
  service: number
  service_name: string
  protocol: string
  port: number
  domain: string
  certificate: string
  is_public: boolean
  metadata: Record<string, any>
}

// ===== 成本优化 =====
export interface OptimizationRule {
  id: number
  name: string
  rule_type: string
  rule_type_display: string
  severity: string
  severity_display: string
  description: string
  scope: { cloud: string; account: string; region: string; resource_type: string }
  conditions: Record<string, any>
  title_template: string
  description_template: string
  saving_config: { type: string; amount?: number; percent?: number }
  is_enabled: boolean
  priority: number
  created_at: string
  updated_at: string
}

export interface OptimizationSuggestion {
  id: number
  report: number | null
  rule: number | null
  rule_name: string
  resource: number | null
  resource_name: string
  resource_id: string
  account: number | null
  account_name: string
  provider_type: string
  region: string
  resource_type: string
  suggestion_type: string
  suggestion_type_display: string
  severity: string
  severity_display: string
  title: string
  description: string
  estimated_saving: string
  is_resolved: boolean
  created_at: string
}

export interface OptimizationReport {
  id: number
  report_no: string
  title: string
  operator: string
  trigger: string
  trigger_display: string
  summary: {
    total_rules: number
    total_matched: number
    total_saving: number
    cloud_count: number
  }
  tree_snapshot: Record<string, any>
  items_snapshot: Record<string, any>[]
  executed_at: string
  cloud_count: number
  total_rules: number
  total_matched: number
  total_saving: number
}

export interface RuleExecutionLog {
  id: number
  rule: number
  rule_name: string
  scope_snapshot: Record<string, any>
  matched_count: number
  created_count: number
  execution_time_ms: number
  executed_at: string
}

export interface CostOverview {
  stats: {
    pending: number
    total: number
    total_saving: number
    resolved: number
    cloud_count: number
  }
  by_cloud: { provider_type: string; total: number; cnt: number }[]
  by_type: { suggestion_type: string; cnt: number; total: number }[]
  by_region: { region: string; total: number }[]
  trend: { label: string; saving: number }[]
  suggestions: OptimizationSuggestion[]
}
