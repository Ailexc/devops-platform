import {
  AppstoreOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { App as AntApp, Avatar, Dropdown, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

export default function AppHeader() {
  const nav = useNavigate()
  const { message } = AntApp.useApp()
  const user = useAuthStore((s) => s.user)

  const handleLogout = async () => {
    // 1. 清门户 BFF 会话（HttpOnly Cookie）
    await useAuthStore.getState().logout()
    message.success('已退出登录')
    // 2. 跳 OIDC end_session 端点，清 IdP 会话（RP-initiated logout）
    const back = encodeURIComponent(`${window.location.origin}/login`)
    window.location.href = `/oauth/logout?post_logout_redirect_uri=${back}`
  }

  const isAdmin = user?.is_admin
  const items = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心' },
    ...(isAdmin
      ? [{ key: 'admin-apps', icon: <AppstoreOutlined />, label: '应用管理' }]
      : []),
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  return (
    <header className="portal-header">
      <div className="portal-header-inner">
        <div
          className="portal-brand"
          onClick={() => nav('/')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && nav('/')}
        >
          <SafetyCertificateOutlined />
          <span>DevOps Platform · 统一门户</span>
        </div>
        <div className="portal-header-nav">
          <span onClick={() => nav('/presentation')}>系统宣讲</span>
          <span onClick={() => nav('/docs')}>系统文档</span>
          <span onClick={() => nav('/dev/e2e-test')}>测试流程</span>
        </div>
        <Dropdown
          menu={{
            items,
            onClick: ({ key }) => {
              if (key === 'profile') nav('/profile')
              if (key === 'admin-apps') nav('/admin/apps')
              if (key === 'logout') handleLogout()
            },
          }}
          placement="bottomRight"
        >
          <Space style={{ cursor: 'pointer', color: '#fff' }}>
            <Avatar
              size="small"
              style={{ background: '#4f8cff' }}
              icon={<UserOutlined />}
            />
            <span>{user?.display_name || user?.username || '用户'}</span>
          </Space>
        </Dropdown>
      </div>
    </header>
  )
}
