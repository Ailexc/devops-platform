import request from '../request'

// 登录（获取 JWT token）
export function login(data) {
  return request.post('/auth/token/', data)
}

// 刷新 token
export function refreshToken(data) {
  return request.post('/auth/token/refresh/', data)
}

// 获取当前用户信息
export function getProfile() {
  return request.get('/users/me/')
}

// 更新用户信息
export function updateProfile(data) {
  return request.patch('/users/me/', data)
}

// 获取快速登录用户列表
export function getQuickLoginUsers() {
  return request.get('/users/quick-login-list/')
}

// 快速登录
export function quickLogin(data) {
  return request.post('/users/quick-login/', data)
}
