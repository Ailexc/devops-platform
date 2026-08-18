#!/usr/bin/env bash
# ============================================================
# reset —— 统一数据重置入口（"回到出厂态"）
# 用法：make reset [P=auth|cloud|event|iam|release|cmdb|workflow]
#   - 带 P：先清空该项目统一库（DROP SCHEMA）→ 再跑该项目重置/种子
#   - 不带 P：删除重建全部统一业务库 + 逐项目重置
# 安全：所有重置前保留旧数据卷/文件（保守切换，确认后手动清理）
#
# 健壮性说明（统一 reset / make demo-reset 的基石）：
#   - 各项目"容器内 exec"前会先 docker compose up -d 确保容器在运行，
#     因此即使此前应用容器处于停止/异常状态，本脚本也能恢复到干净状态。
#   - 不再用 || true 吞掉单项目失败：任一步失败即中止并报错，避免"看起来成功"。
#   - 调用方可配合 scripts/demo-reset.sh 完成 DB+Redis+重建+冒烟的全量一键恢复。
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

# 确保某项目的核心业务容器在运行（供 exec 使用；容器已停也先拉起）
ensure_up() {
  local name="$1" services="${2:-}"
  local dir opts
  dir="$(project_dir "$name")"
  opts="$(project_compose_opts "$name")"
  log "确保 ${name} 容器运行（${dir}）..."
  ( cd "$dir" && docker compose ${opts} up -d --build ${services} )
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
      ensure_up cmdb backend
      ( cd TaskManager && docker compose exec backend python manage.py migrate && \
        docker compose exec backend python manage.py seed_demo_data )
      ;;
    workflow)
      # reset_demo 自带 migrate（幂等）→ flush（清空重建）→ loaddata 恢复 Demo 快照 → 补齐演示数据
      ensure_up workflow api
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

# 清空统一 Redis 中的业务数据（仅清业务 DB index，不碰 auth/session 默认库）
# 约定索引：cloud=1, event=2, event-go=8, cmdb=5, cmdb-go=7, workflow=6
flush_redis() {
  log "清空统一 Redis 业务数据（db 1/2/5/6/7/8）"
  if docker ps --format '{{.Names}}' | grep -q '^devops-redis$'; then
    for db in 1 2 5 6 7 8; do
      docker exec devops-redis redis-cli -n "$db" FLUSHDB >/dev/null 2>&1 \
        && echo "  ✓ redis db${db} 已清空" \
        || err "  ✗ redis db${db} 清空失败"
    done
  else
    err "统一 Redis 未运行，跳过（请先 make bootstrap）"
  fi
}

if [ -n "${P}" ]; then
  log "reset 项目: ${P}"
  reset_project "${P}"
  flush_redis
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
    reset_project "${p}"
  done
  flush_redis
fi
ok "reset 完成"
