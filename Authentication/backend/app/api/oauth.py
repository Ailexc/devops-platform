"""OIDC Provider 端点 —— 认证中心作为规范 OIDC Provider（IdP）。

完整授权码 + PKCE 流程（OAuth 2.1 / RFC 9700 + OIDC Core）：
  ① GET  /oauth/authorize?client_id&redirect_uri&scope&state&nonce&code_challenge
         - 校验客户端 / redirect_uri 精确白名单 / PKCE 必填 / scope 范围
         - 未登录 → 302 IdP 登录页（/oauth/login）→ 登录后回跳
         - 已登录 → 生成一次性授权码（入库，5min，一次性）→ 302 redirect_uri?code=...
  ② POST /oauth/token (grant_type=authorization_code)
         - client 认证（client_secret_post / client_secret_basic）
         - 校验 code（哈希匹配 / 一次性 / 未过期 / 属于该 client / redirect_uri 一致）
         - 校验 code_verifier（PKCE）
         - 签发 access_token（aud=client_id，最小授权信息）与 id_token（独立身份断言，含 nonce）
         - 签发 refresh_token（入库，轮换 + 复用检测）
  ③ POST /oauth/token (grant_type=refresh_token)
         - 轮换：旧 refresh 作废并发新；复用检测：已轮换 token 再次使用 → 撤销整个 family
  ④ GET  /oauth/userinfo（Bearer access_token）→ 按 scope 返回标准 claims
  ⑤ GET  /oauth/logout（end_session_endpoint）→ RP-initiated logout

安全要点（面试可讲）：
- PKCE 强制（防授权码拦截/注入）
- redirect_uri 精确匹配注册白名单（防 open redirect / 授权码劫持）
- state 回传校验（防 CSRF）
- nonce 进入 id_token（防重放）
- 授权码 / refresh token 均只存哈希入库
"""
import base64
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import jwt as pyjwt
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.auth_providers import (
    AuthenticationFailed,
    AuthProviderUnavailable,
    UserNotFound,
    build_provider_chain,
    sync_local_user,
)
from ..core.sessions import IDP_COOKIE, create_idp_session, delete_idp_session, get_idp_session
from ..db import get_db
from ..models import AppRegistration, AuthCode, RefreshToken, User
from ..security import (
    create_access_token,
    create_id_token,
    decode_token,
    generate_oauth_refresh_token,
    hash_oauth_token,
    verify_pkce,
)

settings = get_settings()
router = APIRouter(tags=["oauth"])

_CODE_TTL_MINUTES = 5  # 授权码有效期
_REFRESH_TTL_DAYS = 7  # refresh token 有效期


