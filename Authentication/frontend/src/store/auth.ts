import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import { portalApi } from '../api/client'

// 登录态：门户 BFF 模式 —— token 不落浏览器，只有 user 快照缓存（显示用，不承载鉴权）。
// 鉴权依据是后端 HttpOnly Cookie 会话（portal_session），由 /portal/api/me 恢复。
interface AuthState {
  user: User | null
  initialized: boolean
  setUser: (user: User | null) => void
  setInitialized: (v: boolean) => void
  // 启动时从 BFF 会话恢复当前用户
  bootstrap: () => Promise<boolean>
  // 登出：清门户会话 + IdP 会话（调用方负责跳转 /oauth/logout）
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      initialized: false,
      setUser: (user) => set({ user }),
      setInitialized: (initialized) => set({ initialized }),
      bootstrap: async () => {
        try {
          const { data } = await portalApi.me()
          set({ user: data, initialized: true })
          return true
        } catch {
          set({ user: null, initialized: true })
          return false
        }
      },
      logout: async () => {
        try {
          await portalApi.logout()
        } catch {
          /* 忽略：客户端清理即可 */
        }
        set({ user: null })
      },
    }),
    {
      name: 'auth-portal',
      // 只持久化 user 快照（用于刷新后立即显示），initialized 每次启动重新判定
      partialize: (s) => ({ user: s.user }),
    },
  ),
)
