import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// SSO 统一令牌消费：门户（统一认证中心）跳转带 ?token=<统一 JWT>
// 本系统走方式二（直连 JWKS 验签）：前端保存令牌，请求携带 Bearer，后端本地验签
const ssoToken = new URLSearchParams(window.location.search).get('token')
if (ssoToken) {
  localStorage.setItem('event.token', ssoToken)
  // 立即清理地址栏令牌（JWT 不应留在 URL 历史中）
  window.history.replaceState({}, '', window.location.pathname)
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
