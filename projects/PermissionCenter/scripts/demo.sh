#!/usr/bin/env bash
# 一键演示脚本：正常链路 → 无权限 → CMDB 宕机降级 → 策略发布生效 → 本地 agent 决策
# 前置：make up && make seed && make run && make run-cmdb && make run-id
set -eu

# 访问地址可用环境变量覆盖——服务器（无 OrbStack 域名）用宿主机端口映射：
#   IAM_DEMO=http://localhost:18080 GW_DEMO=http://localhost:19090 bash scripts/demo.sh
IAM=${IAM_DEMO:-https://api.permission-center.orb.local}
GW=${GW_DEMO:-https://cmdb.permission-center.orb.local}
AGENT=${AGENT_DEMO:-http://localhost:19090}
PEP="X-PEP-Token: pep-shared-secret"
CT="Content-Type: application/json"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

say() { printf "\n\033[1;36m===== %s =====\033[0m\n" "$*"; }

say "1. 健康检查"
curl -s "$IAM/healthz"; echo

say "2. 动作级鉴权：alice 读主机（应 allow）"
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read"}'; echo

say "3. 无权限拦截：bob 创建主机（应 deny）"
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:create"}'; echo

say "4. 数据级鉴权：bob 只读 web-01（应 allow，组授权的主机实例）"
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-4","operation":"read"}'; echo

say "5. 数据级鉴权：bob 读 db-01（应 deny，不在组授权实例范围）"
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-6","operation":"read"}'; echo

say "6. filter 列表：bob 可见实例（应 2 个）"
curl -s -X POST "$IAM/v1/authz/filter" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:read","model":"host"}'; echo

say "7. 程序身份（M2M）：云管只读（应 allow）、写（应 deny）"
curl -s -o /tmp/iam-token.json -X POST "$IAM/v1/oauth/token" -H "$CT" -d '{"grant_type":"client_credentials","client_id":"cloud-mgmt","client_secret":"cloud-mgmt-secret"}'
echo "token issued ok"
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"client:cloud-mgmt","app":"cmdb","action":"cmdb:host:read"}'; echo -n " / "
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"client:cloud-mgmt","app":"cmdb","action":"cmdb:host:create"}'; echo

say "8. 网关 PEP 链路（Traefik → forwardAuth → PDP）：业务侧身份头 X-User"
echo "> alice GET /api/v1/hosts（应 200）"
curl -s -o /dev/null -w "  http=%{http_code}\n" "$GW/api/v1/hosts" -H "X-User: alice"
echo "> bob POST /api/v1/hosts（应 403）"
curl -s -o /dev/null -w "  http=%{http_code}\n" -X POST "$GW/api/v1/hosts" -H "X-User: bob" -H "$CT" -d '{"name":"hack-host"}'
echo "> 无 X-User（应 403 deny-by-default）"
curl -s -o /dev/null -w "  http=%{http_code}\n" "$GW/api/v1/hosts"
echo "> 程序身份 client:cloud-mgmt GET（应 200，只读服务）"
curl -s -o /dev/null -w "  http=%{http_code}\n" "$GW/api/v1/hosts" -H "X-User: client:cloud-mgmt"

say "9. CMDB 宕机降级演示（可选：停掉 mock-cmdb 后仍可鉴权）"
if [ -n "${STOP_CMDB:-}" ]; then
  echo "> 停止 mock-cmdb 进程…（请手动 Ctrl-C mock-cmdb 终端）"
fi
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:read"}'; echo
echo "> 关系已物化在 OpenFGA 与本地索引，CMDB 宕机不影响鉴权（stale-but-available）"

say "10. 授权即审批：admin 给 bob 授 host:update（发起申请单 → bob 确认 → alice 复核 → 生效留痕）"
curl -s -o /tmp/iam-login.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"admin","password":"admin123"}'
LOGIN=$(python3 -c 'import json;print(json.load(open("/tmp/iam-login.json"))["access_token"])')
AUTH="Authorization: Bearer $LOGIN"
# bob 用户 id（用户名查询）
curl -s -o /tmp/iam-users.json -X GET "$IAM/api/v1/users?limit=100" -H "$AUTH"
BOB_ID=$(python3 -c 'import json;d=json.load(open("/tmp/iam-users.json"));print([u["id"] for u in d["items"] if u["username"]=="bob"][0])')
# 动态查询 cmdb:host:update 的 action id（ID 随种子变化）
curl -s -o /tmp/iam-actions.json -X GET "$IAM/api/v1/apps/1/actions" -H "$AUTH"
ACTION_ID=$(python3 -c 'import json;d=json.load(open("/tmp/iam-actions.json"));print([a["id"] for a in d["items"] if a["code"]=="cmdb:host:update"][0])')
# 发起授权申请单（createPolicy 不再直授，返回申请单 id + 审批链）
REQ_ID=$(curl -s -o /tmp/iam-req.json -X POST "$IAM/api/v1/policies" -H "$CT" -H "$AUTH" -d "{\"name\":\"grant:bob:update\",\"effect\":1,\"subject_type\":1,\"subject_id\":$BOB_ID,\"app_id\":1,\"action_ids\":[$ACTION_ID],\"resource_scope\":null,\"conditions\":{},\"force_remote\":false,\"reason\":\"上线变更需要主机更新权限（demo）\"}" && python3 -c 'import json;print(json.load(open("/tmp/iam-req.json"))["id"])')
echo "> 授权申请单 #$REQ_ID 已创建，审批链: $(python3 -c 'import json;print(json.load(open("/tmp/iam-req.json")).get("approval_chain"))')"
echo "> 步骤一：bob 本人确认（被授权方）"
curl -s -o /tmp/iam-bob.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"bob","password":"pass123"}'
BOB_TOKEN=$(python3 -c 'import json;print(json.load(open("/tmp/iam-bob.json"))["access_token"])')
curl -s -X POST "$IAM/api/v1/requests/$REQ_ID/approve" -H "$CT" -H "Authorization: Bearer $BOB_TOKEN" -d '{"action":1,"comment":"我同意"}'; echo
echo "> 步骤二：alice 复核（应用其他负责人）"
curl -s -o /tmp/iam-alice.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"alice","password":"pass123"}'
ALICE_TOKEN=$(python3 -c 'import json;print(json.load(open("/tmp/iam-alice.json"))["access_token"])')
curl -s -X POST "$IAM/api/v1/requests/$REQ_ID/approve" -H "$CT" -H "Authorization: Bearer $ALICE_TOKEN" -d '{"action":1,"comment":"同意，注意变更窗口"}'; echo
echo "> bob update 检查（应 allow）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:update"}'; echo
echo "> 留痕校验：bob 权限的授权链（申请单/审批人/理由）"
curl -s -X GET "$IAM/api/v1/me/permissions" -H "Authorization: Bearer $BOB_TOKEN" | python3 -m json.tool | head -60

