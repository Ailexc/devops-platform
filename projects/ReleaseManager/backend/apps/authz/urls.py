from django.urls import path
from . import views

urlpatterns = [
    # 角色
    path('authz/roles/', views.role_list, name='role-list'),
    path('authz/roles/<int:role_id>/', views.role_detail, name='role-detail'),
    # 数据权限规则
    path('authz/data-rules/', views.data_rule_list, name='data-rule-list'),
    path('authz/data-rules/<int:rule_id>/', views.data_rule_detail, name='data-rule-detail'),
    # 用户权限
    path('authz/my-permissions/', views.my_permissions, name='my-permissions'),
    path('authz/users/<int:user_id>/permissions/', views.user_permissions_detail, name='user-permissions-detail'),
    # 组权限
    path('authz/groups/<int:group_id>/permissions/', views.group_permissions_detail, name='group-permissions-detail'),
    # 权限申请
    path('authz/permission-requests/', views.permission_request_list, name='perm-request-list'),
    path('authz/my-permission-requests/', views.my_perm_requests, name='my-perm-requests'),
    path('authz/related-permission-requests/', views.related_perm_requests, name='related-perm-requests'),
    path('authz/permission-requests/<int:request_id>/approve/', views.approve_permission_request, name='approve-perm-request'),
    # 审批流模板
    path('authz/approval-flow-templates/', views.flow_template_list, name='flow-template-list'),
    path('authz/approval-flow-templates/<int:template_id>/', views.flow_template_detail, name='flow-template-detail'),
    # 审批配置
    path('authz/approval-configs/', views.approval_config_list, name='approval-config-list'),
    path('authz/approval-configs/<int:config_id>/', views.approval_config_detail, name='approval-config-detail'),
    # 审批流计算
    path('authz/calculate-approval-flow/', views.calculate_approval_flow, name='calculate-approval-flow'),
    # 业务线负责人
    path('authz/business-line-leader/', views.business_line_leader, name='business-line-leader'),
    # 鉴权检查
    path('authz/check-permission/', views.check_permission, name='check-permission'),
    # ABAC-Lite 鉴权查询
    path('authz/check-access/', views.access_check, name='access-check'),
    path('authz/check-access-batch/', views.access_check_batch, name='access-check-batch'),
    # 权限调整
    path('authz/groups/<int:group_id>/permission-adjust-detail/', views.permission_adjust_detail, name='permission-adjust-detail'),
    path('authz/groups/<int:group_id>/permission-adjust-submit/', views.permission_adjust_submit, name='permission-adjust-submit'),
    # 应用变更审批配置
    path('authz/app-change-approval-configs/', views.app_change_approval_config_list, name='app-change-approval-config-list'),
    path('authz/app-change-approval-configs/<int:config_id>/', views.app_change_approval_config_detail, name='app-change-approval-config-detail'),
    # 发布策略
    path('authz/release-approval-configs/', views.release_approval_config_list, name='release-approval-config-list'),
    path('authz/release-approval-configs/<int:config_id>/', views.release_approval_config_detail, name='release-approval-config-detail'),
]