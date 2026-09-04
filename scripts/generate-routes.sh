#!/usr/bin/env bash
# ============================================================
# generate-routes —— 从模板生成网关路由文件
# 用法：bash scripts/generate-routes.sh
# 依赖：deploy/<env>/.env.<env> 中定义了 SERVER_IP
# 原理：将 routes.yml.template 中的 __SERVER_IP__ 替换为实际 IP，
#       输出到 routes.yml（已被 .gitignore 忽略，不入仓）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
load_env

TEMPLATE="infra/gateway/dynamic/routes.yml.template"
OUTPUT="infra/gateway/dynamic/routes.yml"

if [ ! -f "$TEMPLATE" ]; then
  err "缺少模板文件: ${TEMPLATE}"
  exit 1
fi

if [ -z "${SERVER_IP:-}" ]; then
  err ".env 文件中未定义 SERVER_IP"
  exit 1
fi

log "生成网关路由: SERVER_IP=${SERVER_IP}"
sed "s/__SERVER_IP__/${SERVER_IP}/g" "$TEMPLATE" > "$OUTPUT"
ok "路由已生成: ${OUTPUT}"