say "11. 本地 agent 决策（若已启动 :19090）"
if curl -s -m 2 $AGENT/healthz >/dev/null 2>&1; then
  curl -s -X POST $AGENT/v1/local/check -H "$CT" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read"}'; echo
  curl -s -X POST $AGENT/v1/local/check -H "$CT" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:create"}'; echo
else
  echo "（agent 未运行，跳过；启动方式：make run-agent）"
fi

# ===== 数据契约与新鲜度演示（实施清单 A3/A4/A5a/A5b/A6，2026-09-22）=====
MOCKP=http://localhost:18090
OFGA=http://localhost:18081

say "12. 能力包 v12：应用元数据（网络信息 + 鉴权方式）"
curl -s -X GET "$IAM/api/v1/apps/1" -H "$AUTH" | python3 -c 'import json,sys;d=json.load(sys.stdin);a=d["app"];print("  net:", sorted((a.get("net_info") or {}).keys()));print("  auth:", [m.get("type") for m in (a.get("auth") or [])])'

say "13. 能力包 v12：范围选项（独立表，预设×模型）"
# 动态解析 cmdb「主机管理」能力 ID（reset 后自增顺序可能变化，不硬编码）
CAP_ID=$(curl -s -X GET "$IAM/api/v1/apps/1/capabilities" -H "$AUTH" | python3 -c 'import json,sys;d=json.load(sys.stdin);print([c["id"] for c in d["items"] if c["name"]=="主机管理"][0])')
echo "  主机管理 capability id=$CAP_ID"
curl -s -X GET "$IAM/api/v1/capabilities/$CAP_ID/presets/readonly/models/host/options" -H "$AUTH" | python3 -c 'import json,sys;d=json.load(sys.stdin);print("  options:", [o["type"] for o in d["options"]])'

