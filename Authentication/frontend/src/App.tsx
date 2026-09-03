import { useEffect } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import AppHeader from './components/AppHeader'
import LoginPage from './pages/LoginPage'
import PortalPage from './pages/PortalPage'
import ProfilePage from './pages/ProfilePage'
import AdminAppsPage from './pages/AdminAppsPage'
import E2eTestPage from './pages/E2eTestPage'
import PresentationHubPage from './pages/PresentationHubPage'
import PresentationPlayerPage from './pages/PresentationPlayerPage'
import SystemDocsHubPage from './pages/SystemDocsHubPage'
import SystemDocsReaderPage from './pages/SystemDocsReaderPage'

// 登录守卫：启动时从 BFF 会话恢复用户；未登录跳转登录页
function RequireAuth() {
  const user = useAuthStore((s) => s.user)
  const initialized = useAuthStore((s) => s.initialized)
  const bootstrap = useAuthStore((s) => s.bootstrap)

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  if (!initialized) {
    return (
      <div
        style={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#667085',
          fontSize: 14,
        }}
      >
        正在恢复登录状态…
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return (
    <div className="portal-container">
      <AppHeader />
      <Outlet />
    </div>
  )
}

// 管理员守卫：非管理员跳回首页
function RequireAdmin({ children }: { children: React.ReactNode }) {
  const isAdmin = useAuthStore((s) => s.user?.is_admin)
  if (!isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<PortalPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route
          path="/admin/apps"
          element={
            <RequireAdmin>
              <AdminAppsPage />
            </RequireAdmin>
          }
        />
        <Route path="/dev/e2e-test" element={<E2eTestPage />} />
        <Route path="/presentation" element={<PresentationHubPage />} />
        <Route path="/presentation/:sceneId" element={<PresentationPlayerPage />} />
        <Route path="/docs" element={<SystemDocsHubPage />} />
        <Route path="/docs/:docId" element={<SystemDocsReaderPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
