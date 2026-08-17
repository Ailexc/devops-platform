#!/usr/bin/env bash
# ============================================================
# bootstrap —— 启动统一基础设施并创建 7 个业务库
# 用法：make bootstrap  或  bash scripts/bootstrap.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

# ---- 公共库 ----
source scripts/lib.sh

# 业务库（一实例多库；devops_cmdb_go 为 TaskManager Go 后端独立库）
DBS=(devops_auth devops_cloud devops_event devops_event_go devops_iam devops_openfga devops_release devops_cmdb devops_cmdb_go devops_workflow)

log "检查 Docker 环境"
check_docker

log "启动统一基础设施（PostgreSQL + Redis）"
docker compose -f infra/docker-compose.yml up -d

log "等待基础设施就绪"
wait_container_healthy devops-postgres
wait_container_healthy devops-redis
wait_container_healthy devops-rabbitmq

log "创建业务库（已存在则跳过）"
for db in "${DBS[@]}"; do
  if docker exec devops-postgres psql -U devops -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1; then
    echo "  ✓ ${db}（已存在）"
  else
    docker exec devops-postgres createdb -U devops "${db}"
    echo "  ✓ ${db}（已创建）"
  fi
done

log "完成。统一连接（容器内）："
echo "  PostgreSQL: postgresql://devops:devops@devops-postgres:5432/devops_<项目>   （宿主调试: localhost:25432）"
echo "  Redis:      redis://devops-redis:6379/<0-6>                              （宿主调试: localhost:26379）"
