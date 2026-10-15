#!/usr/bin/env python3
"""T1 e2e 冒烟 v2：路由表导入/五格/变更阻断/归档/网关查表（PEP token + alice 授权链）"""
import json, sys, urllib.request, urllib.error

B = "http://localhost:18080"
PEP = {"X-PEP-Token": "pep-shared-secret"}
PASS, FAIL = 0, 0

def req(method, path, body=None, extra=None):
    h = {"X-Auth-Username": "admin", "Content-Type": "application/json"}
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw) if raw else {}
        except Exception: return e.code, {}

def gw(user, app, method, uri):
    return req("GET", "/v1/gateway/check", None, {
        "X-User": user, "X-App": app,
        "X-Forwarded-Method": method, "X-Forwarded-Uri": uri, **PEP})

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name} {detail}")

# 1. 应用清单
s, apps = req("GET", "/api/v1/apps")
apps = apps if isinstance(apps, list) else apps.get("items", [])
cmdb = next((a for a in apps if a["code"] == "cmdb"), None)
check("GET /apps 200 且含 cmdb", s == 200 and cmdb is not None, f"s={s}")
if not cmdb: sys.exit(1)
aid = cmdb["id"]

# 2. 字典导入（显式 1 条 + 推断 2 条入队 + 非法 1 条拦截）
s, rep = req("POST", f"/api/v1/apps/{aid}/routes", {"source": "dict", "entries": [
    {"method": "GET", "path": "/api/v1/disks", "action": "cmdb:disk:list"},
    {"method": "POST", "path": "/api/v1/e2e/reboot"},
    {"method": "GET", "path": "/api/v1/e2e-things"},
    {"method": "POST", "path": "/api/v1/disks", "action": "BAD CODE"},
]})
check("dict 导入 200", s == 200, f"s={s} {rep}")
check("显式条落表 imported>=1", rep.get("imported", 0) >= 1, rep)
check("推断条入队 pending_count>=2", rep.get("pending_count", 0) >= 2, rep)
check("非法码被拦截 blocked>=1", len(rep.get("blocked", [])) >= 1, rep)
v1 = rep.get("version", 0)
check("版本递增到 >=1", v1 >= 1, rep)

# 3. 路由表总览
s, rt = req("GET", f"/api/v1/apps/{aid}/routes")
check("GET /routes 200", s == 200)
items = rt.get("items", [])
pends = rt.get("pending", [])
check("总览含 version/pending/migrations", all(k in rt for k in ("version", "pending", "migrations")), list(rt.keys()))
check("待确认队列 >=2", len(pends) >= 2, len(pends))
target = next((p for p in pends if p["path"] == "/api/v1/e2e/reboot"), None)
check("e2e/reboot 在队列且推断码为 cmdb:e2e:reboot",
      bool(target) and target.get("inferred_code") == "cmdb:e2e:reboot", target)

# 4. 待确认落表
s, cf = req("POST", f"/api/v1/apps/{aid}/pending-routes/{target['id']}/confirm")
check("confirm 落表 200", s == 200, cf)
new_act = cf.get("action", {})
check("落表动作码 = cmdb:e2e:reboot", new_act.get("code") == "cmdb:e2e:reboot", new_act)
rid = new_act.get("id")

# 5. 五格登记：数据级 + 取材声明 + 范围参数（合法）
s, up = req("PATCH", f"/api/v1/apps/{aid}/routes/{rid}", {
    "rw": "write", "need_data": True,
    "material": {"mode": "id_path", "path": "body.instance_id"},
    "scope_param": {"param": "account", "location": "query"},
})
check("五格登记合法 200", s == 200, up)
a2 = up.get("action", {})
check("material/scope 落库", (a2.get("material") or {}).get("path") == "body.instance_id"
      and (a2.get("scope_param") or {}).get("param") == "account", a2)

# 6. 非法取材声明 → 400
s, bad = req("PATCH", f"/api/v1/apps/{aid}/routes/{rid}", {
    "need_data": True, "material": {"mode": "fetch_source", "url": "GET /x"},
})
check("fetch_source 缺 pick/bind 被拒 400", s == 400, (s, bad))

