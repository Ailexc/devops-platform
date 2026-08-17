from django.urls import path
from . import views

urlpatterns = [
    path('deploy-history/', views.deploy_history_list, name='deploy-history-list'),
    path('deploy-history/<int:history_id>/', views.deploy_history_detail, name='deploy-history-detail'),
    path('deploy-history/<int:history_id>/pods/', views.deploy_pods, name='deploy-pods'),
    path('deploy-history/<int:history_id>/rollback/', views.deploy_rollback, name='deploy-rollback'),
]