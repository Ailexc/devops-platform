from django.urls import path
from . import views
from apps.infrastructures import views as infra_views

urlpatterns = [
    path('apps/', views.app_list, name='app-list'),
    path('apps/<int:app_id>/', views.app_detail, name='app-detail'),
    path('apps/<int:app_id>/env-configs/', views.app_env_config_list, name='app-env-config-list'),
    path('apps/<int:app_id>/env-configs/<int:config_id>/', views.app_env_config_detail, name='app-env-config-detail'),
    path('apps/<int:app_id>/scale/', infra_views.scale_application, name='app-scale'),
    path('apps/<int:app_id>/operations/', infra_views.application_operations, name='app-operations'),
    path('resource-tree/', views.resource_tree, name='resource-tree'),
    # 镜像注册表
    path('images/', views.image_registry_list, name='image-registry-list'),
    path('images/<int:image_id>/', views.image_registry_detail, name='image-registry-detail'),
    # 模拟 Git 数据
    path('apps/<int:app_id>/branches/', views.AppBranchesView.as_view(), name='app-branches'),
    path('apps/<int:app_id>/commits/', views.AppCommitsView.as_view(), name='app-commits'),
]