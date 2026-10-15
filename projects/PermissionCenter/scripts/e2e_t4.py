#!/usr/bin/env python3
"""T4 接入体检 e2e：六种坏配置各被阻断并列明原因 / 正常报告全绿 / 未确认停未完成 /
配置期拦裸豁免 / 网关凭证豁免运行时 / 403 告警打点。
注：配置自洽类坏配置（④）经 API 构造会被配置门禁拦（validateMaterialDecl/预填）——
这正是"配置页不让存"设计；体检兜【存量】，故④用 SQL 直插模拟存量坏数据。"""
import json, subprocess, sys, urllib.request, urllib.error

IAM = "http://localhost:18080"
PASS = FAIL = 0

def http(method, url, body=None, headers=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except Exception:
            return e.code, {"error": raw.decode(errors="replace")[:200]}
    except Exception as e:
        return 0, {"error": str(e)}

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ FAIL {name} {detail}")

def sql(q):
    r = subprocess.run(
        ["docker", "exec", "devops-postgres", "psql", "-U", "devops", "-d", "devops_iam", "-tAc", q],
        capture_output=True, text=True)
    return r.stdout.strip()

# ---- 登录 ----
st, d = http("POST", f"{IAM}/api/v1/auth/login", {"username": "admin", "password": "admin123"})
assert st == 200 and d.get("access_token"), f"login failed: {d}"
TOK = d["access_token"]

# ---- 起点清残留（历史崩溃运行可能留下坏 pending）----
sql("DELETE FROM route_pendings WHERE path LIKE '/api/v1/e2e-bad%'")

print("===== T4-1 未确认路由停『未完成』态（存量 e2e-things）=====")
st, rep = http("GET", f"{IAM}/api/v1/apps/1/onboard-report", token=TOK)
check("报告 API 200", st == 200, str(rep))
check("未确认 → incomplete", rep.get("status") == "incomplete", rep.get("status"))
check("warn=PENDING_UNCONFIRMED 且列明原因",
      any(w["code"] == "PENDING_UNCONFIRMED" and w.get("reason") for w in rep.get("warnings", [])))

print("===== T4-2 构造六种坏配置 -> 各被阻断并列明原因 =====")
# (1) 缺动作（POST 带 id 推断不出）-> dict 导入进待确认队列（inferred_code 空）
st, d = http("POST", f"{IAM}/api/v1/apps/1/routes",
             {"source": "dict", "entries": [{"method": "POST", "path": "/api/v1/e2e-bad/things/{id}"}]}, token=TOK)
check("(1)坏配置导入（推断不出->入队）", st == 200, str(d))
st, ov = http("GET", f"{IAM}/api/v1/apps/1/routes", token=TOK)
PEND_BAD = [p["id"] for p in ov.get("pending", [])
            if p.get("path") == "/api/v1/e2e-bad/things/{id}" and p.get("status") == "pending"]
check("(1)坏配置入队", bool(PEND_BAD), str(ov.get("pending")))

# (2) 格式错 + (3) 同路由挂多码 + (5) 资源段不符：SQL 直插存量（导入期会拦，体检兜存量）
sql("INSERT INTO actions(created_at,updated_at,app_id,code,name,resource,operation,method,path,rw,status) "
    "SELECT now(),now(),1,'cmdb:Host:Read','bad','host','read','GET','/api/v1/hosts-bad/{id}','read','active' "
    "WHERE NOT EXISTS (SELECT 1 FROM actions WHERE code='cmdb:Host:Read')")
sql("INSERT INTO actions(created_at,updated_at,app_id,code,name,resource,operation,method,path,rw,status) "
    "SELECT now(),now(),1,'cmdb:host:dupe1','dup','host','read','GET','/api/v1/dupe-route/{id}','read','active' "
    "WHERE NOT EXISTS (SELECT 1 FROM actions WHERE code='cmdb:host:dupe1')")
sql("INSERT INTO actions(created_at,updated_at,app_id,code,name,resource,operation,method,path,rw,status) "
    "SELECT now(),now(),1,'cmdb:host:dupe2','dup','host','get','GET','/api/v1/dupe-route/{id}','read','active' "
    "WHERE NOT EXISTS (SELECT 1 FROM actions WHERE code='cmdb:host:dupe2')")
sql("INSERT INTO actions(created_at,updated_at,app_id,code,name,resource,operation,method,path,rw,status) "
    "SELECT now(),now(),1,'cmdb:disk:edit','bad','disk','update','PATCH','/api/v1/volumes-bad/{id}','write','active' "
    "WHERE NOT EXISTS (SELECT 1 FROM actions WHERE code='cmdb:disk:edit' AND path='/api/v1/volumes-bad/{id}')")
# (4) 配置自洽四条：SQL 构造存量坏配置（API 配置期会拦——门禁生效证明见 T4-3/T4-3b）
sql("UPDATE actions SET need_data=true, material=NULL WHERE code='cmdb:host:update'")
sql("UPDATE actions SET need_data=true, material='{\"mode\":\"envelope\"}'::jsonb WHERE code='cmdb:disk:create'")
sql("UPDATE actions SET need_data=true, "
    "material='{\"mode\":\"fetch_source\",\"url\":\"GET /api/v1/disks/{disk_id}\",\"pick\":\"nonexistent_field\",\"bind\":{}}'::jsonb "
    "WHERE code='cmdb:disk:update'")
sql("UPDATE apps SET exempt_paths='{\"/api/v1/health-bad\":\"\"}'::jsonb WHERE id=1")

st, rep = http("GET", f"{IAM}/api/v1/apps/1/onboard-report", token=TOK)
codes = {b["code"] for b in rep.get("blocked", [])}
expect = {"NO_ACTION", "BAD_FORMAT", "DUP_ROUTE", "MATERIAL_MISSING",
          "CREATE_NO_SCOPE_PATH", "PLACEHOLDER_UNBOUND", "PICK_NOT_IN_SCHEMA",
          "BARE_EXEMPT", "RESOURCE_MISMATCH"}
missing = expect - codes
check("六种坏配置全部被阻断（9 个阻断码）", not missing, f"缺 {missing}; 实得 {sorted(codes)}")
check("每条阻断列明原因", all(b.get("reason") for b in rep.get("blocked", [])), str(rep.get("blocked")))

print("===== T4-3 配置期拦裸豁免（PUT exempt-paths 400）=====")
st, d = http("PUT", f"{IAM}/api/v1/apps/1/exempt-paths", {"paths": {"/api/v1/health": ""}}, token=TOK)
check("空凭证被拒 400", st == 400 and "裸豁免" in d.get("error", ""), str(d))
st, d = http("PUT", f"{IAM}/api/v1/apps/1/exempt-paths", {"paths": {"/api/v1/health": "no-such-cli"}}, token=TOK)
check("不存在凭证被拒 400", st == 400 and "裸豁免" in d.get("error", ""), str(d))

print("===== T4-3b 配置门禁（validateMaterialDecl 拦坏取材声明）=====")
st, d = http("GET", f"{IAM}/api/v1/apps/1/routes", token=TOK)
RID_READ = next(it["id"] for it in d["items"] if it["code"] == "cmdb:host:read")
st, d = http("PATCH", f"{IAM}/api/v1/apps/1/routes/{RID_READ}",
             {"need_data": True, "material": {"mode": "fetch_source", "url": "GET /x/{id}",
                                               "pick": "account", "bind": {}}}, token=TOK)
check("空 bind 被配置期拦 400", st == 400, f"{st} {d}")

print("===== T4-4 网关凭证豁免运行时（绑定 cloud-mgmt）=====")
st, d = http("PUT", f"{IAM}/api/v1/apps/1/exempt-paths", {"paths": {"/api/v1/health": "cloud-mgmt"}}, token=TOK)
check("合法豁免可配置 200", st == 200, str(d))
GW_H = {"X-PEP-Token": "pep-shared-secret", "X-App": "cmdb",
        "X-Forwarded-Method": "GET", "X-Forwarded-Uri": "/api/v1/health"}
st, d = http("GET", f"{IAM}/v1/gateway/check",
             headers={**GW_H, "X-Client-ID": "cloud-mgmt", "X-Client-Secret": "cloud-mgmt-secret"})
check("凭证匹配 -> 200 exempt 放行", st == 200 and d.get("exempt") is True, f"{st} {d}")
st, d = http("GET", f"{IAM}/v1/gateway/check", headers={**GW_H, "X-User": "alice"})
check("无凭证 -> 照常判（403 未命中）", st == 403, f"{st} {d}")
st, d = http("GET", f"{IAM}/v1/gateway/check",
             headers={**GW_H, "X-User": "alice", "X-Client-ID": "cloud-mgmt", "X-Client-Secret": "wrong"})
check("错凭证 -> 不豁免 403", st == 403, f"{st} {d}")

print("===== T4-5 导入回执带体检报告（触发点自动跑）=====")
st, d = http("POST", f"{IAM}/api/v1/apps/1/routes",
             {"source": "dict", "entries": [{"method": "GET", "path": "/api/v1/healthz",
                                              "action": "cmdb:system:ping"}]}, token=TOK)
check("导入回执含 onboard 报告", st == 200 and isinstance(d.get("onboard"), dict), str(d)[:200])
check("回执报告 status 反映当前阻断", d.get("onboard", {}).get("status") == "blocked",
      str(d.get("onboard", {}).get("status")))

print("===== T4-6 403 告警打点（失配 [ALERT][gw403]）=====")
logs = subprocess.run(["docker", "logs", "permission-center-iam-server-1", "--since", "10m"],
                      capture_output=True, text=True)
check("失配 403 告警日志出现", "[ALERT][gw403]" in logs.stdout + logs.stderr)

# ===== 清理（恢复 demo 现场；material 原值=已知 seed 值）=====
print("===== 清理 =====")
for pid in PEND_BAD:
    http("POST", f"{IAM}/api/v1/apps/1/pending-routes/{pid}/discard", {}, token=TOK)
sql("DELETE FROM actions WHERE code IN ('cmdb:Host:Read','cmdb:host:dupe1','cmdb:host:dupe2')")
sql("DELETE FROM actions WHERE code='cmdb:disk:edit' AND path='/api/v1/volumes-bad/{id}'")
sql("DELETE FROM actions WHERE code='cmdb:system:ping' AND path='/api/v1/healthz'")
sql("UPDATE actions SET need_data=true, material='{\"mode\":\"id_path\",\"path\":\"path.id\"}'::jsonb WHERE code='cmdb:host:update'")
sql("UPDATE actions SET need_data=true, material='{\"mode\":\"envelope\",\"field_path\":\".meta.type\"}'::jsonb WHERE code='cmdb:disk:create'")
sql("UPDATE actions SET need_data=true, material='{\"mode\":\"id_path\",\"path\":\"body.disk_id\"}'::jsonb WHERE code='cmdb:disk:update'")
sql("UPDATE apps SET exempt_paths='{}'::jsonb WHERE id=1")

st, rep = http("GET", f"{IAM}/api/v1/apps/1/onboard-report", token=TOK)
check("清理后 blocked=0", not rep.get("blocked"), str(rep.get("blocked")))
check("清理后仍 incomplete（e2e-things 存量待确认，符合预期）",
      rep.get("status") == "incomplete", rep.get("status"))
st, d = http("GET", f"{IAM}/api/v1/apps/1/routes", token=TOK)
m = {it["code"]: it.get("material") for it in d["items"]}
check("host:update material 恢复 id_path", m.get("cmdb:host:update", {}).get("mode") == "id_path", str(m.get("cmdb:host:update")))
check("disk:create material 恢复 envelope/.meta.type",
      m.get("cmdb:disk:create", {}).get("field_path") == ".meta.type", str(m.get("cmdb:disk:create")))
check("disk:update material 恢复 id_path", m.get("cmdb:disk:update", {}).get("mode") == "id_path", str(m.get("cmdb:disk:update")))

print(f"\n== T4 e2e: PASS {PASS} / FAIL {FAIL} ==")
sys.exit(1 if FAIL else 0)
