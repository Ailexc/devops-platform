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

// 方式一（网关会话）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 前端无需任何 token 消费逻辑，直接调 API 即可
// 若 API 返回 401，说明网关会话未建立/已过期，跳转门户登录

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

  // 尝试拉取当前用户（网关会话 Cookie 自动携带）
  const authStore = useAuthStore()
  try {
    await authStore.fetchUser()
  } catch {
    /* 401 → 由请求拦截器跳转门户登录 */
  }

  app.mount('#app')
}

void bootstrap()
