from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet)
router.register('roles', views.RoleViewSet)
router.register('permissions', views.PermissionViewSet)
router.register('departments', views.DepartmentViewSet)
router.register('audit-logs', views.OperationLogViewSet)

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('', include(router.urls)),
]
