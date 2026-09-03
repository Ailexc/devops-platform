"""网关信任认证：统一网关 forwardAuth 接入。

真实场景：Traefik forwardAuth 校验统一 JWT 通过后，向本系统注入身份头
（X-Auth-Username / X-Auth-User / X-Auth-Name / X-Auth-Source）。

本认证类信任该头，并按 username 自动映射/创建本地用户（on-the-fly provisioning）：
- 身份统一（认证中心/网关）：用户是谁
- 授权分散（本系统）：本地 User 关联的角色/权限由本系统自治

注意：认证中心在 HTTP 头中只放 latin-1，中文等非 ASCII 字符按 URL 编码
（X-Auth-Name 为 quote 后的值），本类消费时需 unquote。
无网关头时返回 None，交给后续认证类（如 SimpleJWT 本地登录）兜底。
"""
from urllib.parse import unquote

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
        # 同步网关显示名（仅内存，不落库；以认证中心目录为准，授权仍由本系统自治）
        gateway_name = request.META.get("HTTP_X_AUTH_NAME")
        if gateway_name:
            user.display_name = unquote(gateway_name)
        return (user, None)
