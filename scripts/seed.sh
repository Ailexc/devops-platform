#!/usr/bin/env bash
# ============================================================
# seed —— 统一初始化数据入口（Phase 0 收编版）
# 用法：make seed [P=auth|cloud|event|iam|release|cmdb|workflow]
# 说明：接入统一 PG 过程中，各项目将统一为「启动时幂等种子」，
#       届时本脚本将收敛为 make seed 直接幂等触发。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

P="${1:-}"

seed_project() {
  case "$1" in
    auth)
      echo "  Authentication 启动时自动种子（migrate+seed），无需单独 seed；如需重置: make reset P=auth"
      ;;
    cloud)
      echo "  CloudManager 无独立 seed 命令，数据由 reset_db.sh 全链路生成；建议: make reset P=cloud"
      ;;
    event)
      ( cd EventManager && make init-all-docker )
      ;;
    iam)
      ( cd PermissionCenter && make seed )
      ;;
    release)
      ( cd ReleaseManager && docker compose --profile init run --rm init )
      ;;
    cmdb)
      ( cd TaskManager && docker compose exec backend python manage.py seed_demo_data )
      ;;
    workflow)
      ( cd WorkFlowCenter && docker compose exec api python manage.py seed_data )
      ;;
    *) err "未知项目 '$1'（可用: auth/cloud/event/iam/release/cmdb/workflow）"; exit 1 ;;
  esac
}

if [ -n "${P}" ]; then
  log "seed 项目: ${P}"
  seed_project "${P}"
else
  log "全量 seed"
  for p in auth cloud event iam release cmdb workflow; do
    echo "==> ${p}"
    seed_project "${p}" || true
  done
fi
ok "seed 完成"
