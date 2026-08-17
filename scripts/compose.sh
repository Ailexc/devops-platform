#!/usr/bin/env bash
# ============================================================
# compose —— 统一 Compose 操作（up/build/down/logs/ps）
# 用法：make up P=auth | bash scripts/compose.sh up auth
#       bash scripts/compose.sh <action> [project]
#   action : up | build | down | logs | ps
#   project: auth/cloud/event/iam/release/cmdb/workflow（空 = 全部）
# 说明：统一处理各项目 compose 文件位置差异
#       （CloudManager → docker-compose.prod.yml；PermissionCenter → deploy/）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

ACTION="${1:-up}"
P="${2:-}"

case "$ACTION" in
  up|build|down|logs|ps) ;;
  *) err "未知操作 '$ACTION'（可用: up/build/down/logs/ps）"; exit 1 ;;
esac

run_one() {
  local name="$1" dir opts
  dir="$(project_dir "$name")"
  opts="$(project_compose_opts "$name")"
  echo "==> ${ACTION} ${name} (${dir} ${opts})"
  case "$ACTION" in
    up)    ( cd "$dir" && docker compose ${opts} up -d --build ) ;;
    build) ( cd "$dir" && docker compose ${opts} build ) ;;
    down)  ( cd "$dir" && docker compose ${opts} down ) ;;
    logs)  ( cd "$dir" && docker compose ${opts} logs -f --tail=200 ) ;;
    ps)    ( cd "$dir" && docker compose ${opts} ps ) ;;
  esac
}

if [ -n "${P}" ]; then
  require_project "${P}"
  run_one "${P}"
else
  for p in auth cloud event iam release cmdb workflow; do
    run_one "${p}" || true
  done
fi
ok "compose ${ACTION} 完成"