say "14. 能力包 v12：预设级上架/下架（审批→工单留痕）"
curl -s -X POST "$IAM/api/v1/apps/1/capabilities/$CAP_ID/publish" -H "$CT" -H "$AUTH" -d '{"action":"publish","preset_ids":["operator"]}'; echo
curl -s -X POST "$IAM/api/v1/apps/1/capabilities/$CAP_ID/publish" -H "$CT" -H "$AUTH" -d '{"action":"offline","preset_ids":["operator"]}'; echo

say "15. 能力包 v12：市场申请（预设过滤 + 双主体 + 范围选择 → 自动生成 CEL）"
curl -s -X POST "$IAM/api/v1/requests/preview" -H "$CT" -H "$AUTH" -d "{\"app_id\":1,\"capability_id\":$CAP_ID,\"preset_id\":\"readonly\",\"subject_type\":1,\"subject_id\":$BOB_ID,\"scope_selections\":[{\"model\":\"host\",\"type\":\"select\",\"selectedValue\":\"prod\"}]}" | python3 -c 'import json,sys;d=json.load(sys.stdin);print("  expr:", d["expression"]["engine"]);print("  code:", d["expression"]["code"])'

say "16. 能力包 v12：接入申请（前置鉴权 + 网络开通，凭证一次签发）"
curl -s -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"erin","password":"pass123"}' > "$TMP/erin.json"
ERIN_TOKEN=$(python3 -c 'import json;print(json.load(open("'$TMP'/erin.json"))["access_token"])')
CLOUD_ID=$(curl -s -X GET "$IAM/api/v1/users/me" -H "Authorization: Bearer $ERIN_TOKEN" | python3 -c 'import json,sys;d=json.load(sys.stdin);print([a["id"] for a in d["apps"] if a["code"]=="cloudportal"][0])')
ONBOARD=$(curl -s -X POST "$IAM/api/v1/requests" -H "$CT" -H "Authorization: Bearer $ERIN_TOKEN" -d "{\"request_type\":3,\"consumer_app_id\":$CLOUD_ID,\"provider_app_id\":1,\"auth_method\":\"oauth2_client_credentials\",\"network_ticket\":true,\"reason\":\"接入 cmdb（demo）\"}")
OID=$(echo "$ONBOARD" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
echo "  接入申请单 #$OID 已提交（凭证待审批后签发）"

say "17. 授权管理聚合（预设状态 + 四维概况）"
curl -s -X GET "$IAM/api/v1/apps/1/capabilities/$CAP_ID/authz" -H "$AUTH" | python3 -c 'import json,sys;d=json.load(sys.stdin);print("  presets:", [(p["id"],p["status"]) for p in d["presets"]]);print("  grants:", d["grants"])'

say "18. 数据契约 · 集合指纹 · 巡检失败历史（A3/A4）"
echo "> 上游集合指纹（mock /sync/fingerprint?model=host）："
curl -s "$MOCKP/sync/fingerprint?model=host" | python3 -m json.tool | head -10
echo "> 数据契约与确认制时钟（GET /api/v1/sync/contracts）："
curl -s "$IAM/api/v1/sync/contracts" -H "$AUTH" | python3 -c 'import json,sys
for c in json.load(sys.stdin)["items"]:
    print("  %s algo=%s sla=%ss max=%ss clock_running=%s watermarked=%s" % (
        c["model"], c["algorithm"], c["staleness_sla_sec"], c["degrade_max_age_sec"],
        bool(c.get("last_confirmed_fresh_at")), bool(c.get("sync_watermark_at"))))'
echo "> 巡检日志最近 3 条（reachable / fingerprint_match / sync_ok / fresh_age）："
curl -s "$IAM/api/v1/sync/patrol-logs?limit=3" -H "$AUTH" | python3 -c 'import json,sys
for l in json.load(sys.stdin)["items"]:
    print("  %s reachable=%s match=%s sync_ok=%s age=%ss" % (
        l["domain"], l["reachable"], l["fingerprint_match"], l["sync_ok"], l["fresh_age_sec"]))'
echo "> 增量过滤（A4 L1 义务：updated_after 远古=全量、未来=空）："
curl -s "$MOCKP/api/v1/models/host/instances?updated_after=2000-01-01T00:00:00Z" | python3 -c 'import json,sys;print("  count(远古)=",len(json.load(sys.stdin)))'
curl -s "$MOCKP/api/v1/models/host/instances?updated_after=2999-01-01T00:00:00Z" | python3 -c 'import json,sys;print("  count(未来)=",len(json.load(sys.stdin)))'

say "19. 实例删除级联清理（A5a：PG+OpenFGA 双侧，幽灵授权=判多红线）"
echo "> 删除前：alice 读 host-5（web-01，应 allow）"
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-5","operation":"read"}'; echo
echo "> 删除 mock 实例 host-5（事件 → 投影行 + OpenFGA 关系级联清理）："
curl -s -X DELETE "$MOCKP/api/v1/models/host/instances/5"; echo
sleep 2
echo "> 事件链清理后重查（应 deny code=DATA_MISSING，fail-closed 拒单条）："
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-5","operation":"read"}'; echo
echo "> OpenFGA 关系残留（应 tuples:[] —— purge 生效，无幽灵授权）："
SID=$(curl -s "$OFGA/stores" | python3 -c 'import json,sys;print(json.load(sys.stdin)["stores"][0]["id"])')
curl -s -X POST "$OFGA/stores/$SID/read" -H "$CT" -d '{"tuple_key":{"object":"host:host-5"}}' | python3 -m json.tool | head -5

say "20. 新鲜度三态：降级续判 → 超龄拒绝 → 恢复自愈（2.3.1 确认制状态机）"
echo "> 0) 当前（应 allow，fresh）：alice 读 host-6"
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-6","operation":"read"}'; echo
echo "> 1) 停 mock-cmdb（上游不可达 → 确认制时钟不再刷新；host 契约 SLA=15s/上限=30s，巡检周期 5s）"
docker compose -f deploy/docker-compose.yml stop mock-cmdb >/dev/null
echo "> 2) 等待 40s（年龄越过 30s 上限 → Expired）…"
sleep 40
echo "> 3) Expired 判定（应 deny code=DATA_STALE_OVERDUE，仅该数据域数据级）："
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-6","operation":"read"}'; echo
echo "> 4) 接口级鉴权不受影响（应仍 allow —— Expired 只拒该域数据级）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read"}'; echo
echo "> 5) 恢复 mock → 巡检（≤10s）指纹确认 → 时钟刷新 → recovery（恢复不解禁、同步落地才解禁）"
docker compose -f deploy/docker-compose.yml start mock-cmdb >/dev/null
sleep 15
echo "> 6) 恢复后判定（应 allow）："
curl -s -X POST "$IAM/v1/authz/check-instance" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read","model":"host","instance_id":"host-6","operation":"read"}'; echo
echo "> 7) 决策日志检索（data_stale_overdue / recovery / force_remote 三类 reason 可查）："
curl -s "$IAM/api/v1/decision-logs?limit=200" -H "$AUTH" | python3 -c 'import json,sys
d=json.load(sys.stdin); items=d.get("items") if isinstance(d,dict) else d
if not isinstance(items,list): items=[]
for tok in ("data_stale_overdue","recovery","force_remote"):
    print("  %s: %d" % (tok, sum(1 for i in items if tok in str(i.get("reason","")))))'

