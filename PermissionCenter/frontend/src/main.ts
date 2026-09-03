import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import App from './App.vue'
import router from './router'

// Initialize theme before mount to prevent flash
import { useThemeStore } from './stores/theme'
import { api } from './api/client'

// SSO 统一令牌消费：门户（统一认证中心）跳转带 ?token=<统一 JWT>
// 前端把统一令牌写入 localStorage 'iam_token'，后续请求由 API client 携带
async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)

  // Initialize theme store
  useThemeStore()

  // 本次会话携带 SSO 令牌时，写入统一令牌并拉取当前用户信息
  const ssoToken = new URLSearchParams(window.location.search).get('token')
  if (ssoToken) {
    localStorage.setItem('iam_token', ssoToken)
    window.history.replaceState({}, '', window.location.pathname)
    try {
      const me = await api.me()
      localStorage.setItem('iam_user', JSON.stringify(me))
    } catch {
      /* 拉取失败（token 无效等）则留在登录页 */
    }
  }

  // 清理地址栏残留的 SSO 令牌（JWT 不应留在 URL 历史中）
  router.afterEach(() => {
    if (window.location.search.includes('token=')) {
      window.history.replaceState({}, '', window.location.pathname + window.location.hash)
    }
  })

  app.mount('#app')
}

void bootstrap()
