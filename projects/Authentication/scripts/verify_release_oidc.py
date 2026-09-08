#!/usr/bin/env python3
"""验证发布系统 OIDC 标准客户端接入（方式三）。

模拟浏览器完成 OIDC 授权码流程：
  发布系统 /oauth/login → 认证中心 authorize → 回调换令牌 → 本地 JWT
"""
import json
import re
import urllib.request
import urllib.parse
import http.cookiejar

AUTH_BASE = "http://localhost:8002"          # 认证中心（宿主机入口）
RELEASE_BASE = "http://api.release-system.orb.local"  # 发布系统后端


def get(url, opener, follow=False):
    req = urllib.request.Request(url)
    try:
        r = opener.open(req)
        return r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode()


def main():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    # 1) 认证中心登录（拿 IDP cookie）
    op.open(urllib.request.Request(
        f"{AUTH_BASE}/oauth/login",
        data=urllib.parse.urlencode({"username": "zhangsan", "password": "demo1234"}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ))

    # 2) 发布系统 OIDC 登录 → 302 到认证中心 authorize
    code, h, _ = get(f"{RELEASE_BASE}/api/v1/oauth/login/", op)
    authorize_url = h.get("Location")
    print("1) /oauth/login ->", code, "-> authorize:", authorize_url[:60], "...")

    # 3) 把 authorize 的 host 换成宿主机可达入口，跟随（带 IDP cookie）→ 302 到 redirect_uri
    fixed = authorize_url.replace("http://auth-backend:8000", AUTH_BASE)
    code2, h2, _ = get(fixed, op)
    cb_url = h2.get("Location")
    print("2) authorize ->", code2, "-> callback:", cb_url)
    if not cb_url:
        print("   !! 未获得 code，响应:", h2)
        return
    m = re.search(r"code=([^&]+)", cb_url)
    st = re.search(r"state=([^&]+)", cb_url)
    if not m:
        print("   !! 无 code")
        return
    code_val = urllib.parse.unquote(m.group(1))
    state_val = urllib.parse.unquote(st.group(1)) if st else ""

    # 4) 发布系统回调（用注册 redirect_uri 换令牌）
    cb = f"{RELEASE_BASE}/api/v1/oauth/callback/?code={code_val}&state={state_val}"
    code3, h3, body = get(cb, op)
    print("3) callback ->", code3)
    try:
        data = json.loads(body)
        print("   响应:", json.dumps(data, ensure_ascii=False)[:300])
        if data.get("code") == 200:
            d = data["data"]
            print("   ✅ OIDC 接入成功：本地用户 =", d["user"].get("username"),
                  "| 本地 JWT len =", len(d["token"]))
    except Exception as e:
        print("   !! 解析失败:", e, body[:200])


if __name__ == "__main__":
    main()
