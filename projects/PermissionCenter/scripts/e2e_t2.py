#!/usr/bin/env python3
"""T2 e2e：点查取材三路（网关 path-id / 带体 body-id / 信封创建）+ fail-closed 三态 + 白名单"""
import json, sys, urllib.request, urllib.error

B = "http://localhost:18080"
HDR = {"X-Auth-Username": "admin", "Content-Type": "application/json"}
PEP = {"X-PEP-Token": "pep-shared-secret"}
PASS, FAIL = 0, 0

def req(method, path, body=None, extra=None):
    h = dict(HDR); h.update(extra or {})
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

def mat(body):
    return req("POST", "/v1/authz/check-material", body, PEP)

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name} {detail}")

aid = 1  # cmdb

# 动态解析动作 id（seed-reset 后 id 会重排，禁硬编码）
_s, _acts = req("GET", "/api/v1/apps/1/actions")
_acts = _acts.get("items") if isinstance(_acts, dict) else _acts
AID = {a["code"]: a["id"] for a in (_acts or [])}
HOST_UPDATE = AID["cmdb:host:update"]
DISK_UPDATE = AID["cmdb:disk:update"]
DISK_CREATE = AID["cmdb:disk:create"]

# ---- 0. 应用回查配置（§3.1）----
s, _ = req("PUT", f"/api/v1/apps/{aid}/perm-query",
           {"url": "http://mock-cmdb:8090/__perm/query", "token": "cmdb-perm-token"})
check("perm-query 配置 200", s == 200, s)
s, _ = req("PUT", f"/api/v1/apps/{aid}/perm-query", {"url": "ftp://bad"})
check("非法回查地址 400", s == 400, s)
req("PUT", f"/api/v1/apps/{aid}/perm-query",
    {"url": "http://mock-cmdb:8090/__perm/query", "token": "cmdb-perm-token"})  # 还原

# ---- 1. 五格登记三路取材声明 ----
s, r4 = req("PATCH", f"/api/v1/apps/{aid}/routes/{HOST_UPDATE}",
            {"need_data": True, "material": {"mode": "id_path", "path": "path.id"}, "rw": "write"})
check("host:update 取材声明 200", s == 200, (s, r4))
s, r38 = req("PATCH", f"/api/v1/apps/{aid}/routes/{DISK_UPDATE}",
             {"need_data": True, "material": {"mode": "id_path", "path": "body.disk_id"}, "rw": "write"})
check("action38 body.* 声明 200", s == 200, (s, r38))
s, r29 = req("PATCH", f"/api/v1/apps/{aid}/routes/{DISK_CREATE}",
             {"need_data": True, "material": {"mode": "envelope", "field_path": ".meta.type"}, "rw": "write"})
check("action29 信封声明 200", s == 200, (s, r29))

# ---- 2. 授权链 ×3（申请 201 → SoD 审批 alice）----
def grant(name, actions, scope):
    s, p = req("POST", "/api/v1/policies", {
        "name": name, "effect": 1, "subject_type": 1, "subject_id": 2,
        "app_id": aid, "action_ids": actions, "resource_scope": scope, "reason": "T2 e2e"})
    if s not in (200, 201) or not p.get("id"):
        return False, (s, p)
    sa, am = req("POST", f"/api/v1/requests/{p['id']}/approve", {}, {"X-Auth-Username": "iam_alice"})
    return sa in (200, 201, 400), (sa, am)

ok, d = grant("t2:host:ip11", [HOST_UPDATE], {"model": "host", "condition": {"op": "eq", "field": "ip", "value": "10.0.1.11"}})
check("host 条件策略生效", ok, d)
ok, d = grant("t2:disk:ssd", [DISK_UPDATE], {"model": "disk", "condition": {"op": "eq", "field": "type", "value": "ssd"}})
check("disk body-id 条件策略生效", ok, d)
ok, d = grant("t2:disk:create-ssd", [DISK_CREATE], {"condition": {"op": "eq", "field": "type", "value": "ssd"}})
check("disk create 条件策略生效", ok, d)

