import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import App from './App.vue'
import router from './router'

// Initialize theme before mount to prevent flash
import { useThemeStore } from './stores/theme'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// Initialize theme store
useThemeStore()

app.mount('#app')
