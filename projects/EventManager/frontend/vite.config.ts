import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://api.event-management.orb.local',
        changeOrigin: true,
      },
      '/go-api': {
        target: 'http://api.go-event-management.orb.local',
        changeOrigin: true,
      },
    },
  },
})
