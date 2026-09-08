"""OIDC 演示应用（oidc-demo）—— 模拟一个通过 OIDC 授权码 + PKCE 接入的应用。

演示标准授权码流（client_secret 只在应用后端使用，绝不进前端）：
  ① 前端点"登录" → 生成 PKCE code_verifier + state + nonce → 跳认证中心 /oauth/authorize
  ② 认证中心校验用户 + 客户端 + PKCE → 302 带一次性 code 回 /callback
  ③ 本应用【后端】校验 state，用 code + code_verifier + client_secret 调 /oauth/token
  ④ 后端解码 id_token 校验 nonce，用 Bearer access_token 调 /oauth/userinfo 拿用户信息
  ⑤ 页面显示"我是谁"
"""
import base64
import hashlib
import json
import os
import secrets
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

CLIENT_ID = os.environ.get("CLIENT_ID", "oidc-demo-app")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "oidc-demo-secret-123456")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8005/callback")
AUTHORIZE_URL = os.environ.get("AUTH_AUTHORIZE_URL", "http://localhost:8002/oauth/authorize")
TOKEN_URL = os.environ.get("AUTH_TOKEN_URL", "http://auth-backend:8000/oauth/token")
USERINFO_URL = os.environ.get("AUTH_USERINFO_URL", "http://auth-backend:8000/oauth/userinfo")
PORT = 8005

# 本次授权流进行中的 PKCE 状态（state → code_verifier / nonce）。Demo 存内存，生产用 Redis/DB。
_state_store: dict[str, dict] = {}


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _pkce_challenge(verifier: str) -> str:
    return _b64url(hashlib.sha256(verifier.encode("utf-8")).digest())


def _decode_jwt_payload(token: str) -> dict | None:
    """不解签地展示 id_token payload（教学用途；生产必须验签）。"""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _http_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OidcDemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/callback":
            self._callback()
        else:
            self._home()

    def _home(self):
        # 门户 SSO 跳转场景：home_url?token=<统一JWT>，读取并透传给 authorize，
        # 使「门户跳转 → 授权码流程」一次完成（token 仅为 Demo 兼容，身份以 IdP 会话为准）
        qs = urllib.parse.urlparse(self.path).query
        token = urllib.parse.parse_qs(qs).get("token", [""])[0]

        # 标准 OIDC 客户端行为：每次发起授权流生成 PKCE + state + nonce
        verifier = _b64url(secrets.token_bytes(48))
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)
        _state_store[state] = {"verifier": verifier, "nonce": nonce}

        auth_params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "openid profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
        }
        if token:
            auth_params["token"] = token
        auth_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(auth_params)
        html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<title>OIDC 演示应用 · 授权码 + PKCE</title>
