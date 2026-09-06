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

// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 前端无需任何 token 消费逻辑，直接调 API 即可
// 若 API 返回 401，说明网关会话未建立/已过期，跳转门户登录

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)

  // Initialize theme store
  useThemeStore()

  // 尝试拉取当前用户（网关会话 Cookie 自动携带）
  try {
    const me = await api.me()
    localStorage.setItem('iam_user', JSON.stringify(me))
  } catch {
    /* 401 → 由请求拦截器跳转门户登录 */
  }

  app.mount('#app')
}

void bootstrap()
