import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '../components/Layout/AppLayout';
import LoginPage from '../pages/login';
import DashboardPage from '../pages/dashboard';
import AppListPage from '../pages/apps';
import AppDetailPage from '../pages/apps/detail';
import ReleaseListPage from '../pages/releases';
import CreateReleasePage from '../pages/releases/create';
import ReleaseDetailPage from '../pages/releases/detail';
import ReleaseStrategiesPage from '../pages/releases/strategies';
import PermissionApprovalPage from '../pages/approvals/permission';
import ChangeApprovalPage from '../pages/approvals/change';
import ReleaseApprovalPage from '../pages/approvals/release';
import PermissionIndexPage from '../pages/permissions';
import MyPermissionsPage from '../pages/permissions/my-permissions';
import PermissionApplyPage from '../pages/permissions/apply';
import PermissionApplyCollaborationPage from '../pages/permissions/apply-collaboration';
import PermissionSharePage from '../pages/permissions/share';
import RevokePermissionPage from '../pages/permissions/revoke';
import ReleaseCollaborationPage from '../pages/permissions/release';
import ApprovalConfigPage from '../pages/permissions/approval-config';
import ApprovalReleaseStrategiesPage from '../pages/configs/approval-release-strategies';
import ApprovalPermissionStrategiesPage from '../pages/configs/approval-permission-strategies';
import ApprovalTemplatesPage from '../pages/configs/approval-templates';
import ApplyRecordsPage from '../pages/permissions/apply-records';
import RelatedToMePage from '../pages/permissions/related-to-me';
import ArtifactListPage from '../pages/artifacts';
import ArtifactDetailPage from '../pages/artifacts/detail';
import ConfigIndexPage from '../pages/configs';
import ConfigTemplateListPage from '../pages/configs/templates';
import ConfigTemplateDetailPage from '../pages/configs/template-detail';
import ConfigVariablePage from '../pages/configs/variables';
import ConfigReleaseListPage from '../pages/configs/releases';
import InfraPage from '../pages/infrastructures';
import AppReleaseDetailPage from '../pages/releases/app-detail';
import ImageRegistryPage from '../pages/images';
import AuditLogPage from '../pages/audit';
import KnowledgePage from '../pages/knowledge';
import KnowledgeDocsPage from '../pages/knowledge/docs';
import KnowledgeInterviewPage from '../pages/knowledge/interview';
import { useAuthStore } from '../store/useAuthStore';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="apps" element={<AppListPage />} />
          <Route path="apps/:id" element={<AppDetailPage />} />
          <Route path="releases" element={<ReleaseListPage />} />
          <Route path="releases/app/:appId" element={<AppReleaseDetailPage />} />
          <Route path="releases/new" element={<CreateReleasePage />} />
          <Route path="releases/:id" element={<ReleaseDetailPage />} />
          <Route path="releases/strategies" element={<ReleaseStrategiesPage />} />
          <Route path="approvals" element={<PermissionApprovalPage />} />
          <Route path="approvals/release" element={<ReleaseApprovalPage />} />
          <Route path="approvals/change" element={<ChangeApprovalPage />} />
          <Route path="permissions" element={<PermissionIndexPage />} />
          <Route path="permissions/my" element={<MyPermissionsPage />} />
          <Route path="permissions/apply" element={<PermissionApplyPage />} />
          <Route path="permissions/share" element={<PermissionSharePage />} />
          <Route path="permissions/revoke" element={<RevokePermissionPage />} />
          <Route path="permissions/release" element={<ReleaseCollaborationPage />} />
          <Route path="permissions/apply-records" element={<ApplyRecordsPage />} />
          <Route path="permissions/related-to-me" element={<RelatedToMePage />} />
          <Route path="permissions/approval-config" element={<ApprovalConfigPage />} />
          <Route path="artifacts" element={<ArtifactListPage />} />
          <Route path="artifacts/:id" element={<ArtifactDetailPage />} />
          <Route path="config" element={<ConfigIndexPage />} />
          <Route path="config/templates" element={<ConfigTemplateListPage />} />
          <Route path="config/templates/:id" element={<ConfigTemplateDetailPage />} />
          <Route path="config/variables" element={<ConfigVariablePage />} />
          <Route path="config/releases" element={<ConfigReleaseListPage />} />
          <Route path="images" element={<ImageRegistryPage />} />
          <Route path="config/approval/release-strategies" element={<ApprovalReleaseStrategiesPage />} />
          <Route path="config/approval/permission-strategies" element={<ApprovalPermissionStrategiesPage />} />
          <Route path="config/approval/templates" element={<ApprovalTemplatesPage />} />
          <Route path="infrastructures" element={<InfraPage />} />
          <Route path="audit-logs" element={<AuditLogPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="knowledge/docs" element={<KnowledgeDocsPage />} />
          <Route path="knowledge/interview" element={<KnowledgeInterviewPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}