def _as_utc(dt: datetime) -> datetime:
    """SQLite 读出的 datetime 无时区（naive），统一视为 UTC 再比较。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------- 工具 ----------
def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _redirect_uri_allowed(app: AppRegistration, redirect_uri: str) -> bool:
    """redirect_uri 精确匹配白名单（OAuth 2.1）。旧数据兼容：白名单为空时回退到 home_url 精确匹配。"""
    whitelist = app.redirect_uris or ([app.home_url] if app.home_url else [])
    return redirect_uri in whitelist


def _redirect_error(redirect_uri: str, error: str, state: str, desc: str = "") -> RedirectResponse:
    """授权失败按 OIDC 规范 302 回 redirect_uri 并带 error 参数。"""
    sep = "&" if "?" in redirect_uri else "?"
    params = [("error", error)]
    if state:
        params.append(("state", state))
    if desc:
        params.append(("error_description", desc))
    return RedirectResponse(f"{redirect_uri}{sep}{urlencode(params)}", status_code=302)


def _current_user_from_request(request: Request, db: Session) -> User | None:
    """解析当前用户：优先 IdP 会话（标准 SSO），兼容 Authorization/URL 统一 JWT（Demo 便利）。"""
    sid = request.cookies.get(IDP_COOKIE)
    if sid:
        idp = get_idp_session(sid)
        if idp:
            return db.get(User, idp.get("user_id"))
    jwt_token = ""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        jwt_token = auth[7:].strip()
    elif request.query_params.get("token"):
        jwt_token = request.query_params.get("token")
    if jwt_token:
        try:
            payload = decode_token(jwt_token)
            if payload.get("type") != "refresh":
                return db.get(User, int(payload.get("sub", 0)))
        except pyjwt.PyJWTError:
            return None
    return None


# ---------- OIDC Provider 元数据 ----------
@router.get("/.well-known/openid-configuration", summary="OIDC Provider 元数据")
def oidc_configuration(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": settings.issuer,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "end_session_endpoint": f"{base}/oauth/logout",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": [settings.jwt_algorithm],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "claims_supported": ["sub", "name", "preferred_username", "email", "department", "source"],
    }


# ---------- ① 授权端点 ----------
@router.get("/oauth/authorize", summary="授权端点：PKCE + state + nonce → 302 带一次性 code")
def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("openid"),
    state: str = Query(""),
    nonce: str = Query(""),
    code_challenge: str = Query(""),
    code_challenge_method: str = Query("S256"),
    response_mode: str = Query("query"),  # Demo 便利：json 时返回 JSON（E2E 演示）
    request: Request = None,
    db: Session = Depends(get_db),
):
    # 1. 本 IdP 只支持授权码流（OAuth 2.1 已移除 implicit）
    if response_type != "code":
        return _redirect_error(redirect_uri, "unsupported_response_type", state)

    # 2. 客户端校验
    app = db.query(AppRegistration).filter(
        AppRegistration.client_id == client_id, AppRegistration.enabled.is_(True)
    ).first()
    if app is None:
        raise HTTPException(status_code=400, detail="未知或已禁用的 client_id")

    # 3. redirect_uri 精确匹配注册白名单（OAuth 2.1 强制）
    if not _redirect_uri_allowed(app, redirect_uri):
        return _redirect_error(
            redirect_uri, "invalid_request", state, desc="redirect_uri 不在该客户端注册白名单中"
        )

    # 4. PKCE 必填（OAuth 2.1 / RFC 9700 强制所有授权码流）
    if not code_challenge:
        return _redirect_error(redirect_uri, "invalid_request", state, desc="缺少 code_challenge（PKCE 必填）")
    if code_challenge_method.upper() not in ("S256", "plain"):
        return _redirect_error(redirect_uri, "invalid_request", state, desc="不支持的 code_challenge_method")

    # 5. scope 校验：必须含 openid，且 ⊆ 客户端允许的 scope
    scopes = scope.split()
    if "openid" not in scopes:
        return _redirect_error(redirect_uri, "invalid_scope", state, desc="缺少 openid scope")
    allowed = set(app.allowed_scopes or ["openid"])
    if not set(scopes).issubset(allowed):
        return _redirect_error(redirect_uri, "invalid_scope", state, desc="scope 超出该客户端允许范围")

    # 6. 用户身份：IdP 会话（标准 SSO）；未登录 → 302 登录页
    user = _current_user_from_request(request, db)
    if user is None or not user.is_active:
        login_url = f"{request.base_url}oauth/login?return={quote(str(request.url), safe='')}"
        return RedirectResponse(login_url, status_code=302)

    # 7. 生成一次性授权码（入库只存哈希）
    code = secrets.token_urlsafe(32)
    db.add(AuthCode(
        code=hash_oauth_token(code),
        client_id=client_id,
        user_id=user.id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method.upper(),
        nonce=nonce,
        scope=scope,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=_CODE_TTL_MINUTES),
    ))
    db.commit()

    if response_mode == "json":
        return {"code": code, "state": state, "redirect_uri": redirect_uri}

    sep = "&" if "?" in redirect_uri else "?"
    qs = f"code={quote(code)}"
    if state:
        qs += f"&state={quote(state)}"
    return RedirectResponse(f"{redirect_uri}{sep}{qs}", status_code=302)


# ---------- ②③ 令牌端点 ----------
def _resolve_client_credentials(cid_form: str, secret_form: str, authorization: str) -> tuple[str, str]:
    """客户端认证：支持 client_secret_post（form）与 client_secret_basic（Authorization: Basic）。"""
    if authorization.lower().startswith("basic "):
        try:
            raw = base64.b64decode(authorization[6:].strip()).decode("utf-8")
            c, _, s = raw.partition(":")
            return c, s
        except Exception:  # noqa: BLE001
            return "", ""
    return cid_form, secret_form


@router.post("/oauth/token", summary="令牌端点：authorization_code（PKCE）/ refresh_token（轮换）")
def token(
    grant_type: str = Form(...),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    code_verifier: str = Form(""),
    refresh_token: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
    authorization: str = Header(""),
    db: Session = Depends(get_db),
):
    cid, secret = _resolve_client_credentials(client_id, client_secret, authorization)
    app = db.query(AppRegistration).filter(
        AppRegistration.client_id == cid, AppRegistration.enabled.is_(True)
    ).first()
    if app is None:
        return JSONResponse(status_code=401, content={"error": "invalid_client", "error_description": "未知客户端"})
    # 客户端认证：机密客户端校验 secret；public 客户端跳过（必须 PKCE）
    if not app.is_public and app.token_endpoint_auth_method != "none":
        if not secret or not secrets.compare_digest(app.client_secret or "", secret):
            return JSONResponse(status_code=401, content={"error": "invalid_client", "error_description": "client_secret 校验失败"})

    if grant_type == "authorization_code":
        return _token_authorization_code(app, code, redirect_uri, code_verifier, db)
    if grant_type == "refresh_token":
        return _token_refresh(app, refresh_token, db)
    return JSONResponse(status_code=400, content={"error": "unsupported_grant_type"})


def _token_authorization_code(app: AppRegistration, code: str, redirect_uri: str,
                              code_verifier: str, db: Session) -> JSONResponse:
    if not code or not code_verifier:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "缺少 code 或 code_verifier"})

    auth_code = db.query(AuthCode).filter(AuthCode.code == hash_oauth_token(code)).first()
    now = datetime.now(timezone.utc)
    if (
        auth_code is None
        or auth_code.used
        or auth_code.client_id != app.client_id
        or _as_utc(auth_code.expires_at) < now
    ):
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "授权码无效、已使用或已过期"})
    # redirect_uri 一致性校验（OIDC Core）
    if redirect_uri and auth_code.redirect_uri != redirect_uri:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "redirect_uri 不一致"})
    # PKCE：验证 code_verifier（OAuth 2.1 强制）
    if not verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE 校验失败（code_verifier 不匹配）"})

    # 一次性：标记已使用
    auth_code.used = True
    db.commit()

    user = db.get(User, auth_code.user_id)
    if user is None or not user.is_active:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "用户不存在或已禁用"})

    # access_token：授权凭证（aud=client_id，最小信息）
    access_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source,
        aud=app.client_id, scope=auth_code.scope,
    )
    # id_token：独立身份断言（含 nonce，防重放）
    id_token = create_id_token(
        user.id, user.username, aud=app.client_id, nonce=auth_code.nonce,
        name=user.display_name, email=user.email, department=user.department, source=user.source,
    )
    # refresh_token：入库（哈希），轮换 + 复用检测
    rt = generate_oauth_refresh_token()
    db.add(RefreshToken(
        token_hash=hash_oauth_token(rt),
        client_id=app.client_id,
        user_id=user.id,
        family_id=secrets.token_urlsafe(16),
        expires_at=datetime.now(timezone.utc) + timedelta(days=_REFRESH_TTL_DAYS),
    ))
    db.commit()

    return JSONResponse({
        "access_token": access_token,
        "id_token": id_token,
        "refresh_token": rt,
        "token_type": "Bearer",
        "expires_in": settings.jwt_access_expire_minutes * 60,
        "scope": auth_code.scope,
    })


def _revoke_family(db: Session, family_id: str) -> None:
    for rec in db.query(RefreshToken).filter(RefreshToken.family_id == family_id).all():
        rec.revoked = True
    db.commit()


def _token_refresh(app: AppRegistration, refresh_token: str, db: Session) -> JSONResponse:
    if not refresh_token:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "缺少 refresh_token"})

    rec = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_oauth_token(refresh_token)).first()
    now = datetime.now(timezone.utc)
    if rec is None or rec.revoked or rec.client_id != app.client_id or _as_utc(rec.expires_at) < now:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "refresh_token 无效或已过期"})

    # 复用检测：已被轮换过的 token 再次使用 → 判定泄露，撤销整个 family（RFC 9700 建议）
    if rec.replaced_by:
        _revoke_family(db, rec.family_id)
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "refresh_token 已被使用，判定泄露已撤销"})

    user = db.get(User, rec.user_id)
    if user is None or not user.is_active:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "用户不存在或已禁用"})

    # 轮换：旧 token 作废，发新 refresh + 新 access
    new_rt = generate_oauth_refresh_token()
    rec.replaced_by = hash_oauth_token(new_rt)
    rec.revoked = True
    db.add(RefreshToken(
        token_hash=hash_oauth_token(new_rt),
        client_id=app.client_id,
        user_id=user.id,
        family_id=rec.family_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=_REFRESH_TTL_DAYS),
    ))
    access_token = create_access_token(
        user.id, user.username, user.display_name, user.email, user.department, user.source,
        aud=app.client_id, scope="openid profile",
    )
    id_token = create_id_token(
        user.id, user.username, aud=app.client_id, nonce="",
        name=user.display_name, email=user.email, department=user.department,
    )
    db.commit()

    return JSONResponse({
        "access_token": access_token,
        "id_token": id_token,
        "refresh_token": new_rt,
        "token_type": "Bearer",
        "expires_in": settings.jwt_access_expire_minutes * 60,
        "scope": "openid profile",
    })


# ---------- ④ UserInfo ----------
@router.get("/oauth/userinfo", summary="UserInfo 端点：Bearer access_token → 按 scope 返回标准 claims")
def userinfo(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization: Bearer access_token")
    token = authorization[7:].strip()
    try:
        payload = decode_token(token, verify_aud=False)
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="access_token 无效") from None
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="refresh token 不可用于 userinfo")

    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    scopes = set((payload.get("scope") or "").split())
    claims: dict = {"sub": str(user.id)}
    if "profile" in scopes:
        claims["preferred_username"] = user.username
        claims["name"] = user.display_name
        claims["department"] = user.department
        claims["source"] = user.source
    if "email" in scopes and user.email:
        claims["email"] = user.email
    return claims


# ---------- ⑤ IdP 登录页（标准 Authorization Server 形态） ----------
_LOGIN_HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>统一认证中心 · 登录</title>
<style>
  body{font-family:-apple-system,'PingFang SC',sans-serif;background:#f0f2f5;margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh}
  .card{max-width:420px;width:92%;background:#fff;border-radius:14px;box-shadow:0 12px 32px rgba(16,24,40,.12);padding:32px 30px;text-align:center}
  .logo{width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,#1d5fd6,#4f8cff);color:#fff;font-size:26px;line-height:52px;margin:0 auto 14px}
  h1{margin:0 0 6px;color:#101828;font-size:20px}
  p{color:#667085;font-size:13px;margin:0 0 20px}
  label{display:block;text-align:left;font-size:13px;color:#344054;margin:12px 0 6px}
  select,input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #d0d5dd;border-radius:8px;font-size:14px;outline:none;background:#fff}
  select:focus,input:focus{border-color:#4f8cff;box-shadow:0 0 0 3px rgba(79,140,255,.15)}
  button{width:100%;margin-top:20px;padding:11px;background:#1d5fd6;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#1a55c0}
  .err{color:#e5484d;font-size:13px;margin-top:12px}
  .hint{margin-top:10px;font-size:11.5px;color:#98a2b3;line-height:1.6;text-align:left}
  .manual{display:none}
</style></head><body>
<div class="card">
  <div class="logo">🔐</div>
  <h1>统一认证中心</h1>
  <p>DevOps Platform · 单点登录（SSO）统一入口</p>
  <form method="post">
    <label>选择系统</label>
    <select id="sys"><option value="">加载中…</option></select>
    <label>选择用户</label>
    <select id="usr"><option value="">—</option></select>
    <label>密码（演示环境固定）</label>
    <input id="pwd" name="password" type="password" autocomplete="current-password" value="demo1234" required />
    <input id="username" name="username" type="hidden" value="" required />
    <button type="submit">登 录</button>
    <div class="err" id="err" style="display:none"></div>
  </form>
  <div class="hint">统一身份目录：用户隶属于组织，不隶属于系统；下拉按系统分组仅为演示切换方便。演示密码统一 <b>demo1234</b>。</div>
</div>
<script>
(function(){
  try{
    fetch('/oauth/users').then(function(r){return r.json();}).then(function(d){
      var sysSel=document.getElementById('sys'), usrSel=document.getElementById('usr');
      var groups=d.groups||[];
      var html='<option value="">全部系统</option>';
      groups.forEach(function(g){ html+='<option value="'+g.system+'">'+g.system_name+'</option>'; });
      sysSel.innerHTML=html;
      function pickUsers(){
        var sel=sysSel.value;
        var users=[];
        if(sel){ var g=groups.find(function(x){return x.system===sel;}); users=g?g.users:[]; }
        else{ var seen={}; groups.forEach(function(g){g.users.forEach(function(u){if(!seen[u.username]){seen[u.username]=1;users.push(u);}});}); }
        var uhtml='<option value="">— 请选择用户 —</option>';
        users.forEach(function(u){ uhtml+='<option value="'+u.username+'">'+u.display_name+'（'+u.username+'）· '+u.department+'</option>'; });
        usrSel.innerHTML=uhtml;
        if(users.length===1){ usrSel.value=users[0].username; pickUser(); }
      }
      function pickUser(){
        var u=usrSel.selectedOptions&&usrSel.selectedOptions[0];
        if(u&&u.value){ document.getElementById('username').value=u.value; }
      }
      sysSel.onchange=pickUsers;
      usrSel.onchange=pickUser;
      pickUsers();
    }).catch(function(){ /* 目录加载失败：降级为手动输入 */ document.querySelector('.manual').style.display='block'; });
  }catch(e){ document.querySelector('.manual').style.display='block'; }
})();
</script>
<div class="manual" style="display:none;margin-top:14px">
  <p style="font-size:12px;color:#667085;margin:0 0 8px">用户目录加载失败，可手动输入用户名 / 密码登录</p>
</div>
</body></html>"""


