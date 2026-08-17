"""FastAPI 依赖：当前用户解析、管理员校验。"""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import decode_token
import jwt as pyjwt


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """从 Authorization Bearer JWT 解析当前用户。"""
    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供凭证")
    try:
        payload = decode_token(token)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"凭证无效: {exc}") from exc
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 不可用于访问")
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
