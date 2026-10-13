#!/usr/bin/env bash
# 一键演示脚本（1.5）：正常链路 → 数据级点查（网关即判/带体调用）→ M2M → 网关 PEP →
#   授权即审批 → 本地 agent → 能力包 → 点查链路展示 → 行删除 fail-closed → TTL 回收
# 前置：make up（iam-server + iam-sync 仅 TTL 回收）&& make seed && make run && make run-cmdb && make run-id
# 数据级前提：应用回查配置/路由取材声明由场景 4/6 自动登记（1.5 投影已退役，判定材料一律实时点查）
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

say "4. 数据级鉴权（1.5 点查取材）：bob 只读 host-4（条件授权 ip=10.0.0.11，网关链路即判）"
# ① 管理员登录（数据级配置与后续场景共用）
curl -s -o /tmp/iam-login.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"admin","password":"admin123"}'
LOGIN=$(python3 -c 'import json;print(json.load(open("/tmp/iam-login.json"))["access_token"])')
AUTH="Authorization: Bearer $LOGIN"
curl -s -o /tmp/iam-users.json -X GET "$IAM/api/v1/users?limit=100" -H "$AUTH"
BOB_ID=$(python3 -c 'import json;d=json.load(open("/tmp/iam-users.json"));print([u["id"] for u in d["items"] if u["username"]=="bob"][0])')
# ② 应用回查配置（§3.1 一系统一约定：内部地址不过网关=零豁免）
curl -s -X PUT "$IAM/api/v1/apps/1/perm-query" -H "$AUTH" -d '{"url":"http://mock-cmdb:8090/__perm/query","token":"demo-perm-token"}' -o /dev/null -w "  perm-query 配置 http=%{http_code}\n"
# ③ 五格登记：cmdb:host:read 勾数据级 + 取材声明 path.id（§3.7——网关持有 URI 自提取）
ACTION_READ=$(curl -s "$IAM/api/v1/apps/1/actions" -H "$AUTH" | python3 -c 'import json,sys;print([a["id"] for a in json.load(sys.stdin)["items"] if a["code"]=="cmdb:host:read"][0])')
curl -s -X PATCH "$IAM/api/v1/apps/1/routes/$ACTION_READ" -H "$AUTH" -d '{"need_data":true,"material":{"mode":"id_path","path":"path.id"}}' -o /dev/null -w "  取材声明登记 http=%{http_code}\n"
# ④ 条件授权（申请-审批）：bob host:read × ip=10.0.0.11（组的空集合策略不放行，判少安全）
REQ4=$(curl -s -o /tmp/iam-req4.json -X POST "$IAM/api/v1/policies" -H "$CT" -H "$AUTH" -d "{\"name\":\"demo:bob:host-read-ip11\",\"effect\":1,\"subject_type\":1,\"subject_id\":$BOB_ID,\"app_id\":1,\"action_ids\":[$ACTION_READ],\"resource_scope\":{\"model\":\"host\",\"condition\":{\"op\":\"eq\",\"field\":\"ip\",\"value\":\"10.0.0.11\"}},\"conditions\":{},\"reason\":\"只允许读网段巡检机（demo）\"}" && python3 -c 'import json;print(json.load(open("/tmp/iam-req4.json"))["id"])')
curl -s -o /tmp/iam-alice.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"alice","password":"pass123"}'
ALICE_T4=$(python3 -c 'import json;print(json.load(open("/tmp/iam-alice.json"))["access_token"])')
curl -s -o /tmp/iam-bob.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"bob","password":"pass123"}'
BOB_T4=$(python3 -c 'import json;print(json.load(open("/tmp/iam-bob.json"))["access_token"])')
echo "> 审批链两级：① bob 本人确认（被授权方——让他知道、让他同意）→ ② alice 复核（应用 owner）"
curl -s -X POST "$IAM/api/v1/requests/$REQ4/approve" -H "$CT" -H "Authorization: Bearer $BOB_T4" -d '{"action":1,"comment":"我知道并同意"}' -o /dev/null
curl -s -X POST "$IAM/api/v1/requests/$REQ4/approve" -H "$CT" -H "Authorization: Bearer $ALICE_T4" -d '{"action":1,"comment":"同意（demo 条件授权）"}' -o /dev/null
# ⑤ 网关链路即判：中心查表→按约定点查权威行→验谓词（业务零配合）
echo "> bob GET /api/v1/hosts/host-4（ip=.11 命中条件 → 应 200）"
SC4=$(curl -s -o /tmp/iam-gw4.txt -w "%{http_code}" "$GW/api/v1/hosts/host-4" -H "X-User: bob")
echo "  http=$SC4"
if [ "$SC4" != "200" ]; then
  echo "  ✗ FAIL：点查+谓词应放行 200（硬断言1）——回查配置/取材声明/条件授权链路断裂" >&2; cat /tmp/iam-gw4.txt >&2; exit 1
