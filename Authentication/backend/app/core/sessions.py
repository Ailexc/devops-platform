"""会话存储：IdP 登录会话 + 门户 BFF 会话。

Demo 用进程内内存存储（重启即失效）。生产环境应替换为 Redis / DB（带 TTL）。
设计：
- IdP 会话：用户在认证中心登录后建立的会话（HttpOnly Cookie: auth_idp_session）
  → authorize 时检查，无需重复登录（SSO 体验）
- 门户 BFF 会话：门户作为 OIDC 客户端换到 token 后建立的会话（HttpOnly Cookie: portal_session）
  → 门户 SPA 调 /api/* 时从该会话解析当前用户，token 不进浏览器
"""
from __future__ import annotations

import secrets
import threading
import time

_IDP_SESSIONS: dict[str, dict] = {}
_PORTAL_SESSIONS: dict[str, dict] = {}
_lock = threading.Lock()

IDP_COOKIE = "auth_idp_session"  # IdP 登录会话 cookie 名
PORTAL_COOKIE = "portal_session"  # 门户 BFF 会话 cookie 名
SESSION_TTL = 8 * 3600  # 会话默认 8 小时


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
