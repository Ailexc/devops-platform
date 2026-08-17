from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # API v1
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.organizations.urls')),
    path('api/v1/', include('apps.authz.urls')),
    # Phase 3: 应用管理 + 基础设施 + 制品 + 配置
    path('api/v1/', include('apps.applications.urls')),
    path('api/v1/', include('apps.infrastructures.urls')),
    path('api/v1/', include('apps.artifacts.urls')),
    path('api/v1/', include('apps.configs.urls')),
    # Phase 4: 发布管理 + 审批 + 部署 + 审计
    path('api/v1/', include('apps.releases.urls')),
    path('api/v1/', include('apps.approvals.urls')),
    path('api/v1/', include('apps.deployments.urls')),
    path('api/v1/', include('apps.audit.urls')),
    # 知识库
    path('api/v1/', include('knowledge.urls')),
]