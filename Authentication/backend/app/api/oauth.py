"""OIDC 授权码模式端点 —— 认证中心作为 OIDC Provider（IdP）。

完整还原企业 SSO 的授权码流程，让 client_id / client_secret 真正派上用场：
  ① 业务系统前端 → /oauth/authorize?client_id=xxx&redirect_uri=xxx&response_type=code
  ② 认证中心校验统一 JWT + 应用注册 → 生成一次性授权码 code → 302 带回业务系统
  ③ 业务系统后端 → POST /oauth/token?code + client_secret（机密只存后端）
  ④ 认证中心校验 client_secret → 发 access_token / id_token（aud=client_id）
  ⑤ 业务系统后端 → GET /oauth/userinfo（Bearer access_token）→ 用户信息

Demo 简化：用户已从门户登录持有统一 JWT（authorize 时携带）；code 一次性短时效存内存。
"""
import secrets
import time
from urllib.parse import urlencode

import jwt as pyjwt
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import AppRegistration, User
from ..schemas import UserOut
from ..security import create_access_token, decode_token

settings = get_settings()
router = APIRouter(tags=["oauth"])

# 一次性授权码存储：code -> {client_id, username, exp}。Demo 用内存；生产应放 Redis。
_auth_codes: dict[str, dict] = {}
_CODE_TTL = 300  # 5 分钟


@router.get("/.well-known/openid-configuration", summary="OIDC Provider 元数据")
def oidc_configuration():
    base = settings.oidc_base_url.rstrip("/")
    return {
        "issuer": settings.issuer,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": [settings.jwt_algorithm],
        "scopes_supported": ["openid", "profile", "email"],
    }


@router.get("/oauth/authorize", summary="① 授权端点：带统一 JWT + client_id → 302 带 code")
def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("openid profile"),
    state: str = Query(""),
    token: str = Query(""),
    # Demo 便利：response_mode=json 时返回 JSON（含 code）而非 302，供 E2E 演示直接拿授权码
    response_mode: str = Query("query"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    if response_type != "code":
        return _redirect_error(redirect_uri, "unsupported_response_type", state)

    app = db.query(AppRegistration).filter(AppRegistration.client_id == client_id).first()
    if app is None or not app.enabled:
        raise HTTPException(status_code=400, detail="未知或已禁用的 client_id")

    # Demo：redirect_uri 需匹配应用注册的 home_url（生产应严格校验注册时的白名单）
    if redirect_uri and not redirect_uri.startswith(app.home_url):
        raise HTTPException(status_code=400, detail="redirect_uri 与注册的 home_url 不匹配")

    # 用户身份：优先 Authorization 头，其次 URL token（门户 SSO 跳转场景）
    auth = request.headers.get("Authorization", "")
    jwt_token = token
    if auth.lower().startswith("bearer "):
        jwt_token = auth[7:].strip()
    if not jwt_token:
        # 未登录 → 302 到门户登录页，登录成功后携带统一 JWT 回跳本 authorize
        from urllib.parse import quote
        return RedirectResponse(
            f"{settings.portal_url}/login?return={quote(str(request.url), safe='')}",
        )
    try:
        payload = decode_token(jwt_token)
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="统一 JWT 无效，请先登录门户")

    # 生成一次性授权码
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        "client_id": client_id,
        "username": payload["uid"],
        "exp": time.time() + _CODE_TTL,
    }
    if response_mode == "json":
        # E2E 演示：直接返回 code（不走 302）
        return {"code": code, "state": state, "redirect_uri": redirect_uri}
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{sep}code={code}{'&state=' + state if state else ''}")


@router.post("/oauth/token", summary="③ 令牌端点：code + client_secret → access_token / id_token")
def token(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(""),
    db: Session = Depends(get_db),
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    app = db.query(AppRegistration).filter(AppRegistration.client_id == client_id).first()
    if app is None or app.client_secret != client_secret:
        raise HTTPException(status_code=401, detail="invalid_client：client_id 或 client_secret 错误")

    info = _auth_codes.pop(code, None)  # code 一次性，取出即失效
    if info is None or info["client_id"] != client_id or info["exp"] < time.time():
        raise HTTPException(status_code=400, detail="invalid_grant：授权码无效或已过期")

    user = db.query(User).filter(User.username == info["username"]).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="invalid_grant：用户不存在或已禁用")

    # access_token 的 aud = client_id（表明"这个 token 是给哪个应用用的"）
    access_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source,
        aud=client_id,
    )
    # id_token 同样为 JWT，携带身份断言
    id_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source,
        aud=client_id,
    )
    return JSONResponse({
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer",
        "expires_in": settings.jwt_access_expire_minutes * 60,
        "scope": "openid profile",
    })


@router.get("/oauth/userinfo", summary="⑤ UserInfo 端点：Bearer access_token → 用户信息")
def userinfo(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization: Bearer access_token")
    token = authorization[7:].strip()
    try:
        payload = decode_token(token, verify_aud=False)  # userinfo 不校验具体 aud，仅验签名/过期
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="access_token 无效")
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return {
        "sub": str(user.id),
        "preferred_username": user.username,
        "name": user.display_name,
        "email": user.email,
        "department": user.department,
        "source": user.source,
    }


def _redirect_error(redirect_uri: str, error: str, state: str) -> RedirectResponse:
    """授权失败时按 OIDC 规范 302 回 redirect_uri 并带 error 参数。"""
    sep = "&" if "?" in redirect_uri else "?"
    qs = f"{urlencode({'error': error})}{'&state=' + state if state else ''}"
    return RedirectResponse(f"{redirect_uri}{sep}{qs}")
