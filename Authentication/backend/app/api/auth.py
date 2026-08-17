"""认证接口：登录 / 刷新 / 登出 / 当前用户 / 修改密码 / SSO 跳转 / 网关 verify。"""
import logging
import threading
import time
from urllib.parse import quote

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..core.auth_providers import (
    AuthProviderUnavailable,
    AuthenticationFailed,
    UserNotFound,
    build_provider_chain,
    sync_local_user,
)
from ..core.deps import get_current_user
from ..db import get_db
from ..models import AppRegistration, AuthLog, User
from ..schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    SsoUrlRequest,
    TokenRefreshRequest,
    UserOut,
)
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger("auth.api")
router = APIRouter(prefix="/api/auth", tags=["auth"])

# 进程内 refresh token 黑名单（jti -> 过期时间戳）。Demo 用；生产应放 Redis。
_refresh_blacklist: dict[str, float] = {}
_blacklist_lock = threading.Lock()


def _revoke_refresh_jti(payload: dict) -> None:
    jti = payload.get("jti")
    exp = payload.get("exp", 0)
    if jti:
        with _blacklist_lock:
            _refresh_blacklist[jti] = float(exp)


def _is_refresh_revoked(jti: str) -> bool:
    with _blacklist_lock:
        exp = _refresh_blacklist.get(jti)
        if exp is None:
            return False
        if time.time() > exp:  # 已过期，清理
            del _refresh_blacklist[jti]
            return False
        return True


def _record_log(db: Session, username: str, source: str, success: bool, detail: str, ip: str) -> None:
    db.add(AuthLog(username=username, source=source, success=success, detail=detail, ip=ip))
    db.commit()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/login", response_model=LoginResponse, summary="用户名密码登录（身份源降级链）")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    chain = build_provider_chain(db)
    ip = _client_ip(request)
    try:
        profile = chain.authenticate(req.username, req.password)
    except UserNotFound as exc:
        _record_log(db, req.username, "", False, str(exc), ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误") from exc
    except AuthenticationFailed as exc:
        _record_log(db, req.username, "", False, str(exc), ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误") from exc
    except AuthProviderUnavailable as exc:
        _record_log(db, req.username, "", False, f"身份源不可用: {exc}", ip)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"认证服务暂不可用: {exc}") from exc

    user = sync_local_user(db, profile)
    _record_log(db, user.username, profile.source, True, "登录成功", ip)

    access_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, profile.source
    )
    refresh_token = create_refresh_token(user.id, user.username)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60,  # 1h
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=LoginResponse, summary="用 refresh_token 换取新 access_token")
def refresh(req: TokenRefreshRequest, request: Request, db: Session = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token 无效") from exc
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "不是 refresh token")
    if _is_refresh_revoked(payload.get("jti", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token 已撤销")

    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已禁用")

    access_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source
    )
    refresh_token = create_refresh_token(user.id, user.username)
    _record_log(db, user.username, user.source, True, "refresh 成功", _client_ip(request))
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/logout", summary="登出（撤销 refresh token，JWT 由客户端清除）")
def logout(req: TokenRefreshRequest, request: Request, db: Session = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        _revoke_refresh_jti(payload)
    except pyjwt.PyJWTError:
        pass
    _record_log(db, "unknown", "", False, "登出（或 token 已失效）", _client_ip(request))
    return {"message": "已登出"}


@router.get("/me", response_model=UserOut, summary="当前登录用户")
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/change-password", summary="修改密码（仅本地身份源用户）")
def change_password(req: ChangePasswordRequest, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if user.source != "local":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "非本地身份源用户不支持在此修改密码")
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码错误")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "密码已修改"}


@router.get("/sso-url", summary="获取某应用的 SSO 跳转地址（携带 JWT）")
def sso_url(app_id: str, request: Request, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    app = db.query(AppRegistration).filter(
        AppRegistration.app_id == app_id, AppRegistration.enabled.is_(True)
    ).first()
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "应用不存在或未启用")
    token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source
    )
    sep = "&" if "?" in app.home_url else "?"
    return {"url": f"{app.home_url}{sep}token={token}", "app": app.name}


@router.get("/verify", summary="统一网关 forwardAuth 校验端点")
def verify(request: Request, db: Session = Depends(get_db)):
    """供 Traefik forwardAuth 使用：校验 Bearer JWT。

    - 200：放行，并通过 X-Auth-* 响应头回传用户信息（Traefik 转给下游）
    - 401：拦截

    Demo 便利：兼容从 query 参数 `token` 读取 JWT（用于门户 SSO 跳转
    `home_url?token=xxx` 场景）。真实生产应仅用 Authorization 头。
    """
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    else:
        token = request.query_params.get("token", "")
    if not token:
        return JSONResponse(status_code=401, content={"code": 401, "user": None})
    try:
        payload = decode_token(token)
    except pyjwt.PyJWTError:
        return JSONResponse(status_code=401, content={"code": 401, "user": None})
    if payload.get("type") == "refresh":
        return JSONResponse(status_code=401, content={"code": 401, "user": None})
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        return JSONResponse(status_code=401, content={"code": 401, "user": None})
    return JSONResponse(
        status_code=200,
        content={"code": 200, "user": UserOut.model_validate(user).model_dump()},
        headers={
            "X-Auth-User": str(user.id),
            "X-Auth-Username": user.username,
            # HTTP 头仅支持 latin-1，中文等需 URL 编码
            "X-Auth-Name": quote(user.display_name),
            "X-Auth-Source": user.source,
        },
    )
