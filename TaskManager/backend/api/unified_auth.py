"""直连统一认证中心 JWKS 验签（方式二：不经网关，本地验签统一 JWT）。

接入模式说明：
- 本系统不信任网关转发头，而是直连统一认证中心的 JWKS 端点拉取公钥，
  对请求携带的 Bearer 统一 JWT 做本地 RS256 验签。
- 验签通过 → 按 uid 自动映射/创建本地用户（身份统一；授权分散由本系统自治）。
- 无 token / 验签失败 → 401（未接入统一认证的调用方被拒绝）。
"""
import time

import jwt
import requests
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

# 统一认证中心 JWKS 端点（认证中心与各系统后端同处 devops-net）
JWKS_URL = "http://auth-backend:8000/.well-known/jwks.json"

_cache = {"keys": None, "fetched": 0.0}
_CACHE_TTL = 300  # 秒


def get_jwks():
    now = time.time()
    if _cache["keys"] and now - _cache["fetched"] < _CACHE_TTL:
        return _cache["keys"]
    resp = requests.get(
        JWKS_URL,
        timeout=5,
        # 容器内网直连认证中心，不走 HTTP_PROXY（避免代理 host.docker.internal 不可达）
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    keys = resp.json().get("keys", [])
    _cache["keys"] = keys
    _cache["fetched"] = now
    return keys


def verify_unified_token(token: str) -> dict:
    """验签统一 JWT，返回 payload（失败抛异常）。"""
    header = jwt.get_unverified_header(token)
    keys = get_jwks()
    jwk = next((k for k in keys if k.get("kid") == header.get("kid")), None)
    if jwk is None:
        raise ValueError("unknown kid")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # aud 为签发时对应 client_id，直连验签不校验受众
    )


class UnifiedJWTAuthentication(BaseAuthentication):
    """直连 JWKS 验签统一 JWT（方式二接入）。"""

    keyword = "UnifiedJWT"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.lower().startswith("bearer "):
            return None  # 无统一 token → 匿名（由视图权限决定）
        try:
            payload = verify_unified_token(auth[7:].strip())
        except Exception:
            raise AuthenticationFailed("无效的统一认证令牌")
        username = payload.get("uid") or payload.get("preferred_username") or payload.get("sub")
        if not username:
            raise AuthenticationFailed("令牌缺少用户名")
        user, _ = get_user_model().objects.get_or_create(
            username=username, defaults={"is_active": True}
        )
        return (user, None)
