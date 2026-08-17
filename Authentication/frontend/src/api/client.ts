import axios from 'axios'
import { useAuthStore } from '../store/auth'
import type { AppCreateResult, AppInfo, AppPayload, LoginResponse, User } from '../types'

export const api = axios.create({ baseURL: '/api' })

// 请求拦截：自动携带 access_token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 统一登出并回登录页
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export const authApi = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { username, password }),
  me: () => api.get<User>('/auth/me'),
  logout: (refreshToken: string) => api.post('/auth/logout', { refresh_token: refreshToken }),
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  ssoUrl: (appId: string) =>
    api.get<{ url: string; app: string }>('/auth/sso-url', { params: { app_id: appId } }),
}

export const appApi = {
  list: () => api.get<AppInfo[]>('/apps'),
  manage: () => api.get<AppInfo[]>('/apps/manage'),
  create: (payload: AppPayload) => api.post<AppCreateResult>('/apps', payload),
  update: (appId: string, payload: Partial<AppPayload>) =>
    api.put<AppInfo>(`/apps/${appId}`, payload),
  remove: (appId: string) => api.delete(`/apps/${appId}`),
}