<style>
 body{font-family:-apple-system,'PingFang SC',sans-serif;background:#f0f2f5;margin:0}
 .card{max-width:600px;margin:56px auto;background:#fff;border-radius:14px;box-shadow:0 12px 32px rgba(16,24,40,.12);padding:36px;text-align:center}
 .tag{display:inline-block;background:#f59e0b;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;margin-bottom:16px}
 h1{margin:0 0 8px;color:#101828} p{color:#475467;font-size:14px}
 .btn{display:inline-block;margin-top:20px;background:#1d5fd6;color:#fff;border:none;padding:12px 28px;border-radius:8px;cursor:pointer;font-size:15px;text-decoration:none}
 code{background:#f3f4f6;padding:2px 7px;border-radius:6px;font-size:12px}
</style></head><body><div class="card">
 <div class="tag">OIDC 授权码 + PKCE</div>
 <h1>OIDC 演示应用</h1>
 <p>本应用通过 <b>OIDC 授权码流程（OAuth 2.1 + PKCE）</b>接入统一认证。点击登录会生成
 <code>code_verifier</code> 并跳转认证中心，之后 <code>client_secret</code> 只在<b>本应用后端</b>用来换 token。</p>
 <a class="btn" href="__AUTH_URL__">通过统一认证登录</a>
</div></body></html>"""
        self._send_html(html.replace("__AUTH_URL__", auth_url))

    def _callback(self):
        qs = urllib.parse.urlparse(self.path).query
        params = {k: v[0] for k, v in urllib.parse.parse_qs(qs).items()}
        code = params.get("code", "")
        state = params.get("state", "")
        error = params.get("error", "")

        if error:
            self._send_html("<p>授权失败：%s</p><a href='/'>返回</a>" % error)
            return
        if not code:
            self._send_html("<p>缺少授权码 code</p>")
            return

        steps = [("① 生成 PKCE code_verifier + state + nonce，跳认证中心 /authorize", True),
                 ("② 认证中心 302 带回一次性 code + state", True)]

        # state 校验（防 CSRF）：取出即失效
        flow = _state_store.pop(state, None)
        if flow is None:
            self._send_html("<p>state 校验失败（防 CSRF）</p><a href='/'>返回</a>")
            return
        steps.append(("③ 校验 state（防 CSRF）", True))

        try:
            # ④ 后端换 token：code + code_verifier + client_secret（机密不进浏览器）
            tokens = _http_form(TOKEN_URL, {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": flow["verifier"],
            })
            steps.append(("④ 后端用 code + code_verifier + client_secret 换 token", True))

            # ⑤ 解码 id_token，校验 nonce 是否等于发起时生成的值（防重放）
            id_claims = _decode_jwt_payload(tokens.get("id_token", ""))
            nonce_ok = bool(id_claims and id_claims.get("nonce") == flow["nonce"])
            steps.append(("⑤ 解码 id_token 并校验 nonce（防重放）" + (" ✅ nonce 匹配" if nonce_ok else ""), nonce_ok))

            # ⑥ userinfo
            user = _http_get(USERINFO_URL, {"Authorization": "Bearer " + tokens["access_token"]})
            steps.append(("⑥ 后端用 Bearer access_token 调 /userinfo", True))
        except Exception as exc:  # noqa: BLE001
            steps.append(("④⑤⑥ 换 token / 校验 / userinfo", False))
            self._send_html("<p>授权码交换失败：%s</p><pre>%s</pre>" % (exc, exc))
            return

        access = tokens.get("access_token", "")
        id_token = tokens.get("id_token", "")
        rows = "\n".join(
            "<tr><th>%s</th><td>%s</td></tr>" % (k, user.get(k, "-"))
            for k in ("preferred_username", "name", "email", "department", "source")
        )
        id_rows = ""
        if id_claims:
            id_rows = "\n".join(
                "<tr><th>%s</th><td>%s</td></tr>" % (k, id_claims.get(k, "-"))
                for k in ("iss", "sub", "aud", "exp", "nonce")
            )
        steps_html = "\n".join(
            '<div style="padding:6px 0">%s %s</div>' % ("✅" if ok else "❌", s)
            for s, ok in steps
        )
        html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<title>OIDC 演示应用 · 登录成功</title>
<style>
 body{font-family:-apple-system,'PingFang SC',sans-serif;background:#f0f2f5;margin:0}
 .card{max-width:720px;margin:40px auto;background:#fff;border-radius:14px;box-shadow:0 12px 32px rgba(16,24,40,.12);padding:32px}
 .tag{display:inline-block;background:#10b981;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;margin-bottom:14px}
 h1{margin:0 0 8px;color:#101828}
 table{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}
 th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #eef0f4}
 th{color:#667085;width:150px}
 .step{background:#f8fafd;border:1px solid #e4e9f2;border-radius:10px;padding:10px 14px;margin-top:6px;font-size:13px}
 .tok{font-size:11px;color:#667085;word-break:break-all;margin-top:6px}
</style></head><body><div class="card">
 <div class="tag">✅ OIDC 授权码 + PKCE 登录成功</div>
 <h1>OIDC 演示应用 · 我的信息</h1>
 <table>__ROWS__</table>
 <h3 style="margin-top:20px">id_token（身份断言，含 nonce）</h3>
 <table>__ID_ROWS__</table>
 <h3 style="margin-top:20px">授权码流程（本应用视角）</h3>
 <div>__STEPS__</div>
 <div class="tok">access_token（前 60 字符）：__ACCESS__…</div>
</div></body></html>"""
        self._send_html(html
                        .replace("__ROWS__", rows)
                        .replace("__ID_ROWS__", id_rows)
                        .replace("__STEPS__", steps_html)
                        .replace("__ACCESS__", access[:60]))

    def _send_html(self, body: str):
        body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"oidc-demo listening on :{PORT}")
    HTTPServer(("0.0.0.0", PORT), OidcDemoHandler).serve_forever()
