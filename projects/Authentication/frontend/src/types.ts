export interface User {
  id: number
  username: string
  display_name: string
  email: string
  department: string
  phone: string
  is_active: boolean
  is_admin: boolean
  source: string
}

export interface AppInfo {
  id: number
  app_id: string
  name: string
  description: string
  icon: string
  home_url: string
  sso_type: string
  access_mode: string
  client_id?: string
  enabled: boolean
  sort_order: number
}

// 新增应用入参
export interface AppPayload {
  app_id?: string
  name: string
  description?: string
  icon?: string
  home_url?: string
  sso_type?: string
  access_mode?: string
  enabled?: boolean
  sort_order?: number
}

// 创建响应：client_secret 一次性返回
export interface AppCreateResult extends AppInfo {
  client_secret?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// ===== 系统文档（后端 /system-docs 提供）=====
export interface SystemDocCategory {
  id: string
  name: string
  color: string
}

export interface SystemDocItem {
  id: string
  title: string
  description: string
  category: string
  icon: string
  color: string
  order: number
  file: string
}

export interface SystemDocsIndex {
  categories: SystemDocCategory[]
  docs: SystemDocItem[]
}

