import axios from 'axios'
import { message } from 'ant-design-vue'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 请求拦截器无需注入 Authorization 头，浏览器自动带 Cookie
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error),
)

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          // 网关会话已过期/未建立 → 跳转门户登录
          message.error('登录已过期，请重新登录')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          window.location.href = `${window.location.protocol}//${window.location.hostname}:8088/login`
          break
        case 403:
          message.error('没有权限执行此操作')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data?.detail || data?.message || '请求失败')
      }
    } else {
      message.error('网络连接失败')
    }
    return Promise.reject(error)
  },
)

export default api
