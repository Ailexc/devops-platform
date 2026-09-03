#!/usr/bin/env python3
"""获取统一认证中心 demo access_token（OIDC 授权码 + PKCE 流程）。

用途：验证统一网关 forwardAuth / 直连 JWKS 验签链路时，签发统一 JWT。
用法：python3 scripts/get_demo_token.py [username] [password]
默认：cloud_admin / demo1234
"""
import sys
import re
import json
import base64
import hashlib
import urllib.request
import urllib.parse
import http.cookiejar

BASE = "http://localhost:8002"
CLIENT_ID = "oidc-demo-app"
CLIENT_SECRET = "oidc-demo-secret-123456"
REDIRECT_URI = "http://localhost:8005/callback"

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "cloud_admin"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "demo1234"


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def post(url, data=None, headers=None, opener=None):
    body = urllib.parse.urlencode(data).encode() if data else b""
    req = urllib.request.Request(url, data=body, headers=headers or {})
    return opener.open(req)


def main():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    # 1) IdP 登录（建立会话；成功为 302 跳转，urllib 会自动跟随）
    post(f"{BASE}/oauth/login", {"username": USERNAME, "password": PASSWORD}, opener=opener)

    # 2) PKCE
    verifier = b64url(base64.urlsafe_b64encode(hashlib.sha256(b"demo-pkce-verifier").digest()))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())

    # 3) authorize（禁用自动重定向，从 Location 提取一次性 code）
    q = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile",
        "state": "demo-state",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })


    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None


    no_redir = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), NoRedirect()
    )
    try:
        auth_resp = no_redir.open(f"{BASE}/oauth/authorize?{q}")
    except urllib.error.HTTPError as e:
        auth_resp = e
    loc = auth_resp.headers.get("Location", "")
    m = re.search(r"[?&]code=([^&]+)", loc)
    if not m:
        print("no code in redirect:", loc[:200])
        sys.exit(1)
    code = urllib.parse.unquote(m.group(1))

    # 4) token
    tok = post(f"{BASE}/oauth/token", {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": verifier,
    }, opener=opener)
    data = json.loads(tok.read().decode())
    token = data.get("access_token")
    if not token:
        print("token error:", json.dumps(data, ensure_ascii=False))
        sys.exit(1)

    print(token)


if __name__ == "__main__":
    main()
