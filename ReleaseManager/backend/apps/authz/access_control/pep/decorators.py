"""
PEP — Policy Enforcement Point

提供 @require_permission 装饰器，用于在视图函数上声明所需的资源权限。

用法:
    @api_view(['POST'])
    @require_permission('group', 'manage')
    def add_member(request, group_id):
        ...

装饰器行为:
    - 权限通过 → 执行原视图函数
    - 权限拒绝 → 返回 403 JSON 响应
"""

from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from apps.authz.access_control.pdp.engine import PolicyDecisionPoint

# 全局 PDP 实例
_pdp = PolicyDecisionPoint()


def require_permission(resource_type: str, action: str):
    """
    装饰器：要求当前用户对指定资源拥有指定操作权限。

    Args:
        resource_type: 资源类型标识（'group', 'business_line', 'user' 等）
        action: 操作标识（'manage', 'view', 'share', 'apply', 'revoke' 等）

    资源 ID 自动从视图函数的 kwargs 中提取:
        resource_type='group'         → 取 group_id
        resource_type='business_line' → 取 bl_id 或 business_line_id
        resource_type='user'          → 取 user_id
        resource_type='app'           → 取 app_id
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            resource_id = _extract_resource_id(resource_type, kwargs)
            if resource_id is None:
                return Response(
                    {"code": 400, "message": "缺少资源ID", "error_code": "MISSING_RESOURCE_ID"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not _pdp.evaluate(request.user, resource_type, resource_id, action):
                return Response(
                    {
                        "code": 403,
                        "message": "您没有权限对当前资源执行此操作",
                        "error_code": "PERMISSION_DENIED",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── 内部工具 ────────────────────────────────────────────────

_RESOURCE_ID_KEY_MAP = {
    "group":          ["group_id"],
    "business_line":  ["bl_id", "business_line_id"],
    "user":           ["user_id"],
    "app":            ["app_id"],
    "environment":    ["env_id", "environment_id"],
}


def _extract_resource_id(resource_type: str, kwargs: dict):
    """从视图函数的 kwargs 中自动提取资源 ID"""
    for key in _RESOURCE_ID_KEY_MAP.get(resource_type, []):
        if key in kwargs:
            return kwargs[key]
    return None
