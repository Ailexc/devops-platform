import { LoadingOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { portalApi } from '../api/client'
import { useAuthStore } from '../store/auth'

export default function LoginPage() {
  const nav = useNavigate()

  useEffect(() => {
    // 1. 检查是否已有 OIDC 会话（HttpOnly Cookie）
    portalApi
      .me()
      .then(({ data }) => {
        useAuthStore.getState().setUser(data)
        nav('/', { replace: true })
      })
      .catch(() => {
        // 2. 无会话 → 直接跳 OIDC 授权端点（不显示中间按钮）
        window.location.href = '/portal/oauth/login'
      })
  }, [nav])

  // 跳转前短暂 Loading（防白屏闪烁）
  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-logo">
          <SafetyCertificateOutlined />
        </div>
        <h1 className="login-title">统一认证中心</h1>
        <p className="login-subtitle">DevOps Platform · 单点登录（SSO）统一入口</p>
        <div style={{ textAlign: 'center', color: '#667085', padding: '24px 0' }}>
          <LoadingOutlined style={{ fontSize: 20 }} />
          <div style={{ marginTop: 10, fontSize: 13 }}>正在跳转到认证中心…</div>
        </div>
        <noscript>
          <p style={{ textAlign: 'center' }}>
            <a href="/portal/oauth/login">点击此处手动跳转登录</a>
          </p>
        </noscript>
      </div>
    </div>
  )
}
