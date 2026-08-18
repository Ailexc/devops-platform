"""
Mock 数据 API URL 配置
"""
from django.urls import path
from . import mock_views

urlpatterns = [
    # 部门 API
    path('departments/', mock_views.department_list, name='mock-department-list'),
    path('departments/tree/', mock_views.department_tree, name='mock-department-tree'),
    
    # 应用 API
    path('applications/', mock_views.application_list, name='mock-application-list'),
    path('applications/<int:app_id>/', mock_views.application_detail, name='mock-application-detail'),
    
    # 环境 API
    path('environments/', mock_views.environment_list, name='mock-environment-list'),
    path('environments/<int:env_id>/', mock_views.environment_detail, name='mock-environment-detail'),
    
    # 服务 API
    path('services/', mock_views.service_list, name='mock-service-list'),
    path('services/<int:service_id>/', mock_views.service_detail, name='mock-service-detail'),
    path('services/<int:service_id>/dependencies/', mock_views.service_dependencies, name='mock-service-dependencies'),
    
    # 关系 API
    path('relations/', mock_views.relation_list, name='mock-relation-list'),
    path('relations/<int:relation_id>/', mock_views.relation_detail, name='mock-relation-detail'),
    path('relations/create/', mock_views.relation_create, name='mock-relation-create'),
    path('relations/<int:relation_id>/update/', mock_views.relation_update, name='mock-relation-update'),
    path('relations/<int:relation_id>/delete/', mock_views.relation_delete, name='mock-relation-delete'),
    
    # 图谱 API
    path('graph/environment/<int:env_id>/', mock_views.graph_environment, name='mock-graph-environment'),
    path('graph/application/<int:app_id>/', mock_views.graph_application, name='mock-graph-application'),
    
    # 资源 API
    path('resources/', mock_views.resource_list, name='mock-resource-list'),
    
    # 部署单元 API
    path('deployment-units/', mock_views.deployment_unit_list, name='mock-deployment-unit-list'),
    
    # 变更记录 API
    path('change-records/', mock_views.change_record_list, name='mock-change-record-list'),
    path('change-records/create/', mock_views.change_record_create, name='mock-change-record-create'),
    
    # 统计 API
    path('statistics/', mock_views.statistics, name='mock-statistics'),
    
    # 初始化 API
    path('initialize/', mock_views.initialize_data, name='mock-initialize'),
]