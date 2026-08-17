import { LockOutlined, SafetyCertificateOutlined, UserOutlined } from '@ant-design/icons'
import { App as AntApp, Button, Form, Input } from 'antd'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'

interface LoginForm {
  username: string
  password: string
}

export default function LoginPage() {
  const nav = useNavigate()
  const [searchParams] = useSearchParams()
  const { message } = AntApp.useApp()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: LoginForm) => {
    setLoading(true)
    try {
      const { data } = await authApi.login(values.username, values.password)
      useAuthStore.getState().setAuth(data.access_token, data.refresh_token, data.user)
      message.success(`欢迎回来，${data.user.display_name || data.user.username}`)
      // OIDC/SSO 回跳：登录成功后携带统一 JWT 跳回原 authorize 地址
      const ret = searchParams.get('return')
      if (ret) {
        const sep = ret.includes('?') ? '&' : '?'
        window.location.href = `${ret}${sep}token=${encodeURIComponent(data.access_token)}`
        return
      }
      nav('/', { replace: true })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      message.error(detail || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-logo">
          <SafetyCertificateOutlined />
        </div>
        <h1 className="login-title">统一认证中心</h1>
        <p className="login-subtitle">DevOps Platform · 单点登录（SSO）统一入口</p>
        <Form<LoginForm> onFinish={onFinish} size="large" autoComplete="off">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登 录
            </Button>
          </Form.Item>
        </Form>
        <div className="login-footer">
          演示账号：admin / admin1234（管理员）<br />
          zhangsan / demo1234（普通用户）
        </div>
      </div>
    </div>
  )
}
