"""试点接入示例业务系统（pilot-app）—— 模拟"真实业务系统接入统一认证后"的样子。

接入方式：经统一网关 forwardAuth（gateway 模式）
- 页面（/）免鉴权加载，SPA 从 URL 读取统一 JWT 存入本地
- 调业务 API 时带 Authorization 头 → 网关校验 → 注入 X-Auth-* 头 → 业务后端读头
- 业务后端零鉴权代码，只从 X-Auth-* 头取当前用户，并生成"该用户的业务数据"

用 Python 标准库实现（与 mock-app 同风格），但更像一个真实业务系统：
工作台 = 当前用户（来自统一认证） + 该用户的待办工单列表。
"""
import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

PORT = 8004

# 模拟业务数据池（按用户生成，体现"业务系统为当前用户服务"）
_TICKET_TEMPLATES = [
    "云主机 {env} 扩容申请", "数据库 {env} 慢查询优化", "发布单 {env} 上线审批",
    "工单 {n}：安全组规则变更", "工单 {n}：配置项更新", "工单 {n}：日志采集异常",
]
_ENVS = ["生产", "预发", "测试"]


def _mock_workbench(username: str) -> dict:
    """根据当前用户生成模拟业务数据（真实的业务系统会查自己的库）。"""
    random.seed(username)
    n = random.randint(3, 6)
    tickets = [
        {"id": f"TC-{1000 + random.randint(0, 9000)}",
         "title": random.choice(_TICKET_TEMPLATES).format(env=random.choice(_ENVS), n=random.randint(1, 99)),
         "status": random.choice(["待处理", "处理中", "待审批"])}
        for _ in range(n)
    ]
    return {
        "pending_count": sum(1 for t in tickets if t["status"] == "待处理"),
        "processing_count": sum(1 for t in tickets if t["status"] == "处理中"),
        "tickets": tickets,
    }


class PilotAppHandler(BaseHTTPRequestHandler):
    def _auth_headers(self) -> dict:
        return {
            "user_id": self.headers.get("X-Auth-User", ""),
            "username": self.headers.get("X-Auth-Username", ""),
            "display_name": unquote(self.headers.get("X-Auth-Name", "")),
            "department": unquote(self.headers.get("X-Auth-Department", "")),
            "source": self.headers.get("X-Auth-Source", ""),
        }

    def do_GET(self):
        auth = self._auth_headers()
        if self.path.startswith("/api/"):
            self._api(auth)
            return
        self._send_html()

    def _api(self, auth: dict):
        if self.path == "/api/me":
            self._send_json({"code": 200, "user": auth})
            return
        if self.path == "/api/workbench":
            # 网关注入的 X-Auth-* 头就是"当前用户"（业务后端零鉴权）
            username = auth["username"] or "guest"
            self._send_json({"code": 200, "user": auth, "workbench": _mock_workbench(username)})
            return
        self._send_json({"code": 404, "message": "not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
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
<title>工单中心 · 试点接入示例</title>
<style>
  body { font-family: -apple-system,'PingFang SC',sans-serif; background:#f0f2f5; margin:0; }
  .top { background:linear-gradient(90deg,#0b1e4b,#123a8f); color:#fff; padding:14px 24px;
         display:flex; align-items:center; justify-content:space-between; }
  .top b { font-size:16px; } .top .user { font-size:13px; opacity:.9; }
  .wrap { max-width:880px; margin:24px auto; padding:0 16px; }
  .banner { background:linear-gradient(120deg,#1d5fd6,#4f8cff); color:#fff; border-radius:14px;
            padding:20px 24px; margin-bottom:20px; }
  .banner h2 { margin:0 0 6px; } .banner p { margin:0; opacity:.92; font-size:13px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:20px; }
  .stat { background:#fff; border-radius:12px; padding:18px; text-align:center; box-shadow:0 1px 3px rgba(16,24,40,.08); }
  .stat .num { font-size:28px; font-weight:700; color:#1d5fd6; }
  .stat .lbl { color:#667085; font-size:13px; margin-top:4px; }
  .card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(16,24,40,.08); }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th,td { text-align:left; padding:10px 12px; border-bottom:1px solid #eef0f4; }
  th { color:#667085; }
  .tag { display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; }
  .ok { background:#ecfdf5; color:#047857; }
  .status { color:#b45309; }
</style>
</head>
<body>
<div class="top">
  <b>📋 工单中心 · 试点接入业务系统</b>
  <span class="user" id="topUser">正在通过统一网关验证身份…</span>
</div>
<div class="wrap">
  <div class="banner">
    <h2>我的工作台</h2>
    <p>本系统已接入统一认证（SSO）。当前用户身份由统一网关校验后注入，业务系统零鉴权。</p>
  </div>
  <div class="grid">
    <div class="stat"><div class="num" id="pending">-</div><div class="lbl">待处理工单</div></div>
    <div class="stat"><div class="num" id="processing">-</div><div class="lbl">处理中</div></div>
    <div class="stat"><div class="num" id="source">-</div><div class="lbl">认证来源</div></div>
  </div>
  <div class="card">
    <h3 style="margin-top:0">我的工单列表</h3>
    <table id="tickets"><thead><tr><th>单号</th><th>标题</th><th>状态</th></tr></thead><tbody></tbody></table>
    <p id="err" style="color:#ef4444;display:none"></p>
  </div>
</div>
<script>
// SSO：从门户跳转 URL 读取统一 JWT，保存后携 Authorization 头调受保护 API
(function () {
  const p = new URLSearchParams(location.search);
  const t = p.get('token');
  if (t) localStorage.setItem('pilot_token', t);
})();

async function call(path) {
  const t = localStorage.getItem('pilot_token');
  const r = await fetch(path, { headers: t ? { 'Authorization': 'Bearer ' + t } : {} });
  if (r.status === 401) throw new Error('未通过统一网关鉴权（401），请从统一门户登录后进入');
  return r.json();
}

async function init() {
  const err = document.getElementById('err');
  try {
    const me = await call('/api/me');
    const u = me.user || {};
    document.getElementById('topUser').textContent =
      '当前用户：' + (u.display_name || u.username || '-') + '（' + ({local:'本地库',ldap:'LDAP',okta:'Okta'}[u.source]||u.source||'-') + '）';

    const wb = await call('/api/workbench');
    const w = wb.workbench || {};
    document.getElementById('pending').textContent = w.pending_count ?? '-';
    document.getElementById('processing').textContent = w.processing_count ?? '-';
    document.getElementById('source').textContent = {local:'本地库',ldap:'LDAP',okta:'Okta'}[u.source] || u.source || '-';

    const tb = document.getElementById('tickets').tBodies[0];
    (w.tickets || []).forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = '<td>' + t.id + '</td><td>' + t.title + '</td><td class="status">' + t.status + '</td>';
      tb.appendChild(tr);
    });
  } catch (e) {
    err.textContent = e.message;
    err.style.display = 'block';
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

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"pilot-app listening on :{PORT} (经统一网关访问)")
    HTTPServer(("0.0.0.0", PORT), PilotAppHandler).serve_forever()
