import {
  AppstoreOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { App as AntApp, Avatar, Dropdown, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'

export default function AppHeader() {
  const nav = useNavigate()
  const { message } = AntApp.useApp()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleLogout = async () => {
    try {
      await authApi.logout(useAuthStore.getState().refreshToken ?? '')
    } catch {
      /* 忽略：客户端清除即可 */
    }
    logout()
    message.success('已退出登录')
    nav('/login', { replace: true })
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
