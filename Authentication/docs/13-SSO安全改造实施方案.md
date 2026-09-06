# SSO 安全改造实施方案

> 状态：待评审  
> 范围：Authentication 认证中心 / 统一网关 / 门户 / 6 个业务系统  
> 目标：消除 URL 裸露 Token，门户登录零点击，三种接入方式安全规范可叙事

---

## 一、问题诊断

### 1.1 当前架构断裂

```
门户 BFF 登录（OIDC，Token 不进浏览器 ✅）
    ↓ 点击应用卡片
    ↓ /api/auth/sso-url 生成 home_url?token=<JWT>
    ↓ 浏览器跳转，JWT 裸露在 URL 上  ← ❌ 安全问题
    ↓ 前端读 token → localStorage → 带 Authorization 头调 API
    ↓ 网关 forwardAuth 每请求验 JWT（无状态）  ← ❌ 不规范
```

### 1.2 具体问题清单

| # | 问题 | 位置 | 风险等级 |
|---|------|------|----------|
| 1 | **JWT 裸露在 URL 参数** | `auth.py:183` sso-url 端点 | 🔴 高 |
| 2 | **网关 forwardAuth 无状态** | `dynamic.yml` auth-forward | 🟠 中 |
| 3 | **门户登录需点击按钮** | `LoginPage.tsx` | 🟡 体验 |
| 4 | **前端 localStorage 持有 Token** | 各系统 `main.ts/tsx/js` | 🟠 中 |
| 5 | **verify 端点兼容 URL token** | `auth.py:200` query_params | 🔴 高 |

### 1.3 安全风险详析

**JWT 在 URL 上的风险**（RFC 6749 §4.2.2、RFC 9700 §4.1 明确反对）：
- 浏览器历史记录泄露
- Referer 头泄露（HTTP → HTTPS 跳转时）
- 服务器访问日志记录
- 代理服务器日志记录
- 共享电脑的 URL 栏残留

---

## 二、业界标准依据

### 2.1 IETF 规范

| 规范 | 要点 |
|------|------|
| **RFC 6749 §4.2.2** | "The authorization server MUST NOT issue access tokens in the authorization endpoint response"（隐式流已废弃） |
| **RFC 9700 §4.1** | "Access tokens should not be passed in the URL" |
| **draft-ietf-oauth-browser-based-apps §6.1** | BFF 模式：Token 永远不进浏览器，BFF 用 HttpOnly Cookie 维护会话 |
| **RFC 6265** | Cookie 域名不含端口——同 IP 不同端口可共享 Cookie |

### 2.2 业界标准架构

**Keycloak + Kong / Okta + API Gateway / Auth0 + Nginx** 的标准做法：

