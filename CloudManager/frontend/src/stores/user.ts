import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const initialized = ref(false)  // 是否已完成初始化（从网关会话恢复）
  // 基于 user 对象判断登录态（网关会话模式下 localStorage 无 token）
  const isLoggedIn = ref(false)

  async function login(username: string, password: string) {
    const { data } = await authApi.login({ username, password })
    token.value = data.access
    user.value = data.user
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_info', JSON.stringify(data.user))
    isLoggedIn.value = true
    return data
  }

  // 获取用户信息（网关会话 Cookie 自动携带，不依赖 localStorage token）
  async function fetchProfile() {
    try {
      const { data } = await authApi.getProfile()
      user.value = data
      isLoggedIn.value = true
      localStorage.setItem('user_info', JSON.stringify(data))
    } catch {
      user.value = null
      isLoggedIn.value = false
    } finally {
      initialized.value = true
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    isLoggedIn.value = false
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  function hasPermission(code: string): boolean {
    if (!user.value) return false
    if (user.value.username === 'admin') return true
    if (user.value.roles?.some((r) => r.code === 'super_admin')) return true
    return user.value.permissions?.includes(code) || false
  }

  return { user, token, initialized, isLoggedIn, login, fetchProfile, logout, hasPermission }
})
