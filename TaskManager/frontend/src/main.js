import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { fetchCurrentUser } from './api/index.js'

// SSO 安全跳转：门户 ?code=xxx → 一次性授权码兑换 JWT（Token 不进 URL）
// 本系统走方式二（直连 JWKS 验签）：后端用 code 换 JWT，前端只持有 localStorage
const ONETIME_CODE = new URLSearchParams(window.location.search).get('code')

async function bootstrap() {
  if (ONETIME_CODE) {
    try {
      // 用一次性授权码向认证中心兑换 JWT（后端完成，Token 不进浏览器 URL）
      const resp = await fetch('/api/auth/redeem-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: ONETIME_CODE }),
      })
      if (resp.ok) {
        const { access_token } = await resp.json()
        localStorage.setItem('cmdb.token', access_token)
      }
    } catch {
      /* 兑换失败静默处理 */
    }
    // 清理地址栏 code 参数
    window.history.replaceState({}, '', window.location.pathname)
    // 预拉当前用户（供 header 显示）
    try {
      await fetchCurrentUser()
    } catch {
      /* 静默 */
    }
  }

  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}

void bootstrap()
