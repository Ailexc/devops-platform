import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发代理：/api 与 /v1 转发到 iam-server（默认 :8080，可用 IAM_API 覆盖，便于本地多实例验证）
const target = process.env.IAM_API || 'http://localhost:8080'
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/v1': { target, changeOrigin: true },
    },
  },
})
