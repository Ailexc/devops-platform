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
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class GatewayAuthentication(BaseAuthentication):
    """信任统一网关注入的 X-Auth-Username 身份头。

    账号作用域收口：网关注入的用户名为「cloud_前缀 + 本名」（如 cloud_ops_user），
    admin 为全局超管；本地已开通才放行，未开通明确拒绝（不再 on-the-fly 建用户）。
    """

    keyword = "Gateway"
    # 本系统账号前缀
    PREFIX = "cloud_"

    @staticmethod
    def map_local(raw: str) -> str | None:
        """认证中心账号 → 本地用户名；None = 未在本系统开通。"""
        if raw == "admin":
            return "admin"  # 全局超管
        if raw == "cloud_admin":
            return "cloud_admin"  # 云管云管理员：原名唯一且即本地名，不重复加前缀
        if raw.startswith(GatewayAuthentication.PREFIX):
            return raw[len(GatewayAuthentication.PREFIX):]  # cloud_ops_user → ops_user
        return None

    def authenticate(self, request):
        username = request.META.get("HTTP_X_AUTH_USERNAME")
        if not username:
            return None  # 无网关头 → 交回原认证链
        local = self.map_local(username)
        if local is None:
            raise AuthenticationFailed("该账号未在云管系统开通")
        user = User.objects.filter(username=local, is_active=True).first()
        if user is None:
            raise AuthenticationFailed("该账号未在云管系统开通")
        # 同步网关显示名（仅内存，不落库；以认证中心目录为准，授权仍由本系统自治）
        gateway_name = request.META.get("HTTP_X_AUTH_NAME")
        if gateway_name:
            user.display_name = unquote(gateway_name)
        return (user, None)