fi
echo "  ✓ 硬断言1：网关点查放行 200（权威行 ip=10.0.0.11 × 条件授权）"

say "5. 谓词不匹配拒单条：bob 读 host-5（ip=10.0.0.12≠授权 .11 → 应 403 NO_PERMISSION）"
SC5=$(curl -s -o /tmp/iam-gw5.txt -w "%{http_code}" "$GW/api/v1/hosts/host-5" -H "X-User: bob")
echo "  http=$SC5"
[ "$SC5" = "403" ] || { echo "  ✗ FAIL：谓词不匹配应 403（硬断言2）" >&2; exit 1; }
grep -q NO_PERMISSION /tmp/iam-gw5.txt || { echo "  ✗ FAIL：应 NO_PERMISSION" >&2; cat /tmp/iam-gw5.txt >&2; exit 1; }
echo "  ✓ 硬断言2：谓词不匹配 403 NO_PERMISSION（行在、条件不命中=判少方向）"
echo "> 未登记路由 deny-by-default（运行期纯查表零推断）："
curl -s -o /dev/null -w "  http=%{http_code}\n" "$GW/api/v1/not-registered" -H "X-User: bob"

say "6. 带体调用（创建=信封材料 fetch-and-bring）：alice 对 disk-create 的条件授权两连判"
# 五格登记：cmdb:disk:create 勾数据级 + 信封声明 .meta.type
ACTION_DCREATE=$(curl -s "$IAM/api/v1/apps/1/actions" -H "$AUTH" | python3 -c 'import json,sys;print([a["id"] for a in json.load(sys.stdin)["items"] if a["code"]=="cmdb:disk:create"][0])')
curl -s -X PATCH "$IAM/api/v1/apps/1/routes/$ACTION_DCREATE" -H "$AUTH" -d '{"need_data":true,"material":{"mode":"envelope","field_path":".meta.type"}}' -o /dev/null
# 条件授权：alice disk-create × type=ssd
REQ6=$(curl -s -o /tmp/iam-req6.json -X POST "$IAM/api/v1/policies" -H "$CT" -H "$AUTH" -d "{\"name\":\"demo:alice:disk-create-ssd\",\"effect\":1,\"subject_type\":1,\"subject_id\":2,\"app_id\":1,\"action_ids\":[$ACTION_DCREATE],\"resource_scope\":{\"condition\":{\"op\":\"eq\",\"field\":\"type\",\"value\":\"ssd\"}},\"conditions\":{},\"reason\":\"只允许建高效盘（demo）\"}" && python3 -c 'import json;print(json.load(open("/tmp/iam-req6.json"))["id"])')
curl -s -X POST "$IAM/api/v1/requests/$REQ6/approve" -H "$CT" -H "Authorization: Bearer $ALICE_T4" -d '{"action":1,"comment":"同意（demo）"}' -o /dev/null
echo "> 带体判定：material.meta.type=ssd（应 allow）"
R6A=$(curl -s -X POST "$IAM/v1/authz/check-material" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:disk:create","material":{"meta":{"type":"ssd"}},"trace_id":"demo-6a"}')
echo "  $R6A"
echo "$R6A" | grep -q '"allow"' || { echo "  ✗ FAIL：信封 ssd 应 allow（硬断言3a）" >&2; exit 1; }
echo "> 带体判定：material.meta.type=hdd（应 deny NO_PERMISSION）"
R6B=$(curl -s -X POST "$IAM/v1/authz/check-material" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:disk:create","material":{"meta":{"type":"hdd"}},"trace_id":"demo-6b"}')
echo "  $R6B"
echo "$R6B" | grep -q NO_PERMISSION || { echo "  ✗ FAIL：信封 hdd 应 deny NO_PERMISSION（硬断言3b）" >&2; exit 1; }
echo "  ✓ 硬断言3：信封创建两连判 allow(ssd)/deny(hdd)——材料即‘未来的行’，伪造被授权集封顶"

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

say "9. 动作级判定不依赖上游（策略快照本地；数据级点查的上游依赖见场景 20）"
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:read"}'; echo
echo "> 动作级读本地策略快照，上游宕机不影响；数据级=点查权威行，不可达时 fail-closed"

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
REQ_ID=$(curl -s -o /tmp/iam-req.json -X POST "$IAM/api/v1/policies" -H "$CT" -H "$AUTH" -d "{\"name\":\"grant:bob:update\",\"effect\":1,\"subject_type\":1,\"subject_id\":$BOB_ID,\"app_id\":1,\"action_ids\":[$ACTION_ID],\"resource_scope\":null,\"conditions\":{},\"reason\":\"上线变更需要主机更新权限（demo）\"}" && python3 -c 'import json;print(json.load(open("/tmp/iam-req.json"))["id"])')
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

# ===== 点查取材演示（1.5——投影机制已退役：判定材料一律实时点查权威行）=====
MOCKP=http://localhost:18090

say "18. 点查链路三件套：应用回查配置 + 契约白名单 + 路由取材声明"
echo "> ① 应用回查配置（系统内部地址，零豁免）："
curl -s "$IAM/api/v1/apps/1" -H "$AUTH" | python3 -c 'import json,sys;a=json.load(sys.stdin)["app"];print("  perm_query_url:", a.get("perm_query_url") or "（未配置）");print("  凭证:", "已配置" if a.get("perm_query_token") else "缺失")'
echo "> ② 数据契约登记（fields=判定字段清单；点查模型白名单）："
curl -s "$IAM/api/v1/sync/contracts" -H "$AUTH" | python3 -c 'import json,sys
items=json.load(sys.stdin)["items"]
if not any(c["model"]=="host" for c in items):
    print("  ✗ FAIL：契约登记缺 host 域（点查白名单不完整）", file=sys.stderr); sys.exit(1)
for c in items: print("  %s fields=%s algo=%s" % (c["model"], c["fields"], c["algorithm"]))
print("  ✓ 硬断言4：契约登记含 host（白名单就绪）")'
echo "> ③ 路由取材声明（五格登记的 need_data 动作清单）："
curl -s "$IAM/api/v1/apps/1/routes" -H "$AUTH" | python3 -c 'import json,sys
items=[a for a in json.load(sys.stdin)["items"] if a.get("need_data")]
if not items:
    print("  ✗ FAIL：无 need_data 路由（场景4/6 的取材声明未生效？）", file=sys.stderr); sys.exit(1)
for a in items: print("  %s %s → %s" % (a["code"], a.get("path") or "-", (a.get("material") or {}).get("mode")))'

say "19. 行删除 → 点查 data_missing（fail-closed 拒单条——判少不判多）"
echo "> 删除前：bob 读 host-4（条件 ip=.11 命中 → 应 200）"
curl -s -o /dev/null -w "  http=%{http_code}\n" "$GW/api/v1/hosts/host-4" -H "X-User: bob"
echo "> 删除 mock 实例 host-4（权威源行没了——无投影无级联，判定实时看权威源）"
curl -s -X DELETE "$MOCKP/api/v1/models/host/instances/4"; echo
sleep 2
echo "> 重查（应 403 DATA_MISSING）："
R19=$(curl -s "$GW/api/v1/hosts/host-4" -H "X-User: bob")
echo "  $R19"
if ! echo "$R19" | grep -q DATA_MISSING; then
  echo "  ✗ FAIL：应 deny code=DATA_MISSING——点查 404 未走 fail-closed（硬断言5）" >&2; exit 1
fi
echo "  ✓ 硬断言5：DATA_MISSING（行删除即判少，幽灵授权不存在）"

say "20. 点查源不可用 = fail-closed + 恢复复通（1.5 的『上游挂了还鉴权吗』）"
echo "> 0) 正常：alice 读 host-6（alice 全量只读 → 应 200）"
SC20=$(curl -s -o /dev/null -w "%{http_code}" "$GW/api/v1/hosts/host-6" -H "X-User: alice")
echo "  http=$SC20"
[ "$SC20" = "200" ] || { echo "  ✗ FAIL：正常态应 200（硬断言6a 前置）" >&2; exit 1; }
echo "> 1) 停 mock-cmdb（权威源不可达）"
docker compose -f deploy/docker-compose.yml stop mock-cmdb >/dev/null
echo "> 2) 点查失败 → deny（应 403 DATA_SOURCE_UNAVAILABLE——fail-closed，无静默放行）"
R20=$(curl -s "$GW/api/v1/hosts/host-6" -H "X-User: alice")
echo "  $R20"
if ! echo "$R20" | grep -q DATA_SOURCE_UNAVAILABLE; then
  echo "  ✗ FAIL：应 DATA_SOURCE_UNAVAILABLE（硬断言6a）——先恢复环境" >&2
  docker compose -f deploy/docker-compose.yml start mock-cmdb >/dev/null; exit 1
fi
echo "  ✓ 硬断言6a：DATA_SOURCE_UNAVAILABLE（取材失败 fail-closed，无隐式降级）"
echo "> 3) 动作级不受影响（策略快照本地，不依赖上游）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"alice","app":"cmdb","action":"cmdb:host:read"}'; echo
echo "> 4) 恢复 mock-cmdb → 点查复通（应 200）"
docker compose -f deploy/docker-compose.yml start mock-cmdb >/dev/null
sleep 3
SC20B=$(curl -s -o /dev/null -w "%{http_code}" "$GW/api/v1/hosts/host-6" -H "X-User: alice")
echo "  http=$SC20B"
[ "$SC20B" = "200" ] || { echo "  ✗ FAIL：恢复后应 200（硬断言6b）" >&2; exit 1; }
echo "  ✓ 硬断言6b：恢复复通（无缓存放行——点查即实时）"

#（原场景21『深对账』已随投影机制退役下线：判定不再依赖投影库，无对账对象）

say "21. 列表判定两步（1.5）：契约登记 → 缺参拒 / 超授权拒 / 业务真过滤（契约测试）"
# ① 五格登记：cmdb:host:list 挂范围参数 env@query（required）——契约两件之一
ACTION_LIST=$(curl -s "$IAM/api/v1/apps/1/actions" -H "$AUTH" | python3 -c 'import json,sys;print([a["id"] for a in json.load(sys.stdin)["items"] if a["code"]=="cmdb:host:list"][0])')
curl -s -X PATCH "$IAM/api/v1/apps/1/routes/$ACTION_LIST" -H "$AUTH" -d '{"scope_param":{"param":"env","location":"query","required":true}}' -o /dev/null -w "  范围参数登记 http=%{http_code}\n"
# ② 条件授权（两级审批）：frank host:list × env=prod
curl -s -o /tmp/iam-frank.json -X POST "$IAM/api/v1/auth/login" -H "$CT" -d '{"username":"frank","password":"pass123"}'
FRANK_T21=$(python3 -c 'import json;print(json.load(open("/tmp/iam-frank.json"))["access_token"])')
REQ21=$(curl -s -o /tmp/iam-req21.json -X POST "$IAM/api/v1/policies" -H "$CT" -H "$AUTH" -d "{\"name\":\"demo:frank:host-list-prod\",\"effect\":1,\"subject_type\":1,\"subject_id\":5,\"app_id\":1,\"action_ids\":[$ACTION_LIST],\"resource_scope\":{\"model\":\"host\",\"condition\":{\"op\":\"eq\",\"field\":\"env\",\"value\":\"prod\"}},\"conditions\":{},\"reason\":\"只看生产主机列表（demo）\"}" && python3 -c 'import json;print(json.load(open("/tmp/iam-req21.json"))["id"])')
curl -s -X POST "$IAM/api/v1/requests/$REQ21/approve" -H "$CT" -H "Authorization: Bearer $FRANK_T21" -d '{"action":1,"comment":"我知道并同意"}' -o /dev/null
curl -s -X POST "$IAM/api/v1/requests/$REQ21/approve" -H "$CT" -H "Authorization: Bearer $ALICE_T4" -d '{"action":1,"comment":"同意（demo 列表契约）"}' -o /dev/null
echo "> 三态判定：?env=prod 应 200 / ?env=dev 应 403 NO_PERMISSION / 无参应 403 MISSING_SCOPE_PARAM"
S21A=$(curl -s -o /dev/null -w "%{http_code}" "$GW/api/v1/hosts?env=prod" -H "X-User: frank")
S21B=$(curl -s "$GW/api/v1/hosts?env=dev" -H "X-User: frank")
S21C=$(curl -s "$GW/api/v1/hosts" -H "X-User: frank")
echo "  env=prod:$S21A / env=dev:$(echo "$S21B" | head -c 60) / 无参:$(echo "$S21C" | head -c 60)"
if [ "$S21A" != "200" ] || ! echo "$S21B" | grep -q NO_PERMISSION || ! echo "$S21C" | grep -q MISSING_SCOPE_PARAM; then
  echo "  ✗ FAIL：判定两步三态（硬断言8）" >&2; exit 1
fi
echo "  ✓ 硬断言8：判定两步三态（缺参拒/超授权拒/授权值过）"
echo "> 一次性契约测试（中心出脚本：业务真按字段过滤 = 判定字段落库字段）："
bash scripts/contract-test.sh frank /api/v1/hosts env prod dev || { echo "  ✗ FAIL：契约测试（硬断言9）" >&2; exit 1; }
echo "  ✓ 硬断言9：契约测试通过（判定两步 + 业务过滤闭环）"

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
echo "> 4) 等待 66s（builder 缓存 30s 重建排除 + ttlSweep 60s 回收策略/重发布 bundle）…"
sleep 66
echo "> 5) TTL 到期后判定（应 deny —— ActiveByApp 已排除过期策略）："
curl -s -X POST "$IAM/v1/authz/check" -H "$CT" -H "$PEP" -d '{"user":"bob","app":"cmdb","action":"cmdb:host:delete"}'; echo
echo "> 6) 回收落地核验（status 应已置 0、expires_at 已过）："
R22=$(docker exec devops-postgres psql -U devops -d devops_iam -t -c "select 'policy#' || $CUSTOM_POLICY || ' status=' || status || ' expired=' || (expires_at <= now()) from policies where id = $CUSTOM_POLICY;")
echo "$R22"
if ! echo "$R22" | grep -q "status=0"; then
  echo "  ✗ FAIL：status≠0——TTL 回收未落地（iam-sync ttlSweep 未跑，硬断言7）" >&2; exit 1
fi
echo "  ✓ 硬断言7：status=0（TTL 回收在 iam-sync 上生效）"
echo "> 7) 申请人视角：审批中心工单（定制需求类型可见、已处置）："
curl -s "$IAM/api/v1/tickets?type=all&role=applicant" -H "Authorization: Bearer $BOB_TOKEN" | python3 -c 'import json,sys
for t in json.load(sys.stdin)["items"][:4]:
    print("  %s %s [%s]" % (t["ticket_no"], t["title"], t["status"]))'

say "完成 ✅"