# 7. 变更阻断：直改 code → 409
s, blk = req("PATCH", f"/api/v1/apps/{aid}/routes/{rid}", {"code": "cmdb:hacked:edit"})
check("直改 code 变更阻断 409", s == 409 and blk.get("error") == "code_change_blocked", (s, blk))

# 8. 迁移：无引用直接迁 200；真被引用（id=8 cmdb:db:backup）未确认 409
s, mg = req("POST", f"/api/v1/apps/{aid}/routes/{rid}/migrate-code", {"new_code": "cmdb:e2e:reboot2"})
check("无引用迁移 200", s == 200, mg)
check("迁移留记录 old→new", (mg.get("migration") or {}).get("old_code") == "cmdb:e2e:reboot", mg)
ref_act = next((a for a in items if a.get("code") == "cmdb:db:backup"), None)
check("找到真被引用动作 cmdb:db:backup", bool(ref_act), "seed 里应有")
s, m2 = req("POST", f"/api/v1/apps/{aid}/routes/{ref_act['id']}/migrate-code",
            {"new_code": "cmdb:db:backupx"})
aff = m2.get("affected") or {}
check("有引用迁移未确认 409+受影响清单", s == 409
      and (len(aff.get("policies") or []) + len(aff.get("capabilities") or [])) > 0, (s, m2))

# 9. 归档轮次（发生在授权前——授权后再归档会被引用检查挡住）：有引用拒 409；自身归档→解析不出→恢复
s, ar = req("POST", f"/api/v1/apps/{aid}/routes/{ref_act['id']}/archive")
check("归档被引用动作 409", s == 409 and ar.get("error") == "archive_blocked", (s, ar))
s, ar2 = req("POST", f"/api/v1/apps/{aid}/routes/{rid}/archive")
check("归档无引用动作 200", s == 200, (s, ar2))
s, g = gw("alice", "cmdb", "POST", "/api/v1/e2e/reboot")
check("归档后网关 403 no action resolved", s == 403 and "no action resolved" in str(g.get("error", "")), (s, g))
s, rs = req("POST", f"/api/v1/apps/{aid}/routes/{rid}/restore")
check("恢复 200", s == 200, rs)
s, g = gw("alice", "cmdb", "POST", "/api/v1/e2e/reboot")
check("恢复后可解析但未授权 403 denied", s == 403 and g.get("code") == "NO_PERMISSION", (s, g))
# 授权链：申请（201）→ SoD 审批（alice 批，admin 是申请人不能自批）→ 网关放行 200
s, pol = req("POST", "/api/v1/policies", {
    "name": "e2e:alice:e2e-reboot", "effect": 1, "subject_type": 1, "subject_id": 2,
    "app_id": aid, "action_ids": [rid], "reason": "T1 e2e 授权链",
})
check("提交授权申请 201 生成申请单", s in (200, 201) and pol.get("id"), (s, pol))
s_a, a_msg = req("POST", f"/api/v1/requests/{pol.get('id')}/approve", {},
                 {"X-Auth-Username": "iam_alice"})
check("审批通过（2xx 或 400=已批）", s_a in (200, 201, 400), (s_a, a_msg))
s, g = gw("alice", "cmdb", "POST", "/api/v1/e2e/reboot")
check("授权后网关放行 200", s == 200, (s, g))

# 10. 网关查表：cloudportal+alice 已登记 200 / 未登记 403 deny-by-default
s, g1 = gw("alice", "cloudportal", "GET", "/api/v1/resources")
check("已登记路由网关放行 200（alice/cloudportal）", s == 200, (s, g1))
s, g2 = gw("alice", "cloudportal", "GET", "/api/v1/nope-not-registered")
check("未登记路由 403 deny-by-default", s == 403 and "no action resolved" in str(g2.get("error", "")), (s, g2))

# 11. 版本累计
s, rt2 = req("GET", f"/api/v1/apps/{aid}/routes")
check(f"版本多次递增 (>= {v1 + 4})", rt2.get("version", 0) >= v1 + 4, rt2.get("version"))

print(f"\n== T1 e2e v2: PASS {PASS} / FAIL {FAIL} ==")
sys.exit(1 if FAIL else 0)
