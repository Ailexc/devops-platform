#!/usr/bin/env bash
# ============================================================
# Authentication 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 契约要求：幂等 / 自包含（清库 + migrate + seed + 就绪等待）/ 自验证 / 无交互
# 顶层 reset-all.sh 爆破数据层后调用；也可独立运行（--full 连 LDAP 卷一起重置）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."                    # → 仓库根
source scripts/lib.sh
load_env >/dev/null                           # 独立运行时自识别环境
NO_BUILD="${NO_BUILD:-0}"
cd Authentication

FULL_FLAG="${1:-}"

echo "── [auth] 停止服务..."
docker compose down

echo "── [auth] 清空统一库 devops_auth（幂等）..."
drop_schema devops_auth

if [ "$FULL_FLAG" = "--full" ]; then
  echo "── [auth] 重置 LDAP 数据卷（--full）..."
  docker volume rm authentication_ldap-data 2>/dev/null || true
  docker volume rm authentication_ldap-config 2>/dev/null || true
fi

echo "── [auth] 启动（表结构 + 种子自动重建）..."
BUILD_FLAG="--build"; [ "$NO_BUILD" = "1" ] && BUILD_FLAG=""
docker compose up -d $BUILD_FLAG

echo "── [auth] 等待就绪..."
wait_http_ready authentication-auth-backend http://127.0.0.1:8000/docs 120

echo "── [auth] 自验证（JWKS 可用）..."
docker exec authentication-auth-backend python -c "
import urllib.request, json
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
keys = json.load(opener.open('http://127.0.0.1:8000/.well-known/jwks.json', timeout=5)).get('keys', [])
assert keys, 'JWKS 无公钥'
print(f'   ✓ JWKS 正常（{len(keys)} 把公钥）')
"

ok "  ✓ auth 重置完成"
