import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import formCreate from '@form-create/element-ui'
import FcDesigner from '@form-create/designer'
import App from './App.vue'
import router from './router'
import './styles/global.scss'
import focus from './directive/focus'
import { useAuthStore } from './stores/auth'

// SSO 统一令牌消费：门户（统一认证中心）跳转带 ?token=<统一 JWT>
// 前端把统一令牌写入 auth store（localStorage 'token'），后续 /api/v1 请求由拦截器携带
function getSSOToken() {
  try {
    return new URLSearchParams(window.location.search).get('token')
  } catch {
    return null
  }
}

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus, { locale: zhCn })

  // 注册 Arco Design Vue（Beeflow 流程设计器 UI 库）
  app.use(ArcoVue)

  // 注册自定义指令
  app.directive('focus', focus)

  // 注册 form-create 渲染器
  app.use(formCreate)

  // 注册 form-create-designer
  app.use(FcDesigner)

  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // 本次会话携带 SSO 令牌时，写入统一令牌并拉取当前用户
  const ssoToken = getSSOToken()
  if (ssoToken) {
    const authStore = useAuthStore()
    authStore.setToken(ssoToken)
    // 立即清理地址栏令牌（JWT 不应留在 URL 历史中）
    window.history.replaceState({}, '', window.location.pathname)
    try {
      await authStore.fetchUser()
    } catch {
      /* 拉取失败（token 无效等）则留在登录页 */
    }
  }

  // 兜底：路由跳转后若地址栏仍残留 token，再次清理
  router.afterEach(() => {
    if (window.location.search.includes('token=')) {
      window.history.replaceState({}, '', window.location.pathname + window.location.hash)
    }
  })

  app.mount('#app')
}

void bootstrap()
