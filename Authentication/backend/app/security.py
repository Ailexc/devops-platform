"""安全工具：bcrypt 密码哈希、RSA 密钥管理、JWT 签发/验证、JWKS。"""
from __future__ import annotations

import json
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
                        department: str = "", source: str = "local", aud: str | None = None) -> str:
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
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        "jti": str(uuid.uuid4()),
    }
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
