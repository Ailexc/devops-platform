"""
backend → executor 请求认证（方案B：EdDSA 签名 + 请求内容绑定）

信任模型（对齐真实 spug-lambda）：
- backend 负责全部用户鉴权 / 权限校验；
- executor 只确认一件事：请求确实来自 backend，且未被篡改 / 重放。
  校验：① 公钥验签  ② issuer 正确  ③ 未过期  ④ jti 防重放
        ⑤ 方案B：method / path / body_hash 与 token 内声明一致
"""

import hashlib
import json
import threading

import jwt
from fastapi import Header, HTTPException, Request

from .config import BACKEND_PUBLIC_KEY_PATH, ISSUER

_seen_jtis = set()
_jtis_lock = threading.Lock()
_MAX_JTIS = 10000


def _load_public_key() -> bytes:
    try:
        with open(BACKEND_PUBLIC_KEY_PATH, "rb") as f:
            return f.read()
    except OSError as e:
        raise RuntimeError(
            f"无法加载 backend 公钥: {BACKEND_PUBLIC_KEY_PATH} ({e})。"
            f"请先运行 scripts/gen_executor_keys.py 生成密钥对"
        )


def _canonical_body(body_bytes: bytes) -> bytes:
    """与 backend 完全一致的请求体规范化：sort_keys + 紧凑分隔符"""
    obj = json.loads(body_bytes.decode("utf-8"))
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _check_replay(jti: str) -> bool:
    """jti 防重放：同一个凭证只能使用一次"""
    if not jti:
        return False
    with _jtis_lock:
        if jti in _seen_jtis:
            return False
        _seen_jtis.add(jti)
        if len(_seen_jtis) > _MAX_JTIS:
            _seen_jtis.clear()  # 简单清理，demo 级
        return True


async def verify_backend_request(
    request: Request,
    authorization: str = Header(default=None),
) -> dict:
    """FastAPI 依赖：确认请求确实来自 backend，返回解出的 claims"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少服务间认证凭证")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        public_key = _load_public_key()
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["EdDSA"],
            issuer=ISSUER,
            options={"require": ["iss", "iat", "exp", "jti", "method", "path", "body_hash"]},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"签名验证失败: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 防重放
    if not _check_replay(claims.get("jti", "")):
        raise HTTPException(status_code=401, detail="重复的请求凭证 (jti 已使用)")

    # 方案B：请求内容与 token 绑定一致
    if claims.get("method") != request.method:
        raise HTTPException(status_code=401, detail="请求方法与凭证不符")
    if claims.get("path") != request.url.path:
        raise HTTPException(status_code=401, detail="请求路径与凭证不符")

    if request.method in ("POST", "PUT", "PATCH"):
        raw = await request.body()
        if hashlib.sha256(_canonical_body(raw)).hexdigest() != claims.get("body_hash"):
            raise HTTPException(status_code=401, detail="请求体与凭证不符")

    return claims
