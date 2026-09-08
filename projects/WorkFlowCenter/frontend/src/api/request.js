import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  // AI 表单生成等接口响应较慢（MiMo 推理可能需 1-3 分钟），超时放宽到 180s
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 请求拦截器无需注入 Authorization 头，浏览器自动带 Cookie
request.interceptors.request.use(
  (config) => {
    // Django APPEND_SLASH 对 POST/PUT/PATCH/DELETE 无尾斜杠请求会抛 500，
    // 这里为非 GET 请求统一补充尾斜杠（保留 query string）
    const method = (config.method || 'get').toLowerCase()
    if (method !== 'get' && config.url && !config.url.endsWith('/')) {
      const [path, query] = config.url.split('?')
      config.url = path + '/' + (query ? `?${query}` : '')
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 网关会话已过期/未建立 → 跳转门户登录
          localStorage.removeItem('token')
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = `${window.location.protocol}//${window.location.hostname}:8088/login`
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          ElMessage.error(data.detail || '请求参数错误')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
