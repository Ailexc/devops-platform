import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// SSO 安全跳转：门户 ?code=xxx → 一次性授权码兑换 JWT（Token 不进 URL）
// 本系统走方式二（直连 JWKS 验签）：后端用 code 换 JWT，前端只持有 localStorage
const ONETIME_CODE = new URLSearchParams(window.location.search).get('code')
if (ONETIME_CODE) {
  const AUTH_API = `${window.location.protocol}//${window.location.hostname}:8099`
  fetch(`${AUTH_API}/api/auth/redeem-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: ONETIME_CODE }),
  })
    .then((r) => (r.ok ? r.json() : Promise.reject()))
    .then(({ access_token }) => {
      localStorage.setItem('event.token', access_token)
    })
    .catch(() => { /* 兑换失败静默处理 */ })
    .finally(() => {
      // 清理地址栏 code 参数
      window.history.replaceState({}, '', window.location.pathname)
    })
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 2,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
