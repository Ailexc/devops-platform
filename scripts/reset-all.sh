#!/usr/bin/env bash
# ============================================================
# reset —— 统一数据重置入口（"回到出厂态"）
# 用法：make reset [P=auth|cloud|event|iam|release|cmdb|workflow]
#   - 带 P：先清空该项目统一库（DROP SCHEMA）→ 再跑该项目重置/种子
#   - 不带 P：删除重建全部统一业务库 + 逐项目重置
# 安全：所有重置前保留旧数据卷/文件（保守切换，确认后手动清理）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

P="${1:-}"
DBS=(devops_auth devops_cloud devops_event devops_event_go devops_iam devops_openfga devops_release devops_cmdb devops_cmdb_go devops_workflow)

# 项目短名 → 统一库
project_db() {
  case "$1" in
    auth) echo devops_auth ;;
    cloud) echo devops_cloud ;;
    event) echo devops_event ;;
    iam) echo devops_iam ;;
    release) echo devops_release ;;
    cmdb) echo devops_cmdb ;;
    workflow) echo devops_workflow ;;
    *) echo "" ;;
  esac
}

# 清空指定统一库（DROP SCHEMA → 重建）
drop_schema() {
  local db="$1"
  log "清空统一库 ${db}"
  if docker ps --format '{{.Names}}' | grep -q '^devops-postgres$'; then
    docker exec devops-postgres psql -U devops -d "$db" \
      -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" >/dev/null
    ok "  ${db} 已清空（schema 重建）"
  else
    err "统一 PostgreSQL 未运行，请先 make bootstrap"; exit 1
  fi
}

reset_project() {
  local db
  db="$(project_db "$1")"
  [ -n "${db}" ] && drop_schema "${db}"
  case "$1" in
    auth)
      ( cd Authentication && ./reset.sh )
      ;;
    cloud)
      ( cd CloudManager && ./reset_db.sh --yes )
      ;;
    event)
      ( cd EventManager && ./scripts/init-all.sh -c -t 1000 )
      ;;
    iam)
      ( cd PermissionCenter && make seed-reset )
      ;;
    release)
      ( cd ReleaseManager && ./scripts/reset-all.sh -y )
      ;;
    cmdb)
      # reset_data 为 TRUNCATE 语义（依赖既有表），schema 已清空 → 直接 migrate + 播种
      ( cd TaskManager && docker compose exec backend python manage.py migrate && \
        docker compose exec backend python manage.py seed_demo_data )
      ;;
    workflow)
      ( cd WorkFlowCenter && docker compose exec api python manage.py reset_demo )
      ;;
    *) err "未知项目 '$1'（可用: auth/cloud/event/iam/release/cmdb/workflow）"; exit 1 ;;
  esac
}

# 重置统一数据库（数据层出厂态：删除重建）
reset_infra_db() {
  log "删除重建统一业务库"
  docker exec devops-postgres psql -U devops -c "SELECT '基础设施已就绪'" >/dev/null 2>&1 || {
    err "统一 PostgreSQL 未运行，请先 make bootstrap"; exit 1
  }
  for db in "${DBS[@]}"; do
    docker exec devops-postgres psql -U devops -c "DROP DATABASE IF EXISTS ${db} WITH (FORCE);" >/dev/null 2>&1 || true
    docker exec devops-postgres createdb -U devops "${db}"
    echo "  ✓ ${db} 已重建"
  done
}

if [ -n "${P}" ]; then
  log "reset 项目: ${P}"
  reset_project "${P}"
else
  log "全量 reset"
  echo "  阶段一：重置统一数据库（数据层出厂态）"
  reset_infra_db
  echo ""
  echo "  阶段二：重建 sidecar 迁移（openfga / cmdb-go）"
  # OpenFGA：distroless 镜像需单独 migrate（幂等），须先于 iam 种子（建 store）
  ( cd PermissionCenter && docker compose -f deploy/docker-compose.yml run --rm openfga migrate >/dev/null 2>&1 ) \
    && echo "  ✓ openfga migrate 完成" \
    || { err "openfga migrate 失败"; exit 1; }
  # cmdb-go：旧容器用旧 hostname，需按当前 compose 重建（--seed 自动迁移+播种）
  ( cd TaskManager && docker compose up -d --force-recreate go_backend >/dev/null 2>&1 ) \
    && echo "  ✓ cmdb-go 已按当前配置重建" \
    || { err "cmdb-go 重建失败"; exit 1; }
  echo ""
  echo "  阶段三：逐项目重置（收编既有 reset）"
  for p in auth cloud event iam release cmdb workflow; do
    echo "==> ${p}"
    reset_project "${p}" || true
  done
fi
ok "reset 完成"
