#!/usr/bin/env bash
# T5 一次性契约测试（方案 §5.2：档 b 上线前置——中心出脚本、应用方跑）
# 验证两件事：
#   ① 判定两步：授权值=过 / 超授权值=拒 / 缺参=拒（契约 required 生效）
#   ② 判定字段=落库字段：业务 API 真按该参数过滤（返回行全部满足 参数=请求值）——不过=该域不得选判定两步主路、降档 c
# 用法：
#   IAM_DEMO=... GW_DEMO=... bash scripts/contract-test.sh <user> <list_path> <param> <allowed_v1[,v2]> <denied_v>
# 示例：
#   GW_DEMO=http://localhost:19080 bash scripts/contract-test.sh frank /api/v1/hosts env prod dev
set -eu
IAM=${IAM_DEMO:-https://api.permission-center.orb.local}
GW=${GW_DEMO:-https://cmdb.permission-center.orb.local}
USER=${1:?user}
LIST_PATH=${2:?list_path}
PARAM=${3:?param}
ALLOWED=${4:?allowed values (comma-separated)}
DENIED=${5:?denied value}

fails=0
IFS=',' read -ra VALS <<< "$ALLOWED"
for v in "${VALS[@]}"; do
  CODE=$(curl -s -o /tmp/ct-body.json -w "%{http_code}" "$GW${LIST_PATH}?${PARAM}=${v}" -H "X-User: $USER")
  if [ "$CODE" != "200" ]; then
    echo "  ✗ 授权值 $v 应 200，实测 $CODE"; fails=1; continue
  fi
  BAD=$(python3 -c "
import json
d=json.load(open('/tmp/ct-body.json')); rows=d.get('items') or []
def val(r):
    v=r.get('$PARAM')
    if v is None: v=(r.get('attributes') or {}).get('$PARAM')
    return v
print(sum(1 for r in rows if str(val(r))!='$v'))")
  if [ "$BAD" != "0" ]; then
    echo "  ✗ 业务未按 ${PARAM}=${v} 过滤（$BAD 行越界）——判定字段 ≠ 落库字段，不得上判定两步主路"; fails=1
  else
    echo "  ✓ ${PARAM}=${v}：200 且返回行全部命中（业务真过滤）"
  fi
done
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$GW${LIST_PATH}?${PARAM}=${DENIED}" -H "X-User: $USER")
if [ "$CODE" = "403" ]; then echo "  ✓ 超授权值 ${DENIED}：403（子集校验）"; else echo "  ✗ 超授权值 ${DENIED} 应 403，实测 $CODE"; fails=1; fi
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$GW${LIST_PATH}" -H "X-User: $USER")
if [ "$CODE" = "403" ]; then echo "  ✓ 缺参：403 MISSING_SCOPE_PARAM（契约 required 生效）"; else echo "  ✗ 缺参应 403，实测 $CODE"; fails=1; fi

if [ "$fails" = "0" ]; then echo "契约测试通过 ✅"; else echo "契约测试失败 ❌"; exit 1; fi
