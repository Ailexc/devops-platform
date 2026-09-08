import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发模式：/api 代理到本地认证中心后端
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8010'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5174, // 避开 5173（可能被其他本地应用占用）
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/.well-known': { target: API_TARGET, changeOrigin: true },
    },
  },
})
