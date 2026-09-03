"""门户 BFF（Backend for Frontend）—— 门户作为 OIDC 客户端（RP）的后端。

架构：门户 SPA 不直接持有 token，登录态走 HttpOnly Cookie（portal_session）。
Demo 中 BFF 与 IdP（认证中心）同进程部署；生产应拆分为独立服务，甚至用现成 OIDC 客户端库。

流程：
  ① GET  /portal/oauth/login
         - 生成 PKCE code_verifier / code_challenge + state + nonce
         - 302 → /oauth/authorize（门户是认证中心的第一个 OIDC 客户端）
  ② GET  /portal/oauth/callback?code=&state=
         - 校验 state（防 CSRF）
         - 用 code + code_verifier + client_secret 调 /oauth/token（机密只在后端）
         - 建立门户 BFF 会话（HttpOnly Cookie），302 回门户首页
  ③ GET  /portal/api/me → 从门户会话解析当前用户（SPA 用）
  ④ POST /portal/api/logout → 清门户会话（IdP 会话由 /oauth/logout 负责）
"""
import json
import secrets
import time
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.sessions import PORTAL_COOKIE, create_portal_session, delete_portal_session, get_portal_session
from ..db import get_db
from ..models import AppRegistration
from ..security import generate_code_verifier, pkce_challenge

settings = get_settings()
router = APIRouter(prefix="/portal", tags=["portal-bff"])

PORTAL_CLIENT_ID = "portal-app"

# BFF 进行中的 PKCE 状态（state -> code_verifier）。内存短时效，生产放 Redis/DB。
_bff_states: dict[str, dict] = {}
_STATE_TTL = 600  # 10 分钟


def _portal_client(db: Session) -> AppRegistration | None:
    return db.query(AppRegistration).filter(
        AppRegistration.client_id == PORTAL_CLIENT_ID,
        AppRegistration.enabled.is_(True),
    ).first()


def _http_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


@router.get("/oauth/login", summary="① 门户发起 OIDC 登录（PKCE → 302 授权端点）")
def portal_oauth_login(request: Request, db: Session = Depends(get_db)):
    client = _portal_client(db)
    if client is None:
        raise HTTPException(status_code=400, detail="门户 OIDC 客户端未注册（请检查 seed）")
    verifier = generate_code_verifier()
    state = secrets.token_urlsafe(16)
    _bff_states[state] = {"verifier": verifier, "exp": time.time() + _STATE_TTL}
    _cleanup_states()

    # origin 以 PORTAL_URL 为唯一权威来源（与 seed 注册的 redirect_uri 白名单严格一致）
    origin = settings.portal_url.rstrip("/")
    params = {
        "response_type": "code",
        "client_id": PORTAL_CLIENT_ID,
        "redirect_uri": f"{origin}/portal/oauth/callback",
        "scope": "openid profile",
        "state": state,
        "nonce": secrets.token_urlsafe(16),
        "code_challenge": pkce_challenge(verifier),
        "code_challenge_method": "S256",
    }
    return RedirectResponse(f"{origin}/oauth/authorize?{urllib.parse.urlencode(params)}", status_code=302)


@router.get("/oauth/callback", summary="② OIDC 回调：code + PKCE 换 token，建立门户会话")
def portal_oauth_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    request: Request = None,
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(f"<p>授权失败：{error} {error_description}</p>", status_code=400)
    # state 校验（防 CSRF）：取出即失效
    info = _bff_states.pop(state, None) if state else None
    if info is None:
        return HTMLResponse("<p>state 校验失败（防 CSRF）</p>", status_code=400)

    client = _portal_client(db)
    if client is None or not client.client_secret:
        return HTMLResponse("<p>门户客户端未配置 client_secret</p>", status_code=500)
    origin = settings.portal_url.rstrip("/")

    # 后端用 code + code_verifier + client_secret 换 token（机密不进浏览器）
    try:
        tokens = _http_form(f"{settings.oidc_base_url.rstrip('/')}/oauth/token", {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{origin}/portal/oauth/callback",
            "code_verifier": info["verifier"],
            "client_id": PORTAL_CLIENT_ID,
            "client_secret": client.client_secret,
        })
    except Exception as exc:  # noqa: BLE001
        return HTMLResponse(f"<p>换取 token 失败：{exc}</p>", status_code=502)

    user = _resolve_user_from_tokens(db, tokens)
    if user is None:
        return HTMLResponse("<p>无法从 token 解析用户</p>", status_code=401)

    sid = create_portal_session({
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "department": user.department,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "source": user.source,
    })
    resp = RedirectResponse(f"{origin}/", status_code=302)
    resp.set_cookie(key=PORTAL_COOKIE, value=sid, httponly=True, samesite="lax", max_age=8 * 3600)
    return resp


def _resolve_user_from_tokens(db: Session, tokens: dict):
    """从 id_token（优先）或 access_token 解析用户 sub。"""
    from ..models import User
    from ..security import decode_token

    for key in ("id_token", "access_token"):
        tok = tokens.get(key, "")
        if not tok:
            continue
        try:
            payload = decode_token(tok, verify_aud=False)
            user = db.get(User, int(payload.get("sub", 0)))
            if user is not None:
                return user
        except pyjwt.PyJWTError:
            continue
    return None


@router.get("/api/me", summary="③ 门户当前用户（从 HttpOnly Cookie 会话解析）")
def portal_me(request: Request):
    sid = request.cookies.get(PORTAL_COOKIE)
    session = get_portal_session(sid) if sid else None
    if session is None:
        raise HTTPException(status_code=401, detail="门户未登录")
    return session["user"]


@router.post("/api/logout", summary="④ 门户登出：清门户会话")
def portal_logout(request: Request):
    sid = request.cookies.get(PORTAL_COOKIE)
    delete_portal_session(sid)
    resp = JSONResponse({"message": "门户会话已清除"})
    resp.delete_cookie(key=PORTAL_COOKIE)
    return resp


def _cleanup_states() -> None:
    now = time.time()
    for k in [k for k, v in _bff_states.items() if v.get("exp", 0) < now]:
        _bff_states.pop(k, None)