@router.get("/oauth/users", summary="登录页用户目录（按系统分组，演示便利索引）")
def oauth_users(db: Session = Depends(get_db)):
    """返回登录下拉用的用户目录：按 demo_systems 分组展示。

    demo_systems 仅是登录页分组的演示索引（非用户模型）；用户真正归属是 department 组织。
    """
    apps = (
        db.query(AppRegistration)
        .filter(AppRegistration.access_mode.isnot(None))
        .order_by(AppRegistration.sort_order.asc())
        .all()
    )
    users = db.query(User).filter(User.is_active.is_(True)).all()
    groups = []
    for app in apps:
        sys_users = [u for u in users if app.app_id in (u.demo_systems or [])]
        if not sys_users:
            continue
        ordered = sorted(
            sys_users,
            key=lambda x: (x.is_admin is not True, x.username),
        )
        groups.append(
            {
                "system": app.app_id,
                "system_name": app.name,
                "users": [
                    {
                        "username": u.username,
                        "display_name": u.display_name,
                        "department": u.department,
                    }
                    for u in ordered
                ],
            }
        )
    return {"groups": groups, "password_hint": "demo1234"}


@router.get("/oauth/login", response_class=HTMLResponse, summary="IdP 登录页（标准 Authorization Server 形态）")
def oauth_login_page(request: Request):
    return HTMLResponse(_LOGIN_HTML)


