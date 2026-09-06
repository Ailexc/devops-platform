import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

// 全局样式
import './assets/global-styles.css'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'

// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 前端无需任何 token 消费逻辑，直接调 API 即可
// 若 API 返回 401，说明网关会话未建立/已过期，跳转门户登录

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(Antd)

  // 尝试拉取当前用户（网关会话 Cookie 自动携带）
  const userStore = useUserStore()
  try {
    await userStore.fetchProfile()
  } catch {
    /* 401 → 由请求拦截器跳转门户登录 */
  }

  app.mount('#app')
}

void bootstrap()
