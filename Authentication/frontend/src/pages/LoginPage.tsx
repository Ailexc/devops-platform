import { LoadingOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { portalApi } from '../api/client'
import { useAuthStore } from '../store/auth'

export default function LoginPage() {
  const nav = useNavigate()
  const [checking, setChecking] = useState(true)

  // 若已有 OIDC 会话（HttpOnly Cookie），直接恢复登录态回首页
  useEffect(() => {
    let mounted = true
    portalApi
      .me()
      .then(({ data }) => {
        if (!mounted) return
        useAuthStore.getState().setUser(data)
        nav('/', { replace: true })
      })
      .catch(() => {
        if (mounted) setChecking(false)
      })
    return () => {
      mounted = false
    }
  }, [nav])

  const goLogin = () => {
    // 门户作为 OIDC 客户端发起授权码流（BFF：/portal/oauth/login → 认证中心 /oauth/authorize）
    window.location.href = '/portal/oauth/login'
  }

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-logo">
          <SafetyCertificateOutlined />
        </div>
        <h1 className="login-title">统一认证中心</h1>
        <p className="login-subtitle">DevOps Platform · 单点登录（SSO）统一入口</p>
        {checking ? (
          <div style={{ textAlign: 'center', color: '#667085', padding: '24px 0' }}>
            <LoadingOutlined style={{ fontSize: 20 }} />
            <div style={{ marginTop: 10, fontSize: 13 }}>正在检查登录状态…</div>
          </div>
        ) : (
          <Button type="primary" size="large" block onClick={goLogin} style={{ marginTop: 8 }}>
            前往统一认证中心登录
          </Button>
        )}
        {!checking && (
          <p className="login-subtitle" style={{ marginTop: 12, fontSize: 12 }}>
            将跳转到 OIDC 授权端点（OAuth 2.1 Authorization Code + PKCE）
          </p>
        )}
        <div className="login-footer">
          演示账号：admin / demo1234（管理员）<br />
          zhangsan / demo1234（普通用户）
        </div>
      </div>
    </div>
  )
}
