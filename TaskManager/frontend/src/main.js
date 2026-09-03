import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { fetchCurrentUser } from './api/index.js'

// SSO 统一令牌消费：门户（统一认证中心）跳转带 ?token=<统一 JWT>
// 本系统走方式二（直连 JWKS 验签）：前端保存令牌，请求携带 Bearer，后端本地验签
async function bootstrap() {
  const ssoToken = new URLSearchParams(window.location.search).get('token')
  if (ssoToken) {
    localStorage.setItem('cmdb.token', ssoToken)
    // 立即清理地址栏令牌（JWT 不应留在 URL 历史中）
    window.history.replaceState({}, '', window.location.pathname)
    // 预拉当前用户（供 header 显示）；失败则静默（进入页面后再尝试）
    try {
      await fetchCurrentUser()
    } catch {
      /* 令牌无效等场景忽略，页面仍可浏览 */
    }
  }

  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}

void bootstrap()
