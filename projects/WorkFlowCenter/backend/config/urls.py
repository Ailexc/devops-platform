from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Django Admin 迁移到 /django-admin/，释放 /admin/* 给前端管理页面
    path('django-admin/', admin.site.urls),
    # Common (AI 配置等)
    path('api/v1/', include('apps.common.urls')),
    # Accounts
    path('api/v1/', include('apps.accounts.urls')),
    # Process engine
    path('api/v1/', include('apps.processes.urls')),
    # Tickets
    path('api/v1/', include('apps.tickets.urls')),
    # Capabilities
    path('api/v1/', include('apps.capabilities.urls')),
    # Events
    path('api/v1/', include('apps.events.urls')),
    # Knowledge
    path('api/v1/', include('apps.knowledge.urls')),
    # OpenAPI schema & Swagger UI
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
