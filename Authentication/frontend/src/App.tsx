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

// 登录守卫：未登录跳转登录页
function RequireAuth() {
  const token = useAuthStore((s) => s.accessToken)
  if (!token) return <Navigate to="/login" replace />
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
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
