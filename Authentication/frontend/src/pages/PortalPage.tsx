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
  const [apps, setApps] = useState<(AppInfo & { ssoUrl?: string })[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    appApi
      .list()
      .then(async (r) => {
        // 预取每个应用的 SSO 跳转地址，渲染为真实 <a href> 链接。
        // 移动端浏览器会拦截「异步回调里的 window.open」（popup 拦截），导致点击无反应；
        // 用原生链接导航可避免，桌面 / 移动行为一致。
        const list = r.data
        const withUrl = await Promise.all(
          list.map(async (app): Promise<AppInfo & { ssoUrl?: string }> => {
            try {
              const { data } = await authApi.ssoUrl(app.app_id)
              return { ...app, ssoUrl: data.url }
            } catch {
              return { ...app }
            }
          }),
        )
        setApps(withUrl)
      })
      .catch(() => message.error('加载应用列表失败'))
      .finally(() => setLoading(false))
  }, [message])

  // 兜底：sso-url 预取失败时点击卡片，用顶层导航打开
  //（异步 window.open 在移动端会被 popup 拦截，故改用 location.href）
  const openAppFallback = async (app: AppInfo) => {
    try {
      const { data } = await authApi.ssoUrl(app.app_id)
      window.location.href = data.url
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
                  <Card className="app-card" style={{ position: 'relative' }}>
                    <a
                      href={app.ssoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="app-card-link"
                      aria-label={`打开应用 ${app.name}`}
                      onClick={(e) => {
                        // 预取失败无链接时，兜底异步跳转
                        if (!app.ssoUrl) {
                          e.preventDefault()
                          void openAppFallback(app)
                        }
                      }}
                    >
                      <Tag
                        style={{ position: 'absolute', top: 12, right: 12, margin: 0 }}
                        color={app.access_mode === 'direct' ? 'purple' : app.access_mode === 'external' ? 'orange' : 'blue'}
                      >
                        {app.access_mode === 'direct' ? '直连接入' : app.access_mode === 'external' ? '独立管理' : '网关接入'}
                      </Tag>
                      <div className="app-icon" style={{ background: color }}>
                        {icon}
                      </div>
                      <h3>{app.name}</h3>
                      <p>{app.description}</p>
                    </a>
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
