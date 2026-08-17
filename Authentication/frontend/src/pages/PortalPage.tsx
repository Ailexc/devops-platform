import {
  AlertOutlined,
  ApartmentOutlined,
  AppstoreOutlined,
  CheckSquareOutlined,
  CloudServerOutlined,
  ExperimentOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { App as AntApp, Card, Col, Row, Skeleton, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { appApi, authApi } from '../api/client'
import { useAuthStore } from '../store/auth'
import type { AppInfo } from '../types'

// 应用图标映射（来自应用注册表 icon 字段）
const ICON_MAP: Record<string, { icon: React.ReactNode; color: string }> = {
  CheckSquareOutlined: { icon: <CheckSquareOutlined />, color: '#1677ff' },
  CloudServerOutlined: { icon: <CloudServerOutlined />, color: '#0ea5e9' },
  ApartmentOutlined: { icon: <ApartmentOutlined />, color: '#8b5cf6' },
  AlertOutlined: { icon: <AlertOutlined />, color: '#f59e0b' },
  RocketOutlined: { icon: <RocketOutlined />, color: '#ef4444' },
  SafetyCertificateOutlined: { icon: <SafetyCertificateOutlined />, color: '#10b981' },
  ExperimentOutlined: { icon: <ExperimentOutlined />, color: '#6366f1' },
}
const FALLBACK = { icon: <AppstoreOutlined />, color: '#64748b' }

export default function PortalPage() {
  const { message } = AntApp.useApp()
  const user = useAuthStore((s) => s.user)
  const [apps, setApps] = useState<AppInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    appApi
      .list()
      .then((r) => setApps(r.data))
      .catch(() => message.error('加载应用列表失败'))
      .finally(() => setLoading(false))
  }, [message])

  // 点击应用：获取带统一 JWT 的 SSO 跳转地址，新窗口打开业务系统
  const openApp = async (app: AppInfo) => {
    try {
      const { data } = await authApi.ssoUrl(app.app_id)
      window.open(data.url, '_blank', 'noopener,noreferrer')
    } catch {
      message.error(`打开「${app.name}」失败，请确认应用地址可访问`)
    }
  }

  return (
    <main>
      <div className="welcome-banner">
        <div>
          <h2>欢迎回来，{user?.display_name || user?.username}</h2>
          <p>您已通过统一认证中心登录，以下应用均已为您开通，点击即可直接访问。</p>
        </div>
        <span>认证来源：{user?.source === 'ldap' ? 'LDAP' : user?.source === 'okta' ? 'Okta' : '本地用户库'}</span>
      </div>

      <div className="app-grid">
        <h3 style={{ color: '#344054', margin: '8px 8px 16px' }}>应用广场</h3>
        {loading ? (
          <Row gutter={[20, 20]}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Col key={i} xs={24} sm={12} md={8} lg={6}>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Col>
            ))}
          </Row>
        ) : (
          <Row gutter={[20, 20]}>
            {apps.map((app) => {
              const { icon, color } = ICON_MAP[app.icon] ?? FALLBACK
              return (
                <Col key={app.id} xs={24} sm={12} md={8} lg={6}>
                  <Card
                    className="app-card"
                    style={{ position: 'relative' }}
                    onClick={() => openApp(app)}
                    aria-label={`打开应用 ${app.name}`}
                  >
                    <Tag
                      style={{ position: 'absolute', top: 12, right: 12, margin: 0 }}
                      color={app.access_mode === 'direct' ? 'purple' : 'blue'}
                    >
                      {app.access_mode === 'direct' ? '直连接入' : '网关接入'}
                    </Tag>
                    <div className="app-icon" style={{ background: color }}>
                      {icon}
                    </div>
                    <h3>{app.name}</h3>
                    <p>{app.description}</p>
                  </Card>
                </Col>
              )
            })}
          </Row>
        )}
      </div>
    </main>
  )
}
