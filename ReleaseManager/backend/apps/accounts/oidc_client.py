"""发布系统 · 标准 OIDC 客户端（方式三：以 OIDC 授权码接入统一认证中心）。

流程：
  1. /oauth/login  → 302 认证中心 authorize（PKCE + state + openid scope）
  2. /oauth/callback → 收 code → 认证中心 token 端点换 access_token + id_token
  3. 本地 JWKS 验签 id_token，按 uid 映射本地用户，签发本地 SimpleJWT
"""
import base64
import hashlib
import secrets
import time

import jwt
import requests

# 统一认证中心（发布系统后端与认证中心同处 devops-net）
AUTH_ISSUER = "http://auth-backend:8000"
OIDC_CLIENT_ID = "release-manager-app"
OIDC_CLIENT_SECRET = "release-secret-123456"
OIDC_REDIRECT_URI = "http://release.devops.orb.local/oauth/callback"
JWKS_URL = f"{AUTH_ISSUER}/.well-known/jwks.json"

_jwks_cache = {"keys": None, "fetched": 0.0}
_CACHE_TTL = 300

_NO_PROXY = {"http": None, "https": None}


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def generate_pkce() -> tuple[str, str]:
    verifier = b64url(base64.urlsafe_b64encode(secrets.token_bytes(32)))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def generate_state() -> str:
    return secrets.token_urlsafe(16)


def _get_jwks():
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched"] < _CACHE_TTL:
        return _jwks_cache["keys"]
    resp = requests.get(JWKS_URL, timeout=5, proxies=_NO_PROXY)
    resp.raise_for_status()
    keys = resp.json().get("keys", [])
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched"] = now
    return keys


def verify_id_token(id_token: str) -> dict:
    """本地 JWKS 验签 id_token（标准 OIDC 客户端应验签名/iss/aud）。"""
    header = jwt.get_unverified_header(id_token)
    keys = _get_jwks()
    jwk = next((k for k in keys if k.get("kid") == header.get("kid")), None)
    if jwk is None:
        raise ValueError("unknown kid")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
    return jwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=OIDC_CLIENT_ID,
    )


def exchange_code(code: str, code_verifier: str) -> dict:
    """授权码换令牌（authorization_code + PKCE + client_secret）。"""
    resp = requests.post(
        f"{AUTH_ISSUER}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OIDC_REDIRECT_URI,
            "client_id": OIDC_CLIENT_ID,
            "client_secret": OIDC_CLIENT_SECRET,
            "code_verifier": code_verifier,
        },
        timeout=8,
        proxies=_NO_PROXY,
    )
    resp.raise_for_status()
    return resp.json()


def build_authorize_url(state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode
    q = urlencode({
        "response_type": "code",
        "client_id": OIDC_CLIENT_ID,
        "redirect_uri": OIDC_REDIRECT_URI,
        "scope": "openid profile",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    return f"{AUTH_ISSUER}/oauth/authorize?{q}"
