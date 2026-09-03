"""网关信任认证：统一网关 forwardAuth 接入（工单中心 WorkFlowCenter）。

真实场景：Traefik forwardAuth 校验统一 JWT 通过后，向本系统注入身份头
（X-Auth-Username / X-Auth-User / X-Auth-Name / X-Auth-Source）。

本认证类信任该头，并按 username 自动映射/创建本地用户（on-the-fly provisioning）：
- 身份统一（认证中心/网关）：用户是谁
- 授权分散（本系统）：本地 User 关联的角色/权限由本系统自治

无网关头时返回 None，交给后续认证类（如 SimpleJWT 本地登录）兜底。
"""
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

User = get_user_model()


class GatewayAuthentication(BaseAuthentication):
    """信任统一网关注入的 X-Auth-Username 身份头。"""

    keyword = "Gateway"

    def authenticate(self, request):
        username = request.META.get("HTTP_X_AUTH_USERNAME")
        if not username:
            return None  # 无网关头 → 交回原认证链
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"is_active": True},
        )
        return (user, None)
