import axios from 'axios'
import { useAuthStore } from '../store/auth'
import type { AppCreateResult, AppInfo, AppPayload, LoginResponse, SystemDocsIndex, User } from '../types'

// 门户 SPA 不再持有 token：OIDC 登录后，后端 BFF（/portal/*）持有 token，
// 浏览器仅保存 HttpOnly Cookie（portal_session）。所有 /api、/portal/api 请求同源自动携带 cookie。
export const api = axios.create({ baseURL: '/api' })

// 请求拦截：无 token 可附加；身份由 HttpOnly Cookie 会话保证（BFF 模式）
api.interceptors.request.use((config) => config)

// 响应拦截：401 → 重新发起 OIDC 登录
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().setUser(null)
      const path = window.location.pathname
      if (path !== '/login' && !path.startsWith('/portal/oauth')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

// 内部兼容链路（自研 SSO 模拟，供 E2E 演示 / 遗留应用接入，非 OIDC 标准路径）
export const authApi = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { username, password }),
  me: () => api.get<User>('/auth/me'),
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  ssoUrl: (appId: string) =>
    api.get<{ url: string; app: string }>('/auth/sso-url', { params: { app_id: appId } }),
}

// 门户 BFF（OIDC 客户端后端）：当前用户 / 登出。
// 注意：BFF 路由是 /portal/*（不走 /api 前缀），需独立实例，否则会打到 /api/portal/* 404。
const portal = axios.create({ baseURL: '' })

portal.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().setUser(null)
      const path = window.location.pathname
      if (path !== '/login' && !path.startsWith('/portal/oauth')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export const portalApi = {
  me: () => portal.get<User>('/portal/api/me'),
  logout: () => portal.post('/portal/api/logout'),
}

// 系统文档（HTML 文档库，后端 /system-docs 提供）：清单 + 文档内容
const sysDocs = axios.create({ baseURL: '' })

export const systemDocsApi = {
  index: () => sysDocs.get<SystemDocsIndex>('/system-docs/index.json'),
  doc: (id: string) => sysDocs.get<string>(`/system-docs/${id}`, { responseType: 'text' }),
}

export const appApi = {
  list: () => api.get<AppInfo[]>('/apps'),
  manage: () => api.get<AppInfo[]>('/apps/manage'),
  create: (payload: AppPayload) => api.post<AppCreateResult>('/apps', payload),
  update: (appId: string, payload: Partial<AppPayload>) =>
    api.put<AppInfo>(`/apps/${appId}`, payload),
  remove: (appId: string) => api.delete(`/apps/${appId}`),
}
