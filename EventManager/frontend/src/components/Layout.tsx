import { useState, useCallback, useEffect } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { getBackendMode, switchBackend, fetchCurrentUser, type BackendMode } from '../api'

const navItems = [
  { to: '/dashboard', icon: '📊', label: '仪表盘' },
  { to: '/events', icon: '📋', label: '事件列表' },
  { to: '/dlq', icon: '💀', label: '死信队列' },
  { to: '/event-types', icon: '🧩', label: '事件类型' },
  { to: '/test-lab', icon: '🧪', label: '测试模块' },
  { to: '/docs', icon: '📚', label: '系统文档', end: true },
  { to: '/docs/handbook', icon: '🎤', label: '面试手册' },
]

export default function Layout() {
  // 收缩状态持久化到 localStorage
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar-collapsed') === '1')
  const [backend, setBackend] = useState<BackendMode>(() => getBackendMode())
  const [username, setUsername] = useState<string>(() => localStorage.getItem('event.user') || '')

  // 加载当前用户（统一认证 SSO 方式二：直连 JWKS 验签）
  useEffect(() => {
    if (!localStorage.getItem('event.token')) return
    fetchCurrentUser()
      .then((me) => {
        setUsername(me.username)
        localStorage.setItem('event.user', me.username)
      })
      .catch(() => {
        /* 未认证则保持匿名 */
      })
  }, [])

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      localStorage.setItem('sidebar-collapsed', c ? '0' : '1')
      return !c
    })
  }

  const handleSwitchBackend = useCallback(() => {
    setBackend((prev) => {
      const next: BackendMode = prev === 'python' ? 'go' : 'python'
      switchBackend(next)
      // 刷新页面使所有 API 请求使用新的 base URL
      window.location.reload()
      return next
    })
  }, [])

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside
        className={`bg-white border-r border-slate-200 flex flex-col flex-shrink-0 transition-colors duration-200 ${
          collapsed ? 'w-16' : 'w-56'
        }`}
      >
        {/* Header */}
        <div className="h-14 flex items-center px-3 border-b border-slate-200 gap-2">
          {!collapsed && (
            <span className="text-lg font-bold text-primary-500 flex-1 truncate">⚡ EventFlow</span>
          )}
          <button
            onClick={toggleCollapsed}
            title={collapsed ? '展开菜单' : '收起菜单'}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-slate-100 transition-colors ${
              collapsed ? 'mx-auto' : ''
            }`}
          >
            {collapsed ? '»' : '«'}
          </button>
        </div>

        {/* Backend Switch Toggle */}
        <div className="px-3 py-2 border-b border-slate-200">
          <button
            onClick={handleSwitchBackend}
            title={collapsed ? `当前: ${backend === 'python' ? 'Python (Django)' : 'Go (Gin)'}` : '切换后端'}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              collapsed ? 'justify-center px-0' : ''
            } ${
              backend === 'go'
                ? 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                : 'bg-green-50 text-green-600 hover:bg-green-100'
            }`}
          >
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${backend === 'go' ? 'bg-blue-500' : 'bg-green-500'}`} />
            <span className={collapsed ? 'hidden' : ''}>
              {backend === 'python' ? 'Python · Django' : 'Go · Gin'}
            </span>
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  collapsed ? 'justify-center px-0' : ''
                } ${
                  isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              <span className="text-base flex-shrink-0">{item.icon}</span>
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-200">
          {username && (
            <div
              className={`flex items-center gap-2 py-2 text-xs font-medium text-slate-600 ${
                collapsed ? 'justify-center px-0' : 'px-3'
              }`}
              title="当前登录用户（统一认证 SSO）"
            >
              <span className="flex-shrink-0">👤</span>
              {!collapsed && <span className="truncate">{username}</span>}
            </div>
          )}
          <div
            className={`flex items-center gap-2 py-2 text-xs text-slate-400 ${
              collapsed ? 'justify-center px-0' : 'px-3'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" />
            {!collapsed && <span>Demo v0.1</span>}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
