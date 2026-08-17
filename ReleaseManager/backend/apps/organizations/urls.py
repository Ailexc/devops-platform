from django.urls import path
from . import views

urlpatterns = [
    path('org/tree/', views.org_tree, name='org-tree'),
    # 业务线
    path('org/business-lines/', views.business_line_list, name='business-line-list'),
    path('org/business-lines/<int:bl_id>/', views.business_line_detail, name='business-line-detail'),
    # 组
    path('org/groups/', views.group_list, name='group-list'),
    path('org/groups/<int:group_id>/', views.group_detail, name='group-detail'),
    # 组成员
    path('org/groups/<int:group_id>/members/', views.add_member, name='add-member'),
    path('org/groups/<int:group_id>/members/<int:user_id>/', views.member_detail, name='member-detail'),
]