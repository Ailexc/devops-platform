"""
backend → executor 服务间认证：用私钥签发 EdDSA JWT（方案B：绑定 method / path / body_hash）

与 executor/app/auth.py 对称：
- backend 持私钥，签发凭证（真实 spug 中由 backend 完成全部用户鉴权后放行）
- executor 持公钥，只验签确认"请求确实来自 backend"

使用方式：
    token = sign_request("POST", "/api/v1/executions", body_bytes)
    Authorization: Bearer <token>
"""

import hashlib
import json
import time
import uuid

import jwt
from django.conf import settings

ISSUER = "release-system-backend"


def _load_private_key() -> str:
    with open(settings.EXECUTOR_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def sign_request(method: str, path: str, body: bytes) -> str:
    """为一次 backend → executor 请求签发服务间凭证"""
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": ISSUER,
        "iat": now,
        "exp": now + settings.EXECUTOR_TOKEN_TTL,
        "jti": uuid.uuid4().hex,
        "method": method,
        "path": path,
        # 方案B：请求体哈希绑定，防篡改 / 防重放
        "body_hash": hashlib.sha256(body).hexdigest(),
    }
    return jwt.encode(claims, _load_private_key(), algorithm="EdDSA")


def canonicalize(payload: dict) -> bytes:
    """与 executor 完全一致的请求体规范化：sort_keys + 紧凑分隔符"""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