say "21. 深对账手动触发（A5b：三类差异——常规更新 / 孤儿双侧清理 / 静默漂移告警）"
curl -s -X POST "$IAM/api/v1/sync/reconcile" -H "$AUTH" | python3 -m json.tool | head -30
echo "> （干净状态下 orphans/drift 为空；静默漂移=改数据不改 updated_at 的 L1/L2 盲区，由本通道天级兜底）"

say "22. 定制需求卡（A8 非目录请求：包覆盖不到 → 定制单 → owner 直授带 TTL → 判定排除+回收）"
echo "> 0) 授权前：bob 用 cmdb:host:delete（能力目录里有但无人授权 → 应 deny）"
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:delete"}'; echo
echo "> 1) bob 提交定制需求单（虚拟卡入口的 API 等价：诉求 + 勾选想要的动作）"
ACTION_DEL=$(curl -s "$IAM/api/v1/apps/1/actions" -H "$AUTH" | python3 -c 'import json,sys;print([a["id"] for a in json.load(sys.stdin)["items"] if a["code"]=="cmdb:host:delete"][0])')
CUSTOM_ID=$(curl -s -o /tmp/iam-custom.json -X POST "$IAM/api/v1/apps/1/custom-requests" -H "$CT" -H "Authorization: Bearer $BOB_TOKEN" -d "{\"description\":\"运维脚本需要清理过期测试主机（定制诉求 demo）\",\"action_ids\":[$ACTION_DEL]}" && python3 -c 'import json;print(json.load(open("/tmp/iam-custom.json"))["id"])')
echo "> 定制单 #$CUSTOM_ID 已创建，owner 审批链: $(python3 -c 'import json;print(json.load(open("/tmp/iam-custom.json")).get("approval_chain"))')"
echo "> 2) owner（alice）处置：直接授权 + 强制 TTL 1 天（A8：不留游离授权碎片）"
CUSTOM_POLICY=$(curl -s -o /tmp/iam-fulfill.json -X POST "$IAM/api/v1/requests/$CUSTOM_ID/fulfill" -H "$CT" -H "Authorization: Bearer $ALICE_TOKEN" -d '{"mode":"grant","ttl_days":1,"note":"定制诉求合理，直授并限期回收"}' && python3 -c 'import json;print(json.load(open("/tmp/iam-fulfill.json"))["policy_id"])')
echo "> 策略 #$CUSTOM_POLICY 已创建（expires_at=now+1d）——立即生效（缓存已 bump）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:delete"}'; echo
echo "> 3) TTL 快进（演示用 psql 把该策略 expires_at 改到 1 分钟前）"
docker exec devops-postgres psql -U devops -d devops_iam -t -c "update policies set expires_at = now() - interval '1 minute' where id = $CUSTOM_POLICY;" >/dev/null && echo "  已快进"
echo "> 4) 等待 66s（builder 缓存 30s 重建排除 + ttlSweep 60s 回收元组/重发布 bundle）…"
sleep 66
echo "> 5) TTL 到期后判定（应 deny —— ActiveByApp 已排除过期策略）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:delete"}'; echo
echo "> 6) 回收落地核验（status 应已置 0、expires_at 已过）："
docker exec devops-postgres psql -U devops -d devops_iam -t -c "select 'policy#' || $CUSTOM_POLICY || ' status=' || status || ' expired=' || (expires_at <= now()) from policies where id = $CUSTOM_POLICY;"
echo "> 7) 申请人视角：审批中心工单（定制需求类型可见、已处置）："
curl -s "$IAM/api/v1/tickets?type=all&role=applicant" -H "Authorization: Bearer $BOB_TOKEN" | python3 -c 'import json,sys
for t in json.load(sys.stdin)["items"][:4]:
    print("  %s %s [%s]" % (t["ticket_no"], t["title"], t["status"]))'

say "完成 ✅"
