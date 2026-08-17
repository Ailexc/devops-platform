from django.urls import path
from . import views

urlpatterns = [
    path('audit-logs/', views.audit_log_list, name='audit-log-list'),
    path('audit-logs/<int:log_id>/', views.audit_log_detail, name='audit-log-detail'),
]