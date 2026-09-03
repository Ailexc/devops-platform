import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

// 全局样式
import './assets/global-styles.css'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'

// SSO 统一令牌消费：门户（统一认证中心）跳转带 ?token=<统一 JWT>
// 前端把统一令牌写入 localStorage，后续所有 /api/ 请求由请求拦截器携带
// （API 流量经统一网关 forwardAuth，后端信任 X-Auth-* 头识别用户）
function consumeSSOToken() {
  try {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      localStorage.setItem('access_token', token)
      // 从地址栏清除令牌，避免留在 URL 历史中
      window.history.replaceState({}, '', window.location.pathname)
      return true
    }
  } catch {
    /* ignore */
  }
  return false
}

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(Antd)

  // 本次会话携带 SSO 令牌时，拉取当前用户信息（首次进入显示门户登录的用户）
  const consumed = consumeSSOToken()
  if (consumed) {
    const userStore = useUserStore()
    try {
      await userStore.fetchProfile()
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