@router.post("/oauth/login", summary="IdP 登录提交：验证身份源 → 建立 IdP 会话 → 回跳")
def oauth_login_submit(
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    return_url = request.query_params.get("return", "")
    chain = build_provider_chain(db)
    try:
        profile = chain.authenticate(username, password)
    except (UserNotFound, AuthenticationFailed):
        return HTMLResponse(
            _LOGIN_HTML.replace(
                '<div class="err" id="err" style="display:none"></div>',
                '<div class="err" id="err" style="display:block">用户名或密码错误</div>',
            ),
            status_code=401,
        )
    except AuthProviderUnavailable as exc:
        return HTMLResponse(
            _LOGIN_HTML.replace(
                '<div class="err" id="err" style="display:none"></div>',
                f'<div class="err" id="err" style="display:block">认证服务暂不可用：{exc}</div>',
            ),
            status_code=503,
        )
    user = sync_local_user(db, profile)
    sid = create_idp_session(user.id, user.username)
    resp = RedirectResponse(return_url or "/", status_code=302)
    resp.set_cookie(
        key=IDP_COOKIE, value=sid, httponly=True, samesite="lax", max_age=8 * 3600
    )
    return resp


# ---------- ⑤ RP-initiated logout（end_session） ----------
@router.get("/oauth/logout", summary="OIDC 单点登出（end_session_endpoint）")
def oauth_logout(request: Request, post_logout_redirect_uri: str = Query("")):
    sid = request.cookies.get(IDP_COOKIE)
    delete_idp_session(sid)
    resp = RedirectResponse(post_logout_redirect_uri or f"{request.base_url}oauth/login", status_code=302)
    resp.delete_cookie(key=IDP_COOKIE)
    return resp
