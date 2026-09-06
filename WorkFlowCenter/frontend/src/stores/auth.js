import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getProfile, quickLogin as quickLoginApi } from '@/api/modules/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const initialized = ref(false)  // 是否已完成初始化（从网关会话恢复）
  
  // 计算属性：基于 user 对象判断（网关会话模式下 localStorage 无 token）
  const isAuthenticated = computed(() => !!user.value)
  
  // 设置 token（方式二/三链路用，方式一不需要）
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }
  
  // 登录（本地登录页用）
  async function login(username, password) {
    try {
      const response = await loginApi({ username, password })
      const { access, refresh: refreshToken } = response.data || response
      setToken(access)
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
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

  // 获取用户信息（网关会话 Cookie 自动携带，不依赖 localStorage token）
  async function fetchUser() {
    try {
      const response = await getProfile()
      user.value = response?.data ?? response
      initialized.value = true
      return true
    } catch (error) {
      user.value = null
      initialized.value = true
      return false
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
    initialized,
    isAuthenticated,
    setToken,
    login,
    quickLogin,
    logout,
    fetchUser
  }
})