"""
自定义权限类
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """仅管理员可访问"""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsAgent(BasePermission):
    """客服 / 代理人员"""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name='agents').exists()
        )


class IsUser(BasePermission):
    """普通用户（已认证）"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(BasePermission):
    """对象级：仅允许 owner 修改"""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        owner_attr = getattr(obj, 'started_by', None) or getattr(obj, 'user', None)
        return owner_attr == request.user