```
┌─────────────────────────────────────────────────────────────┐
│                     浏览器（SPA）                            │
│  只持有 HttpOnly Session Cookie，不持有任何 Token            │
└─────────────────────────┬───────────────────────────────────┘
                          │ 所有请求自动带 Cookie
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              统一网关（Traefik / Kong / Nginx）               │
│                                                              │
│  ① 收到请求，检查 Session Cookie                             │
│  ② 有有效 Session → 注入 X-Auth-* 头 → 放行到后端           │
│  ③ 无 Session → 返回 401 → 前端跳登录                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ X-Auth-User / X-Auth-Username
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              业务后端（零鉴权代码，只读 X-Auth-* 头）         │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**：
1. Token 永远不进浏览器（BFF 服务端持有）
2. 浏览器只用 HttpOnly Cookie（JavaScript 不可读）
3. 网关维护会话（有状态），不是每请求验 JWT（无状态）
4. 会话 Cookie 设在网关域名/IP 上，所有端口共享

---

## 三、目标架构

### 3.1 改造后架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                          浏览器                                  │
│                                                                  │
│  持有：_gw_session（HttpOnly Cookie，网关 IP 域，所有端口共享）  │
│  不持有：任何 JWT / Token                                        │
└─────────────────────────────┬────────────────────────────────────┘
                              │ 所有请求自动带 _gw_session Cookie
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    统一网关 Traefik                               │
│                                                                  │
│  forwardAuth → /api/auth/verify                                  │
│    ├─ 读 _gw_session Cookie → 验证会话 → 注入 X-Auth-* 头       │
│    ├─ 无 Cookie → 401                                            │
│    └─ 会话过期 → 401                                             │
│                                                                  │
│  addAuthCookiesToResponse: ["_gw_session"]                       │
│  （认证服务器 Set-Cookie 透传给浏览器）                          │
└─────────────────────────────┬────────────────────────────────────┘
                              │ X-Auth-User / X-Auth-Username
                              │ X-Auth-Name / X-Auth-Source
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              业务后端（零鉴权代码，只读 X-Auth-* 头）             │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    认证中心 FastAPI                               │
│                                                                  │
│  ┌─ /api/auth/verify    网关 forwardAuth 校验（Session 优先）    │
│  ├─ /api/auth/sso-url   返回干净 URL（不带 token）              │
│  ├─ /oauth/authorize    OIDC 授权端点                            │
│  ├─ /oauth/token        OIDC 令牌端点                            │
│  ├─ /portal/oauth/*     门户 BFF（PKCE → 换 token → 建会话）    │
│  └─ 会话存储            _GW_SESSIONS（内存/Demo，生产 Redis）    │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 三种接入方式的安全边界

| 接入方式 | 适用场景 | Token 位置 | 认证链路 |
|----------|----------|------------|----------|
| **方式一：网关会话** | 内部系统，网关可覆盖 | 服务端（认证中心） | 浏览器 Cookie → 网关验证 → X-Auth-* 头 |
| **方式二：一次性授权码** | 跨网络，网关覆盖不到 | 服务端（业务后端） | 浏览器 ?code= → 业务后端换 JWT → 本地验签 |
| **方式三：OIDC 客户端** | 外部/异构系统 | 服务端（业务后端） | 标准授权码 + PKCE → 后端换 token |

**关键改进**：方式一和方式二的 Token 都不再进浏览器 URL。

### 3.3 方式二改进说明

当前方式二（直连 JWKS）的问题：JWT 通过 URL 传给前端，前端存 localStorage。

改造后：
```
门户 BFF 生成一次性授权码（非 JWT，UUID，60s 有效期）
    ↓ 跳转 home_url?code=<一次性授权码>
    ↓ 业务后端收到 code → 调认证中心 /oauth/token 换 JWT
    ↓ JWT 不进浏览器，业务后端本地持有
    ↓ 浏览器只持有业务后端的 Session Cookie
```

这本质上是 OIDC 授权码流的简化版——Token 不进浏览器，授权码一次性用完即毁。

---

## 四、详细改造清单

### 4.1 门户登录零点击（体验优化）

**问题**：当前 `LoginPage.tsx` 显示一个"前往统一认证中心登录"按钮，用户需点击才跳转。

**规范做法**：未认证时直接跳转 OIDC 授权端点，不显示中间页。

**改动文件**：`Authentication/frontend/src/pages/LoginPage.tsx`

**改造前**：
```tsx
// 检查会话 → 无会话 → 显示按钮 → 用户点击 → 跳转
const goLogin = () => {
  window.location.href = '/portal/oauth/login'
}
return <Button onClick={goLogin}>前往统一认证中心登录</Button>
```

**改造后**：
```tsx
// 检查会话 → 无会话 → 直接跳转（不显示按钮）
useEffect(() => {
  portalApi.me()
    .then(({ data }) => {
      useAuthStore.getState().setUser(data)
      nav('/', { replace: true })
    })
    .catch(() => {
      // 无会话 → 直接跳 OIDC 授权端点
      window.location.href = '/portal/oauth/login'
    })
}, [nav])
```

**保留降级**：跳转前显示 500ms Loading（"正在跳转到认证中心…"），防止白屏闪烁。若 JS 禁用，noscript 标签提供手动链接。

---

### 4.2 网关会话改造（核心安全改造）

#### 4.2.1 认证中心：新增网关会话存储

**改动文件**：`Authentication/backend/app/core/sessions.py`

新增 `_GW_SESSIONS` 存储，与现有 `_IDP_SESSIONS` / `_PORTAL_SESSIONS` 并列：

```python
_GW_SESSIONS: dict[str, dict] = {}
GW_COOKIE = "_gw_session"  # 网关会话 cookie 名

