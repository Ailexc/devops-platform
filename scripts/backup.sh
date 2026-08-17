#!/usr/bin/env bash
# ============================================================
# backup —— 统一数据备份（切换统一 PostgreSQL 前的保守安全网）
# 用法：make backup  或  bash scripts/backup.sh
# 输出：backups/<时间戳>/  （SQLite 原样复制 + PG pg_dump + MySQL mysqldump）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

TS=$(date +%Y%m%d-%H%M%S)
DIR="backups/${TS}"
mkdir -p "${DIR}"
log "备份目录：${DIR}"

# ---- 1) SQLite / 本地文件备份（若存在） ----
SQLITE_FILES=(
  "Authentication/data/auth.db"
  "Authentication/backend/auth.db"
  "ReleaseManager/backend/db.sqlite3"
  "WorkFlowCenter/backend/db.sqlite3"
  "TaskManager/backend/db.sqlite3"
)
for f in "${SQLITE_FILES[@]}"; do
  if [ -f "$f" ]; then
    mkdir -p "${DIR}/$(dirname "$f")"
    cp -p "$f" "${DIR}/$f"
    ok "备份 ${f}"
  fi
done

# ---- 2) PostgreSQL 逻辑备份（各项目自带 PG 容器，若在运行） ----
pg_dump_project() {
  local container="$1" user="$2" db="$3" name="$4"
  if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
    mkdir -p "${DIR}/pg"
    if docker exec "$container" pg_dump -U "$user" -d "$db" > "${DIR}/pg/${name}.sql" 2>/dev/null; then
      ok "备份 pg:${name} -> backups/${TS}/pg/${name}.sql"
    else
      err "pg:${name} 备份失败（请手动确认）"
    fi
  fi
}
pg_dump_project cmdb-task-postgres  cmdb      cmdb      cmdb_task
pg_dump_project cmdb-event-postgres eventuser eventdb   event
pg_dump_project iam-postgres        iam       iam       iam

# ---- 3) MySQL 逻辑备份 ----
if docker ps --format '{{.Names}}' | grep -q '^cloud_manager_mysql$'; then
  mkdir -p "${DIR}/mysql"
  if docker exec cloud_manager_mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" cloud_manager' > "${DIR}/mysql/cloud_manager.sql" 2>/dev/null; then
    ok "备份 mysql:cloud_manager"
  else
    err "mysql 备份失败（可稍后手动补）"
  fi
fi

log "备份完成，清单："
find "${DIR}" -type f | sed 's/^/  /'