# ---- 3. 网关链路点查（path.*，§3.5 零配合）----
# host-6 = db-01（ip=10.0.1.11，与 grant 条件同值；reset 后 mock 实例重排——id 以运行时解析为准）
s, g = gw("alice", "cmdb", "PATCH", "/api/v1/hosts/host-6")
check("点查+谓词放行 200（ip=10.0.1.11）", s == 200, (s, g))
s, g = gw("alice", "cmdb", "PATCH", "/api/v1/hosts/host-5")
check("谓词不匹配 403 NO_PERMISSION（ip=.12）", s == 403 and g.get("code") == "NO_PERMISSION", (s, g))
s, g = gw("alice", "cmdb", "PATCH", "/api/v1/hosts/host-999")
check("权威行不存在 403 DATA_MISSING", s == 403 and g.get("code") == "DATA_MISSING", (s, g))
s, g = gw("admin", "cmdb", "PATCH", "/api/v1/hosts/host-1")
check("动作级短路 403（admin 无策略，取材不触发）", s == 403 and g.get("code") == "NO_PERMISSION", (s, g))

# ---- 4. 带体调用（body-id / 信封 / fail-closed）----
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:update",
            "material": {"disk_id": "disk-8"}, "trace_id": "t2-1"})
check("带体 body-id 点查放行 200（ssd）", s == 200, (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:update",
            "material": {"disk_id": "disk-404"}, "trace_id": "t2-2"})
check("带体 body-id 行不存在 403 DATA_MISSING", s == 403 and r.get("code") == "DATA_MISSING", (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:update",
            "material": {}, "trace_id": "t2-3"})
check("id 取值缺失 403 MATERIAL_MISSING", s == 403 and r.get("code") == "MATERIAL_MISSING", (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:create",
            "material": {"meta": {"type": "ssd"}}, "trace_id": "t2-4"})
check("信封创建放行 200（.meta.type=ssd）", s == 200, (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:create",
            "material": {"meta": {"type": "hdd"}}, "trace_id": "t2-5"})
check("信封谓词不匹配 403 NO_PERMISSION（hdd）", s == 403 and r.get("code") == "NO_PERMISSION", (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:disk:create",
            "material": {"spec": {}}, "trace_id": "t2-6"})
check("信封字段缺失 403 MATERIAL_MISSING", s == 403 and r.get("code") == "MATERIAL_MISSING", (s, r))
s, r = mat({"user": "alice", "app": "cmdb", "action": "cmdb:host:update",
            "material": {}, "trace_id": "t2-7"})
check("path.* 声明缺 path → 400（合同：走网关链路）", s == 400, (s, r))
s, r = mat({"user": "bob", "app": "cmdb", "action": "cmdb:disk:create",
            "material": {"meta": {"type": "ssd"}}, "trace_id": "t2-8"})
check("动作级短路 403（bob 无策略）", s == 403 and r.get("code") == "NO_PERMISSION", (s, r))

# ---- 5. 未配置回查地址 = fail-closed，恢复后复通 ----
req("PUT", f"/api/v1/apps/{aid}/perm-query", {"url": "", "token": ""})
s, g = gw("alice", "cmdb", "PATCH", "/api/v1/hosts/host-6")
check("未配置回查 403 DATA_SOURCE_UNCONFIGURED", s == 403 and g.get("code") == "DATA_SOURCE_UNCONFIGURED", (s, g))
req("PUT", f"/api/v1/apps/{aid}/perm-query",
    {"url": "http://mock-cmdb:8090/__perm/query", "token": "cmdb-perm-token"})
s, g = gw("alice", "cmdb", "PATCH", "/api/v1/hosts/host-6")
check("恢复配置后复通 200", s == 200, (s, g))

print(f"\n== T2 e2e: PASS {PASS} / FAIL {FAIL} ==")
sys.exit(1 if FAIL else 0)
