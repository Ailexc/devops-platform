from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login, name='auth-login'),
    path('auth/logout/', views.logout, name='auth-logout'),
    path('auth/me/', views.me, name='auth-me'),
    path('oauth/login/', views.oidc_login, name='oidc-login'),
    path('oauth/callback/', views.oidc_callback, name='oidc-callback'),
    path('users/', views.user_list, name='user-list'),
    path('users/<int:user_id>/', views.user_detail, name='user-detail'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user-permissions'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('dashboard/recent-releases/', views.dashboard_recent_releases, name='dashboard-recent-releases'),
    path('dashboard/my-pending-approvals/', views.dashboard_pending_approvals, name='dashboard-pending-approvals'),
]