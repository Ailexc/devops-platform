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

const app = createApp(App)
app.use(createPinia())
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

app.mount('#app')
