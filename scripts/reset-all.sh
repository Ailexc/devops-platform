#!/usr/bin/env bash
# ============================================================
# reset —— 统一数据重置入口（"回到出厂态"）
# 用法：make reset [P=auth|cloud|event|iam|release|cmdb|workflow]
#   - 带 P：先清空该项目统一库（DROP SCHEMA）→ 调用该项目重置契约
#   - 不带 P：删除重建全部统一业务库 + 逐项目重置契约
#   - NO_BUILD=1（make reset 默认）：复用现有镜像；NO_BUILD=0：重建镜像
#
# 架构（契约制，docs/DevOps流程标准化梳理与改进方案.md §8.1）：
#   - 顶层只负责：爆破数据层（阶段一）→ sidecar 迁移（阶段二）→ 调用契约（阶段三）
#   - 每项目"怎么重置"由契约 <Project>/scripts/reset.sh 自治（幂等/自包含/自验证）
#   - 新增项目 = 实现一个契约文件，本脚本零改动
#
# 健壮性（实战踩坑记录，勿删）：
#   - 各项目"容器内 exec"前先 ensure_up 确保容器运行
#   - 不用 || true 吞失败：任一契约失败即中止，避免"看起来成功"
#   - schema 清空后禁止重复 exec migrate/seed（pg_type 唯一约束竞态）→ 契约内统一走容器重建
#   - 无 TTY 环境（nohup/管道）compose run 必须 -T 且 stdin </dev/null（防 SIGTTIN 挂起）
#   - Django runserver stdout 块缓冲 → 就绪判定用 HTTP 探活（wait_http_ready）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
load_env

P="${1:-}"
DBS=(devops_auth devops_cloud devops_event devops_event_go devops_iam devops_openfga devops_release devops_cmdb devops_cmdb_go devops_workflow)
PROJECTS=(auth cloud event iam release cmdb workflow)

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

# 清空统一 Redis 中的业务数据（仅清业务 DB index，不碰默认库）
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

# 调用项目重置契约（唯一的项目级入口，实现细节项目自治）
run_contract() {
  local p="$1" dir
  dir="$(project_dir "$p")"
  [ -f "$dir/scripts/reset.sh" ] || { err "缺少重置契约：$dir/scripts/reset.sh"; exit 1; }
  log "执行重置契约：$dir/scripts/reset.sh"
  ( cd "$dir" && NO_BUILD="${NO_BUILD:-1}" bash scripts/reset.sh )
}

if [ -n "${P}" ]; then
  require_project "${P}"
  log "reset 项目: ${P}"
  db="$(project_db "${P}")"
  [ -n "${db}" ] && drop_schema "${db}"
  run_contract "${P}"
  flush_redis
else
  log "全量 reset"
  echo "  阶段一：重置统一数据库（数据层出厂态）"
  reset_infra_db
  echo ""
  echo "  阶段二：重建 sidecar 迁移（openfga / cmdb-go）"
  # OpenFGA：distroless 镜像需单独 migrate（幂等），须先于 iam 种子（建 store）
  # docker compose run 无 TTY 必须 -T 且 stdin </dev/null（防 SIGTTIN 挂起）
  ( cd PermissionCenter && docker compose -f deploy/docker-compose.yml run -T --rm openfga migrate < /dev/null > /tmp/reset-sidecar.log 2>&1 ) \
    && echo "  ✓ openfga migrate 完成" \
    || { err "openfga migrate 失败（详见 /tmp/reset-sidecar.log）"; exit 1; }
  # cmdb-go：旧容器用旧 hostname，需按当前 compose 重建（--seed 自动迁移+播种）
  ( cd TaskManager && docker compose up -d --force-recreate go_backend >> /tmp/reset-sidecar.log 2>&1 ) \
    && echo "  ✓ cmdb-go 已按当前配置重建" \
    || { err "cmdb-go 重建失败（详见 /tmp/reset-sidecar.log）"; exit 1; }
  echo ""
  echo "  阶段三：逐项目重置（重置契约 <Project>/scripts/reset.sh）"
  for p in "${PROJECTS[@]}"; do
    echo "==> ${p}"
    run_contract "${p}"
  done
  flush_redis
fi
ok "reset 完成"
