"""安全工具：bcrypt 密码哈希、RSA 密钥管理、JWT 签发/验证、JWKS、PKCE。"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .config import get_settings

settings = get_settings()

# 本地密钥持久化目录
_KEYS_DIR = Path(__file__).resolve().parent.parent / ".jwt_keys"


# ---------- 密码哈希（bcrypt） ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------- RSA 密钥管理 ----------
def _generate_keypair() -> tuple[bytes, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def load_or_create_keys() -> tuple[str, str]:
    """优先用配置注入的 PEM；否则从 .jwt_keys/ 加载，不存在则生成并持久化。"""
    if settings.jwt_private_key and settings.jwt_public_key:
        return settings.jwt_private_key, settings.jwt_public_key

    _KEYS_DIR.mkdir(parents=True, exist_ok=True)
    priv_path = _KEYS_DIR / "private.pem"
    pub_path = _KEYS_DIR / "public.pem"
    if priv_path.exists() and pub_path.exists():
        return priv_path.read_text(), pub_path.read_text()
    private_pem, public_pem = _generate_keypair()
    priv_path.write_text(private_pem.decode("utf-8"))
    pub_path.write_text(public_pem.decode("utf-8"))
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")


_PRIVATE_KEY, _PUBLIC_KEY = load_or_create_keys()
_KID = "devops-auth-1"  # 密钥 ID，用于 JWKS 与轮换


def _load_private():
    return serialization.load_pem_private_key(_PRIVATE_KEY.encode("utf-8"), password=None)


def _load_public():
    return serialization.load_pem_public_key(_PUBLIC_KEY.encode("utf-8"))


# ---------- JWT ----------
def create_access_token(user_id: int, username: str, name: str = "", email: str = "",
                        department: str = "", source: str = "local", aud: str | None = None,
                        scope: str = "") -> str:
    """签发 access_token（授权凭证）。

    - 门户/统一 JWT：aud=settings.audience（devops-portal），携带 profile claims（内部信任域共享）
    - OIDC access_token：aud=client_id，scope=请求的 scope，仅含最小授权信息（身份走 userinfo）
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "uid": username,
        "name": name,
        "email": email,
        "department": department,
        "source": source,
        "iss": settings.issuer,
        # OIDC 场景 aud 用 client_id（访问哪个应用）；默认门户 audience
        "aud": aud or settings.audience,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        "jti": str(uuid.uuid4()),
    }
    if scope:
        payload["scope"] = scope
    return jwt.encode(payload, _load_private(), algorithm=settings.jwt_algorithm, headers={"kid": _KID})


def create_id_token(user_id: int, username: str, aud: str, nonce: str = "",
                    name: str = "", email: str = "", department: str = "", source: str = "local") -> str:
    """签发 id_token（OIDC 身份断言）。

    与 access_token 职责分离：id_token 证明「用户是谁」（含 nonce 防重放），
    access_token 授权「能访问什么」（aud=client_id）。详细信息由 userinfo 按 scope 提供。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.issuer,
        "sub": str(user_id),
        "aud": aud,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        "nonce": nonce,
        "jti": str(uuid.uuid4()),
    }
    # OIDC Core 允许 id_token 携带基础 profile claims；敏感/详细信息走 userinfo
    if username:
        payload["preferred_username"] = username
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    if department:
        payload["department"] = department
    return jwt.encode(payload, _load_private(), algorithm=settings.jwt_algorithm, headers={"kid": _KID})


def create_refresh_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "uid": username,
        "type": "refresh",
        "iss": settings.issuer,
        "aud": settings.audience,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_expire_days),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _load_private(), algorithm=settings.jwt_algorithm, headers={"kid": _KID})


def decode_token(token: str, *, verify_aud: bool = True, aud: str | None = None) -> dict:
    """验证 JWT。无效时抛 jwt.PyJWTError。"""
    options = {"verify_aud": verify_aud, "require": ["exp", "sub"]}
    return jwt.decode(
        token,
        _load_public(),
        algorithms=[settings.jwt_algorithm],
        issuer=settings.issuer,
        audience=aud if aud else (settings.audience if verify_aud else None),
        options=options,
    )


# ---------- JWKS ----------
def jwks_payload() -> dict:
    """生成 JWKS（JSON Web Key Set），供 /.well-known/jwks.json 发布。"""
    public_key = _load_public()
    numbers = public_key.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": settings.jwt_algorithm,
                "kid": _KID,
                "n": _b64_int(numbers.n),
                "e": _b64_int(numbers.e),
            }
        ]
    }


def _b64_int(value: int) -> str:
    """整数转 base64url 无填充编码。"""
    length = (value.bit_length() + 7) // 8
    return jwt.utils.base64url_encode(value.to_bytes(length, byteorder="big")).decode("utf-8")


def public_key_pem() -> str:
    return _PUBLIC_KEY


# ---------- PKCE（OAuth 2.1 / RFC 9700 强制） ----------
def generate_code_verifier() -> str:
    """生成 PKCE code_verifier（43~128 字符，base64url）。"""
    return base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode("ascii")


def pkce_challenge(verifier: str) -> str:
    """S256：code_challenge = base64url(sha256(code_verifier))。"""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def verify_pkce(verifier: str, challenge: str, method: str = "S256") -> bool:
    """校验 code_verifier 与授权时保存的 code_challenge 是否匹配。"""
    if method.upper() == "S256":
        return secrets.compare_digest(pkce_challenge(verifier), challenge)
    if method.upper() == "plain":
        return secrets.compare_digest(verifier, challenge)
    return False


# ---------- OIDC refresh token（入库存哈希，轮换 + 复用检测） ----------
def generate_oauth_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_oauth_token(token: str) -> str:
    """refresh token 只存哈希（泄露数据库不泄露令牌本身）。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
