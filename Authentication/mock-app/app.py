"""受统一网关保护的演示业务应用（mock-app）。

真实场景：业务系统挂在统一网关（Traefik forwardAuth）后面，
网关校验 JWT 后把用户身份通过 X-Auth-* 请求头注入，
业务后端无需解析 JWT，直接读请求头即可。

本应用用 Python 标准库实现，仅用于演示「统一鉴权」效果。
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

PORT = 8081


class MockAppHandler(BaseHTTPRequestHandler):
    def _auth_headers(self) -> dict:
        return {
            "user_id": self.headers.get("X-Auth-User", ""),
            "username": self.headers.get("X-Auth-Username", ""),
            # X-Auth-Name 为 URL 编码的中文显示名，需解码
            "display_name": unquote(self.headers.get("X-Auth-Name", "")),
            "source": self.headers.get("X-Auth-Source", ""),
        }

    def do_GET(self):
        auth = self._auth_headers()
        if self.path.startswith("/api/"):
            self._send_json({
                "message": "业务 API 数据（经统一网关鉴权后放行）",
                "code": 200,
                "current_user": auth,
            })
            return
        self._send_html()

    def _send_json(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MockApp · 受网关保护的业务系统</title>
<style>
  body { font-family: -apple-system, 'PingFang SC', sans-serif; background:#f0f2f5; margin:0; }
  .card { max-width:720px; margin:64px auto; background:#fff; border-radius:14px;
          box-shadow:0 12px 32px rgba(16,24,40,.12); padding:40px; }
  h1 { margin:0 0 8px; color:#101828; }
  .tag { display:inline-block; background:#1d5fd6; color:#fff; padding:4px 12px;
         border-radius:20px; font-size:13px; margin-bottom:20px; }
  table { width:100%; border-collapse:collapse; }
  td,th { text-align:left; padding:10px 12px; border-bottom:1px solid #eef0f4; font-size:14px; }
  th { color:#667085; width:160px; }
  .ok { color:#10b981; font-weight:600; }
</style>
</head>
<body>
<div class="card">
  <div class="tag" id="statusTag">… 正在通过统一网关验证身份</div>
  <h1>MockApp · 演示业务系统</h1>
  <p style="color:#667085">本系统由统一网关 forwardAuth 保护。前端从 SSO 跳转获取统一 JWT，携 Authorization 头调用业务 API，网关校验后放行并注入身份。</p>
  <table>
    <tr><th>当前用户</th><td id="user">…</td></tr>
    <tr><th>用户 ID</th><td id="uid">…</td></tr>
    <tr><th>登录名</th><td id="uname">…</td></tr>
    <tr><th>认证来源</th><td id="src">…</td></tr>
    <tr><th>网关鉴权</th><td class="ok">X-Auth-* 头注入</td></tr>
  </table>
  <pre id="out" style="margin-top:16px;background:#f6f8fb;padding:12px;border-radius:8px;display:none"></pre>
</div>
<script>
// SSO：从 URL 读取统一 JWT，保存后携 Authorization 头调用受保护 API
(function () {
  const params = new URLSearchParams(location.search);
  const token = params.get('token');
  if (token) localStorage.setItem('mock_app_token', token);
})();

const SRC_MAP = { local: '本地用户库', ldap: 'LDAP', okta: 'Okta' };

async function init() {
  const token = localStorage.getItem('mock_app_token');
  const out = document.getElementById('out');
  out.style.display = 'block';
  try {
    const r = await fetch('/api/data', {
      headers: token ? { 'Authorization': 'Bearer ' + token } : {}
    });
    if (r.status === 401) {
      document.getElementById('statusTag').textContent = '✗ 未通过统一网关鉴权（401）';
      out.textContent = '未通过统一网关鉴权（401）。请从统一门户登录后访问本应用。';
      return;
    }
    const j = await r.json();
    const u = j.current_user || {};
    document.getElementById('statusTag').textContent = '✓ 已通过统一网关 forwardAuth 鉴权';
    document.getElementById('user').textContent = u.display_name || u.username || '-';
    document.getElementById('uid').textContent = u.user_id || '-';
    document.getElementById('uname').textContent = u.username || '-';
    document.getElementById('src').textContent = SRC_MAP[u.source] || u.source || '-';
    out.textContent = JSON.stringify(j, null, 2);
  } catch (e) {
    out.textContent = '请求失败：' + e.message;
  }
}
init();
</script>
</body>
</html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # 静默访问日志
        pass


if __name__ == "__main__":
    print(f"mock-app listening on :{PORT} (仅经 Traefik 网关访问)")
    HTTPServer(("0.0.0.0", PORT), MockAppHandler).serve_forever()
