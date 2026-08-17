import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getProfile, quickLogin as quickLoginApi } from '@/api/modules/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  
  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  
  // 设置 token
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }
  
  // 登录
  async function login(username, password) {
    try {
      const response = await loginApi({ username, password })
      // JWT 返回 { access, refresh }
      const { access, refresh: refreshToken } = response.data || response
      setToken(access)
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
      // 登录成功后获取用户信息
      await fetchUser()
      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      return { success: false, error: error.response?.data?.detail || error.message }
    }
  }
  

  // 快速登录
  async function quickLogin(userId) {
    try {
      const response = await quickLoginApi({ user_id: userId })
      const { access, refresh: refreshToken } = response.data || response
      setToken(access)
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
      await fetchUser()
      return { success: true }
    } catch (error) {
      console.error('快速登录失败:', error)
      return { success: false, error: error.response?.data?.detail || error.message }
    }
  }

  // 获取用户信息
  async function fetchUser() {
    if (!token.value) return

    try {
      const response = await getProfile()
      user.value = response?.data ?? response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果 token 无效，清除登录状态
      if (error.response?.status === 401) {
        logout()
      }
    }
  }
  
  // 登出
  function logout() {
    setToken('')
    user.value = null
    router.push('/login')
  }
  
  return {
    token,
    user,
    isAuthenticated,
    setToken,
    login,
    quickLogin,
    logout,
    fetchUser
  }
})