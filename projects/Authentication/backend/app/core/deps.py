"""FastAPI 依赖：当前用户解析、管理员校验。"""
import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import decode_token
from .sessions import PORTAL_COOKIE, get_portal_session


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """解析当前用户。

    兼容两条认证通道：
    1. Authorization: Bearer <JWT> —— 网关 forwardAuth、直连应用、OIDC 客户端
    2. 门户 BFF 会话（HttpOnly Cookie）—— 门户 SPA 同源调用 /api/*（OIDC 登录后）
    """
    # 1. Bearer JWT
    token = _bearer_token(request)
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") != "refresh":
                user = db.get(User, int(payload.get("sub", 0)))
                if user is not None and user.is_active:
                    return user
        except pyjwt.PyJWTError:
            pass  # 无效 Bearer 不立即拒绝，继续尝试门户会话
    # 2. 门户 BFF 会话（OIDC 登录后的 HttpOnly Cookie）
    sid = request.cookies.get(PORTAL_COOKIE)
    session = get_portal_session(sid) if sid else None
    if session and session.get("user"):
        user = db.get(User, session["user"].get("id"))
        if user is not None and user.is_active:
            return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供有效凭证")


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
