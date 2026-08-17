#!/usr/bin/env bash
# 一键演示脚本：正常链路 → 无权限 → CMDB 宕机降级 → 策略发布生效 → 本地 agent 决策
# 前置：make up && make seed && make run && make run-cmdb && make run-id
set -eu

IAM=https://api.permission-center.orb.local
GW=https://cmdb.permission-center.orb.local
AGENT=http://localhost:19090
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

say "完成 ✅"
