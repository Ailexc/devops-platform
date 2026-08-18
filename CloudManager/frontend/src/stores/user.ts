import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const isLoggedIn = ref(!!localStorage.getItem('access_token'))

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

  async function fetchProfile() {
    try {
      const { data } = await authApi.getProfile()
      user.value = data
      localStorage.setItem('user_info', JSON.stringify(data))
    } catch {
      logout()
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
    // Demo 模式：admin 用户拥有所有权限
    if (user.value.username === 'admin') return true
    if (user.value.roles?.some((r) => r.code === 'super_admin')) return true
    return user.value.permissions?.includes(code) || false
  }

  // 初始化时从 localStorage 恢复用户信息
  const storedUser = localStorage.getItem('user_info')
  if (storedUser && isLoggedIn.value) {
    try {
      user.value = JSON.parse(storedUser)
    } catch {
      logout()
    }
  }

  return { user, token, isLoggedIn, login, fetchProfile, logout, hasPermission }
})
