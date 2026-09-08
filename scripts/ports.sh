#!/usr/bin/env bash
# ============================================================
# ports —— 端口映射与网关路由清单
#   运行态：docker ps 实时解析 + Traefik 路由 API
#   设计态：docs/端口分配.md（make ports --doc）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

if [ "${1:-}" = "--doc" ]; then
  cat docs/端口分配.md
  exit 0
fi

echo "── 宿主端口映射（运行态 · docker ps 实时）──────────────"
docker ps --format '{{.Names}}\t{{.Ports}}' > /tmp/dp-ports.txt
python3 - <<'PY'
import re
rows = []
seen = set()
for line in open("/tmp/dp-ports.txt"):
    if "\t" not in line:
        continue
    name, ports = line.rstrip("\n").split("\t", 1)
    # 支持单端口与范围映射：0.0.0.0:8088->80/tcp、0.0.0.0:8089-8099->8089-8099/tcp
    for m in re.finditer(r"0\.0\.0\.0:(\d+)(?:-(\d+))?->(\d+)(?:-(\d+))?/tcp", ports):
        h1, h2, c1, c2 = m.groups()
        host = f"{h1}-{h2}" if h2 else h1
        cport = f"{c1}-{c2}" if c2 else c1
        key = (int(h1), name, cport)
        if key in seen:
            continue
        seen.add(key)
        rows.append((int(h1), host, name, cport))
for _, host, name, cport in sorted(rows):
    print("  %-10s  %-36s → %s" % (host, name, cport))
PY

echo ""
echo "── 统一网关路由（Traefik API 实时）──────────────────"
if curl -s --max-time 2 http://localhost:8086/api/http/routers -o /tmp/traefik-routers.json 2>/dev/null && [ -s /tmp/traefik-routers.json ]; then
  python3 - <<'PY'
import json
try:
    rs = json.load(open("/tmp/traefik-routers.json"))
except Exception as exc:
    print(f"  （Traefik API 响应异常：{exc}）")
    raise SystemExit(0)
for r in sorted(rs, key=lambda x: (x.get("entryPoints", [""])[0], x.get("rule", ""))):
    ep = ",".join(r.get("entryPoints", []))
    mw = "*" if r.get("middlewares") else " "
    print("  %-12s %-62s → %s %s" % (ep, r.get("rule", "")[:60], r.get("service", ""), mw))
print("  （* = 带 forwardAuth 鉴权中间件）")
PY
else
  echo "  （Traefik API 不可达：8086 未启动？）"
fi

echo ""
echo "设计基准：docs/端口分配.md（make ports --doc 查看）"
