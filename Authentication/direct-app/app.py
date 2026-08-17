"""直连模式示例应用（direct-app）。

演示「不经过统一网关的应用如何验证统一 JWT」：
- 本应用直接对外暴露（不经 Traefik forwardAuth）
- 每个请求由自己的 JWKS 验签中间件本地验证统一 JWT
- 验签通过 → 返回用户信息；无 token / 无效 → 401

与"经网关接入"（mock-app）形成对照，两种方式都无需请求 verify 接口。
"""
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from jwks_auth import verify_jwt

app = FastAPI(title="直连模式示例应用（JWKS 自验签）", version="0.1.0")

PORT = int(os.environ.get("PORT", 8003))


def get_current_user(authorization: str = Header(default="")):
    """FastAPI 依赖：本地验签统一 JWT（20-30 行的"验签中间件"）。"""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供凭证（缺少 Authorization: Bearer）")
    token = authorization[7:].strip()
    try:
        return verify_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"统一 JWT 验签失败: {exc}") from exc


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<title>直连模式示例 · JWKS 自验签</title>
<style>
  body{font-family:-apple-system,'PingFang SC',sans-serif;background:#f0f2f5;margin:0}
  .card{max-width:640px;margin:56px auto;background:#fff;border-radius:14px;
        box-shadow:0 12px 32px rgba(16,24,40,.12);padding:36px}
  .tag{display:inline-block;background:#8b5cf6;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;margin-bottom:16px}
  h1{margin:0 0 8px;color:#101828} p{color:#475467;line-height:1.8}
  code{background:#f3f4f6;padding:2px 7px;border-radius:6px;font-size:13px}
</style></head><body><div class="card">
  <div class="tag">直连模式 · 不经统一网关</div>
  <h1>直连模式示例应用</h1>
  <p>本应用<b>不经过统一网关</b>，用认证中心发布的公钥（<code>/.well-known/jwks.json</code>）
  在<b>本地验签统一 JWT</b>。</p>
  <p>请求 <code>/api/me</code> 时带 <code>Authorization: Bearer &lt;统一JWT&gt;</code>
  → 本地验签通过即返回当前用户；无票/假票 → 401。</p>
  <p>用 curl 试：<br/><code>curl /api/me -H "Authorization: Bearer 你的JWT"</code></p>
</div></body></html>"""
    return HTMLResponse(html)


@app.get("/api/me", summary="本地验签统一 JWT 后返回当前用户")
def me(payload: dict = Depends(get_current_user)):
    return {
        "message": "直连模式：本地 JWKS 验签通过（未经过网关）",
        "user": {
            "id": payload.get("sub"),
            "username": payload.get("uid"),
            "name": payload.get("name"),
            "department": payload.get("department", ""),
            "source": payload.get("source", ""),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
