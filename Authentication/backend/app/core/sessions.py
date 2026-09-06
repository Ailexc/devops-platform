"""会话存储：IdP 登录会话 + 门户 BFF 会话 + 网关会话 + 一次性授权码。

Demo 用进程内内存存储（重启即失效）。生产环境应替换为 Redis / DB（带 TTL）。
设计：
- IdP 会话：用户在认证中心登录后建立的会话（HttpOnly Cookie: auth_idp_session）
  → authorize 时检查，无需重复登录（SSO 体验）
- 门户 BFF 会话：门户作为 OIDC 客户端换到 token 后建立的会话（HttpOnly Cookie: portal_session）
  → 门户 SPA 调 /api/* 时从该会话解析当前用户，token 不进浏览器
- 网关会话：统一网关 forwardAuth 使用的会话（HttpOnly Cookie: _gw_session）
  → 门户登录时签发，所有业务系统共享，替代 URL 传 token
- 一次性授权码：方式二（直连 JWKS）安全跳转用（非 JWT，UUID，60s 有效期，用完即毁）
"""
from __future__ import annotations

import secrets
import threading
import time

_IDP_SESSIONS: dict[str, dict] = {}
_PORTAL_SESSIONS: dict[str, dict] = {}
_GW_SESSIONS: dict[str, dict] = {}
_ONETIME_CODES: dict[str, dict] = {}  # 一次性授权码（code -> 用户信息 + 过期时间）
_lock = threading.Lock()

IDP_COOKIE = "auth_idp_session"  # IdP 登录会话 cookie 名
PORTAL_COOKIE = "portal_session"  # 门户 BFF 会话 cookie 名
GW_COOKIE = "_gw_session"  # 网关会话 cookie 名
SESSION_TTL = 8 * 3600  # 会话默认 8 小时
ONETIME_CODE_TTL = 60  # 一次性授权码有效期 60 秒


def _cleanup(store: dict) -> None:
    now = time.time()
    for key in [k for k, v in store.items() if v.get("exp", 0) < now]:
        store.pop(key, None)


def _create(store: dict, data: dict, ttl: int) -> str:
    sid = secrets.token_urlsafe(32)
    with _lock:
        _cleanup(store)
        merged = dict(data)
        merged["exp"] = time.time() + ttl
        store[sid] = merged
    return sid


def _get(store: dict, sid: str | None) -> dict | None:
    if not sid:
        return None
    with _lock:
        _cleanup(store)
        s = store.get(sid)
        if s is None:
            return None
        if s.get("exp", 0) < time.time():
            store.pop(sid, None)
            return None
        return dict(s)


def _delete(store: dict, sid: str | None) -> None:
    if not sid:
        return
    with _lock:
        store.pop(sid, None)


# ---------- IdP 登录会话 ----------
def create_idp_session(user_id: int, username: str) -> str:
    return _create(_IDP_SESSIONS, {"user_id": user_id, "username": username}, SESSION_TTL)


def get_idp_session(sid: str | None) -> dict | None:
    return _get(_IDP_SESSIONS, sid)


def delete_idp_session(sid: str | None) -> None:
    _delete(_IDP_SESSIONS, sid)


# ---------- 门户 BFF 会话 ----------
def create_portal_session(user: dict) -> str:
    """user：门户会话要缓存的用户信息（含 OIDC token 快照，供刷新使用）。"""
    return _create(_PORTAL_SESSIONS, {"user": user}, SESSION_TTL)


def get_portal_session(sid: str | None) -> dict | None:
    return _get(_PORTAL_SESSIONS, sid)


def delete_portal_session(sid: str | None) -> None:
    _delete(_PORTAL_SESSIONS, sid)


# ---------- 网关会话（统一网关 forwardAuth 用）----------
def create_gateway_session(user_info: dict) -> str:
    """创建网关会话。user_info 含 id/username/display_name/email/department/source。
    门户登录时签发，所有业务系统共享（同 IP 不同端口 Cookie 共享，RFC 6265）。"""
    return _create(_GW_SESSIONS, {
        "user_id": user_info["id"],
        "username": user_info["username"],
        "display_name": user_info.get("display_name", ""),
        "email": user_info.get("email", ""),
        "department": user_info.get("department", ""),
        "source": user_info.get("source", "local"),
    }, SESSION_TTL)


def get_gateway_session(sid: str | None) -> dict | None:
    return _get(_GW_SESSIONS, sid)


def delete_gateway_session(sid: str | None) -> None:
    _delete(_GW_SESSIONS, sid)


# ---------- 一次性授权码（方式二：直连 JWKS 安全跳转）----------
def create_onetime_code(user) -> str:
    """生成一次性授权码（非 JWT，UUID，60s 有效期，用完即毁）。
    用于方式二（直连 JWKS）：门户跳转时携带 code，业务后端用 code 换 JWT。"""
    code = secrets.token_urlsafe(32)
    with _lock:
        _cleanup(_ONETIME_CODES)
        _ONETIME_CODES[code] = {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name or "",
            "email": user.email or "",
            "department": user.department or "",
            "source": user.source or "local",
            "exp": time.time() + ONETIME_CODE_TTL,
        }
    return code


def redeem_onetime_code(code: str) -> dict | None:
    """兑换一次性授权码，用完即毁。返回用户信息或 None。"""
    with _lock:
        info = _ONETIME_CODES.pop(code, None)
        if info is None:
            return None
        if info["exp"] < time.time():
            return None
    return info


def get_portal_session(sid: str | None) -> dict | None:
    return _get(_PORTAL_SESSIONS, sid)


def delete_portal_session(sid: str | None) -> None:
    _delete(_PORTAL_SESSIONS, sid)