def create_gateway_session(user_info: dict) -> str:
    """创建网关会话。user_info 含 id/username/display_name/email/department/source。"""
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
```

#### 4.2.2 认证中心：verify 端点支持 Session

**改动文件**：`Authentication/backend/app/api/auth.py`

**改造前**（只验 JWT）：
```python
@router.get("/verify")
def verify(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    else:
        token = request.query_params.get("token", "")  # ← 问题：兼容 URL token
    # ... 验 JWT ...
```

**改造后**（Session 优先，JWT 兜底）：
```python
@router.get("/verify")
def verify(request: Request, db: Session = Depends(get_db)):
    # 1. 优先检查网关 Session Cookie
    gw_sid = request.cookies.get(GW_COOKIE)
    session = get_gateway_session(gw_sid)
    if session:
        user = db.get(User, session["user_id"])
        if user and user.is_active:
            return _build_verify_response(user)

    # 2. 无 Session → 退回到 Bearer JWT 验证（兼容直连 JWKS 链路）
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        try:
            payload = decode_token(token, verify_aud=False)
            if payload.get("type") != "refresh":
                user = db.get(User, int(payload.get("sub", 0)))
                if user and user.is_active:
                    # JWT 有效 → 自动创建网关 Session（后续请求走 Cookie）
                    sid = create_gateway_session({
                        "id": user.id, "username": user.username,
                        "display_name": user.display_name, "email": user.email,
                        "department": user.department, "source": user.source,
                    })
                    resp = _build_verify_response(user)
                    resp.set_cookie(GW_COOKIE, sid, httponly=True, samesite="lax", max_age=SESSION_TTL)
                    return resp
        except Exception:
            pass

    # 3. 都没有 → 401
    return JSONResponse(status_code=401, content={"code": 401, "user": None})
```

**删除**：`request.query_params.get("token", "")` 这行——URL token 不再是合法认证方式。

#### 4.2.3 认证中心：sso-url 端点返回干净 URL

**改动文件**：`Authentication/backend/app/api/auth.py`

**改造前**：
```python
token = create_access_token(user.id, user.username, ...)
sep = "&" if "?" in app.home_url else "?"
return {"url": f"{app.home_url}{sep}token={token}", "app": app.name}
```

**改造后**：
```python
# 方式一（网关接入）：返回干净 URL，网关 Session Cookie 自动随请求发送
if app.access_mode == "gateway":
    return {"url": app.home_url, "app": app.name}

# 方式二（直连 JWKS）：返回带一次性授权码的 URL（非 JWT）
if app.access_mode == "direct" and app.sso_type != "oidc":
    code = create_onetime_code(user)  # UUID，60s 有效期
    sep = "&" if "?" in app.home_url else "?"
    return {"url": f"{app.home_url}{sep}code={code}", "app": app.name}

# 方式三（OIDC 客户端）：跳转 OIDC 授权端点（已有逻辑，不变）
url = f"{app.home_url.rstrip('/')}/oauth/login" if app.app_id == "release-manager" else app.home_url
return {"url": url, "app": app.name}
```

#### 4.2.4 认证中心：门户 BFF 登录时设置网关 Session

**改动文件**：`Authentication/backend/app/api/portal.py`

在 `portal_oauth_callback` 中，创建门户会话的同时创建网关会话：

```python
# 现有：创建门户会话
sid = create_portal_session({...})
resp = RedirectResponse(f"{origin}/", status_code=302)
resp.set_cookie(key=PORTAL_COOKIE, value=sid, httponly=True, samesite="lax", max_age=8*3600)

# 新增：同时创建网关会话（关键！）
gw_sid = create_gateway_session({
    "id": user.id, "username": user.username,
    "display_name": user.display_name, "email": user.email,
    "department": user.department, "source": user.source,
})
resp.set_cookie(key=GW_COOKIE, value=gw_sid, httponly=True, samesite="lax", max_age=8*3600)

return resp
```

#### 4.2.5 认证中心：新增一次性授权码端点

**改动文件**：`Authentication/backend/app/api/auth.py` + `sessions.py`

用于方式二（直连 JWKS）的安全跳转：

```python
# sessions.py 新增
_ONETIME_CODES: dict[str, dict] = {}

def create_onetime_code(user) -> str:
    """生成一次性授权码（非 JWT，UUID，60s 有效期，用完即毁）。"""
    code = secrets.token_urlsafe(32)
    _ONETIME_CODES[code] = {
        "user_id": user.id, "username": user.username,
        "display_name": user.display_name, "email": user.email,
        "department": user.department, "source": user.source,
        "exp": time.time() + 60,
    }
    return code

def redeem_onetime_code(code: str) -> dict | None:
    """兑换一次性授权码，用完即毁。"""
    info = _ONETIME_CODES.pop(code, None)
    if info and info["exp"] > time.time():
        return info
    return None
```

```python
# auth.py 新增端点
@router.post("/redeem-code", summary="一次性授权码兑换 JWT")
def redeem_code(code: str = Body(..., embed=True), db: Session = Depends(get_db)):
    info = redeem_onetime_code(code)
    if not info:
        raise HTTPException(status_code=401, detail="授权码无效或已过期")
    token = create_access_token(info["user_id"], info["username"], info["display_name"],
                                 info["email"], info["department"], info["source"])
    return {"access_token": token, "token_type": "bearer"}
```

#### 4.2.6 Traefik 配置：透传 Cookie

**改动文件**：`infra/gateway/dynamic/routes.yml.template` + `Authentication/gateway/dynamic/dynamic.yml`

```yaml
auth-forward:
  forwardAuth:
    address: "http://authentication-auth-backend:8000/api/auth/verify"
    trustForwardHeader: true
    authResponseHeaders:
      - "X-Auth-User"
      - "X-Auth-Username"
      - "X-Auth-Name"
      - "X-Auth-Source"
    # 新增：从认证服务器透传 Set-Cookie 到浏览器
    addAuthCookiesToResponse:
      - "_gw_session"
```

---

### 4.3 业务系统前端改造

#### 4.3.1 方式一系统（网关接入）：移除 URL token 消费

**受影响系统**：CloudManager / WorkFlowCenter / PermissionCenter

**改动点**：各系统 `main.ts/tsx/js` 中移除 URL token 读取逻辑。

**改造前**（以 CloudManager 为例）：
```ts
function consumeSSOToken() {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')
  if (token) {
    localStorage.setItem('access_token', token)
    window.history.replaceState({}, '', window.location.pathname)
    return true
  }
  return false
}
```

**改造后**：
```ts
// 方式一（网关接入）：Token 不进浏览器，网关 Session Cookie 自动随请求发送
// 前端无需任何 token 消费逻辑，直接调 API 即可
// 若 API 返回 401，跳转门户登录页
```

**API 拦截器改造**：
```ts
// 移除 localStorage 读取 token 的逻辑
// 改为：401 时跳转门户登录
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = 'http://192.168.3.155:8088/login'
    }
    return Promise.reject(err)
  },
)
```

#### 4.3.2 方式二系统（直连 JWKS）：用授权码换 JWT

**受影响系统**：TaskManager / EventManager

**改动点**：各系统 `main.js/tsx` 中用授权码换 JWT。

**改造前**：
```js
const ssoToken = new URLSearchParams(window.location.search).get('token')
if (ssoToken) {
  localStorage.setItem('cmdb.token', ssoToken)
  window.history.replaceState({}, '', window.location.pathname)
}
```

**改造后**：
```js
const code = new URLSearchParams(window.location.search).get('code')
if (code) {
  // 用一次性授权码向认证中心兑换 JWT（后端完成，Token 不进 URL）
  const resp = await fetch('http://192.168.3.155:8099/api/auth/redeem-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
  const { access_token } = await resp.json()
  localStorage.setItem('cmdb.token', access_token)
  window.history.replaceState({}, '', window.location.pathname)
}
```

#### 4.3.3 方式三系统（OIDC 客户端）：不变

**受影响系统**：ReleaseManager

**说明**：已走标准 OIDC 授权码 + PKCE 流程，Token 不进浏览器 URL，无需改造。

---

### 4.4 登出链路完善

**改动文件**：`Authentication/backend/app/api/portal.py` + `auth.py`

登出时清除所有会话：

```python
# /portal/api/logout 改造
@router.post("/api/logout")
def portal_logout(request: Request):
    # 清除门户会话
    portal_sid = request.cookies.get(PORTAL_COOKIE)
    delete_portal_session(portal_sid)
    
    # 清除网关会话
    gw_sid = request.cookies.get(GW_COOKIE)
    delete_gateway_session(gw_sid)
    
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(PORTAL_COOKIE)
    resp.delete_cookie(GW_COOKIE)
    return resp
```

---

## 五、完整流程对比

### 5.1 门户登录流程

**改造前**：
```
访问门户 → RequireAuth 检查 → 无会话 → 跳 /login
→ 显示"前往统一认证中心登录"按钮 → 用户点击
→ 跳 /portal/oauth/login → OIDC 授权码流 → 回调 → 建门户会话
→ 跳回首页
```

**改造后**：
```
访问门户 → RequireAuth 检查 → 无会话 → 跳 /login
→ 自动跳 /portal/oauth/login（不显示按钮）
→ OIDC 授权码流 → 回调 → 建门户会话 + 网关会话
→ 跳回首页
```

### 5.2 方式一：网关会话（云管/工单/权限）

**改造前**：
```
点击应用卡片 → /api/auth/sso-url → home_url?token=<JWT>
→ 浏览器跳转（JWT 裸露在 URL）
→ 前端读 token → localStorage → 带 Authorization 头调 API
→ 网关 forwardAuth 验 JWT
```

**改造后**：
```
点击应用卡片 → /api/auth/sso-url → home_url（干净 URL）
→ 浏览器跳转（自动带 _gw_session Cookie）
→ 网关 forwardAuth 读 Cookie → 验证会话 → 注入 X-Auth-* 头
→ 业务后端读 X-Auth-* 头 → 正常工作
```

### 5.3 方式二：一次性授权码（任务/事件）

**改造前**：
```
点击应用卡片 → /api/auth/sso-url → home_url?token=<JWT>
→ 浏览器跳转（JWT 裸露在 URL）
→ 前端读 token → localStorage → 带 Authorization 头调 API
→ 业务后端本地验 JWKS
```

**改造后**：
```
点击应用卡片 → /api/auth/sso-url → home_url?code=<一次性授权码>
→ 浏览器跳转（授权码非 JWT，泄露无害，一次性用完即毁）
→ 前端用 code 调认证中心 /api/auth/redeem-code 换 JWT
→ JWT 不进 localStorage，业务后端本地持有
→ 前端只持有业务后端的 Session Cookie
```

### 5.4 方式三：OIDC 客户端（发布）

**不变**：
```
点击应用卡片 → /api/auth/sso-url → home_url/oauth/login
→ 跳转认证中心 /oauth/authorize → 授权码 + PKCE
→ 业务后端换 token → 建会话
```

---

## 六、关键设计决策（面试叙事）

| 决策 | 选择 | 依据 |
|------|------|------|
| **Token 存储** | 服务端（认证中心 / 业务后端） | RFC 9700 §4.1、draft-ietf-oauth-browser-based-apps §6.1 |
| **浏览器会话** | HttpOnly Cookie | 防 XSS 窃取，JavaScript 不可读 |
| **Cookie 域** | 网关 IP（192.168.3.155） | RFC 6265：Cookie 域不含端口，同 IP 所有端口共享 |
| **SameSite** | Lax | 允许顶层导航（点击链接跳转）自动带 Cookie |
| **网关职责** | 有状态会话管理 | 不只是每请求验 JWT，而是维护用户会话 |
| **Session 优先** | Session → JWT 兜底 | 新链路走 Session，旧链路（直连 JWKS）仍可用 JWT |
| **授权码一次性** | UUID + 60s TTL + 用完即毁 | 非 JWT，泄露无害；短时效降低重放风险 |

---

## 七、实施计划

### Phase 1：门户登录零点击 + 网关会话基础设施（0.5 天）

| 任务 | 文件 | 改动量 |
|------|------|--------|
| 门户登录自动跳转 | `LoginPage.tsx` | ~10 行 |
| 网关会话存储 | `sessions.py` | ~30 行 |
| verify 端点 Session 优先 | `auth.py` | ~30 行 |
| sso-url 端点返回干净 URL | `auth.py` | ~15 行 |
| 门户 BFF 设置网关 Cookie | `portal.py` | ~10 行 |
| Traefik addAuthCookiesToResponse | `dynamic.yml` | ~2 行 |

### Phase 2：一次性授权码 + 方式二改造（0.5 天）

| 任务 | 文件 | 改动量 |
|------|------|--------|
| 一次性授权码存储 | `sessions.py` | ~25 行 |
| redeem-code 端点 | `auth.py` | ~15 行 |
| TaskManager 前端兑换 | `main.js` | ~15 行 |
| EventManager 前端兑换 | `main.tsx` | ~15 行 |

### Phase 3：方式一前端清理（0.5 天）

| 任务 | 文件 | 改动量 |
|------|------|--------|
| CloudManager 移除 token 消费 | `main.ts` | ~20 行删除 |
| WorkFlowCenter 移除 token 消费 | `main.js` | ~20 行删除 |
| PermissionCenter 移除 token 消费 | `main.ts` | ~20 行删除 |
| 各系统 401 跳转门户登录 | 各 `main.ts/tsx/js` | ~5 行/系统 |

### Phase 4：登出链路 + 验证 + 文档（0.5 天）

| 任务 | 文件 | 改动量 |
|------|------|--------|
| 登出清除所有会话 | `portal.py` | ~10 行 |
| 端到端验证 | 手动测试 | — |
| 更新文档 | `docs/12-*.html` / `docs/13-*.md` | — |

**总计**：~2 人天

---

## 八、验证清单

| # | 验证项 | 预期结果 |
|---|--------|----------|
| 1 | 访问门户未登录 | 自动跳转 OIDC 登录页（无按钮） |
| 2 | 登录后访问门户 | 直接进入首页（Session 恢复） |
| 3 | 点击云管/工单/权限卡片 | URL 干净（无 token），页面正常加载 |
| 4 | 点击任务/事件卡片 | URL 带 ?code=（非 JWT），页面正常加载 |
| 5 | 点击发布系统卡片 | 跳转 OIDC 授权码流（不变） |
| 6 | 浏览器地址栏 | 全程无 JWT 出现 |
| 7 | 浏览器开发者工具 → Cookie | 只有 _gw_session（HttpOnly） |
| 8 | 浏览器开发者工具 → localStorage | 无 token 存储 |
| 9 | 各系统 API 调用 | 返回 200（网关注入 X-Auth-* 头） |
| 10 | 各系统页面显示用户名 | 正确显示当前用户 |
| 11 | 登出 | 清除所有会话，跳转登录页 |
| 12 | 登出后再访问业务系统 | 401 → 跳转门户登录 |

---

## 九、边界与后续

### 当前不做（超出范围）
- 生产级 Session 存储（Redis）—— Demo 用内存即可
- 统一登出广播（SLO）—— 各系统独立登出
- Token 刷新统一处理 —— Demo 会话 8h 足够
- 密钥轮换（多 kid）—— 单密钥够用

### 后续可做
- Session 存储迁移到 Redis（生产级）
- 统一登出（RP-initiated logout + SLO 广播）
- Token 刷新统一处理（网关层自动续期）
- 密钥轮换（多 kid + JWKS 平滑过渡）
