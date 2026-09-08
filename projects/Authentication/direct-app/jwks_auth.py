"""直连模式 JWT 验签中间件（JWKS 自验签）—— 可复用于任何"不经统一网关"的应用。

演示要点：
1. 不经过统一网关，业务系统自己验证统一 JWT
2. 从认证中心 /.well-known/jwks.json 拉取公钥（缓存 + 定时刷新，支持密钥轮换）
3. 用公钥本地验签 RS256 JWT（校验签名 / 过期 / audience）

任何语言都有等价实现（Go: lestrrat-go/jwx · Node: jose · Java: nimbus-jose-jwt），
本文件用 Python 展示其原理。
"""
import base64
import json
import os
import time
import urllib.request

import jwt as pyjwt

# 认证中心 JWKS 公钥地址（容器内用服务名；本地调试可用 localhost:8002）
AUTH_JWKS_URL = os.environ.get("AUTH_JWKS_URL", "http://auth-backend:8000/.well-known/jwks.json")
AUDIENCE = os.environ.get("JWT_AUDIENCE", "devops-portal")
_JWKS_TTL = int(os.environ.get("JWKS_TTL_SECONDS", "300"))  # 公钥缓存刷新周期

_jwks_cache: dict[str, dict] = {}
_jwks_fetched_at: float = 0.0


def _fetch_jwks() -> dict:
    """拉取并缓存 JWKS（首次 / 过期时刷新）。"""
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache and now - _jwks_fetched_at < _JWKS_TTL:
        return _jwks_cache
    with urllib.request.urlopen(AUTH_JWKS_URL, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    _jwks_cache = {k["kid"]: k for k in data.get("keys", [])}
    _jwks_fetched_at = now
    return _jwks_cache


def _b64_to_int(b64url: str) -> int:
    pad = "=" * (-len(b64url) % 4)
    raw = base64.urlsafe_b64decode(b64url + pad)
    return int.from_bytes(raw, "big")


def _jwk_to_public_key(jwk: dict):
    """把 JWK（RSA）转成 cryptography 公钥对象。"""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

    n = _b64_to_int(jwk["n"])
    e = _b64_to_int(jwk["e"])
    pub = RSAPublicNumbers(e, n).public_key(default_backend())
    return pub


def verify_jwt(token: str) -> dict:
    """用认证中心公钥本地验签统一 JWT。成功返回 payload，失败抛异常。"""
    header = pyjwt.get_unverified_header(token)
    keys = _fetch_jwks()
    jwk = keys.get(header.get("kid"))
    if jwk is None:
        # 密钥可能已轮换，强制刷新一次再试
        global _jwks_fetched_at
        _jwks_fetched_at = 0.0
        keys = _fetch_jwks()
        jwk = keys.get(header.get("kid"))
    if jwk is None:
        raise ValueError("未找到匹配 kid 的公钥（公钥轮换后需刷新）")
    public_key = _jwk_to_public_key(jwk)
    return pyjwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=AUDIENCE,
        options={"require": ["exp", "sub"]},
    )
