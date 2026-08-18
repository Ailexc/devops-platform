#!/usr/bin/env bash
# ============================================================
# demo-reset —— 一键恢复到干净出厂态（演示专用）
# 用法：make demo-reset          # 快速恢复（默认，复用现有镜像，只重建数据）
#       make demo-reset BUILD=1  # 完整模式（先构建最新镜像再恢复，代码变更时用）
#
# 目标：不论业务数据被如何破坏（删除/篡改/清空/异常），
#       一条命令即可把整站恢复到"出厂演示态"，保证随时可演示。
#
# 原理（硬恢复，不依赖备份）：
#   - 数据层从代码重建：DROP DATABASE 重建全部统一业务库 → 逐项目 migrate/seed
#   - Redis 业务数据清空（asynq 队列 / 缓存 / 任务状态）
#   - 应用容器复用现有镜像重启（基建/镜像本身不会被业务数据破坏，无需重建）
#   - 冒烟测试验证各系统 HTTP 可达
#
# 为什么默认不 build：
#   业务数据再脏也只会污染"数据"，不会污染"镜像/基础设施"。恢复数据只需
#   重建 DB + 清 Redis + 重启容器，无需重新编译镜像（节省 90%+ 时间）。
#   仅当代码变更、需要部署新代码时才需 BUILD=1 先构建镜像。
#
# 流程：
#   1. 确保统一基础设施运行（bootstrap 幂等）
#   2. [BUILD=1 时] 构建全部业务镜像（确保最新代码）
#   3. 全量硬重置（scripts/reset-all.sh：DB 重建 + 逐项目种子 + Redis 清空）
#   4. 启动全部应用（含演示 app / 认证 API / 统一网关）
#   5. 冒烟测试（门户 + 各系统 + 演示 app HTTP 可达）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

BUILD="${BUILD:-0}"
log "══════════════════════════════════════════════════════"
log "  make demo-reset —— 一键恢复到干净出厂态"
if [ "${BUILD}" = "1" ]; then
  log "  模式：完整（BUILD=1，先构建最新镜像再恢复）"
else
  log "  模式：快速（默认，复用现有镜像只重建数据；需构建请 BUILD=1）"
fi
log "══════════════════════════════════════════════════════"

check_docker

# ── 1. 确保统一基础设施运行（幂等）────────────────────────
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^devops-postgres$'; then
  ok "统一基础设施已就绪（devops-postgres / devops-redis / devops-rabbitmq）"
else
  log "统一基础设施未启动，执行 bootstrap ..."
  bash scripts/bootstrap.sh
fi

# ── 2. [可选] 构建全部业务镜像 ────────────────────────────
if [ "${BUILD}" = "1" ]; then
  log "构建全部业务镜像（BUILD=1）..."
  bash scripts/compose.sh build
  # 认证项目（含演示 mock/direct/pilot/oidc + 认证 API）由 Authentication/reset.sh 构建启动
  # 统一网关单独构建（聚合 7 系统 + 演示 app + 认证 API 到 8088-8099）
  log "构建统一网关镜像 ..."
  docker compose -f infra/gateway/docker-compose.yml build
else
  ok "跳过镜像构建（快速模式；BUILD=1 可强制重新构建）"
fi

# ── 3. 全量硬重置（DB 重建 + 逐项目种子 + Redis 清空）─────
log "全量硬重置数据库并逐项目回种数据 ..."
# 快速模式（默认）：透传 NO_BUILD=1，reset 链路内各 up 不再触发 build
if [ "${BUILD}" = "1" ]; then
  bash scripts/reset-all.sh
else
  NO_BUILD=1 bash scripts/reset-all.sh
fi
# 说明：reset-all.sh 阶段三 auth 分支已调用 Authentication/reset.sh
#   （内含 drop schema + 种子 + 认证/门户/演示 app/认证 API 的 up --build），
#   故认证相关服务无需在此重复构建/启动。

# ── 4. 启动全部业务应用 ──────────────────────────────────
log "启动全部业务应用 ..."
if [ "${BUILD}" = "1" ]; then
  bash scripts/compose.sh up
  # 启动统一网关（Traefik，聚合 7 系统 + 演示 app + 认证 API）
  log "启动统一网关 ..."
  docker compose -f infra/gateway/docker-compose.yml up -d --build
else
  NO_BUILD=1 bash scripts/compose.sh up
  # 启动统一网关（复用现有镜像）
  log "启动统一网关 ..."
  docker compose -f infra/gateway/docker-compose.yml up -d
fi

# ── 5. 冒烟测试 ──────────────────────────────────────────
log "冒烟测试：验证各系统 HTTP 可达 ..."

# 等待统一网关就绪（端口可连，避免 up 后立即探测返回 000）
HOST_HEADER="${DEMO_RESET_HOST:-112.124.69.224}"
GATEWAY_PORT="${DEMO_RESET_GATEWAY_PORT:-8088}"
log "等待网关（${GATEWAY_PORT}）就绪 ..."
GATEWAY_OK=0
for _ in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 -H "Host: ${HOST_HEADER}" "http://127.0.0.1:${GATEWAY_PORT}/" 2>/dev/null || echo 000)
  if [ "$code" != "000" ]; then GATEWAY_OK=1; break; fi
  sleep 1
done
if [ "$GATEWAY_OK" = "1" ]; then
  ok "  网关已就绪（HTTP ${code}）"
else
  err "  网关 30s 内未就绪，继续尝试（可能失败）"
fi

FAIL=0
check_http() {
  local name="$1" url="$2" code
  # 路由规则为 Host(112.124.69.224)，须显式带 Host 头（ECS 用公网 IP 访问时天然匹配，本地 loopback 需带上）
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -H "Host: ${HOST_HEADER}" "$url" || echo 000)
  if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ] || [ "$code" = "303" ] || [ "$code" = "401" ] || [ "$code" = "403" ]; then
    ok "  ✓ ${name} -> HTTP ${code}"
  else
    err "  ✗ ${name} -> HTTP ${code}"
    FAIL=1
  fi
}

# 基础 URL：本地走 loopback（同 ECS，避免 NAT loopback 000 问题）
BASE="${DEMO_RESET_BASE:-http://127.0.0.1}"
check_http "门户 portal        " "${BASE}:8088/"
check_http "任务管理 cmdb      " "${BASE}:8089/"
check_http "多云管理 cloud     " "${BASE}:8090/"
check_http "流程中心 workflow  " "${BASE}:8091/"
check_http "事件管理 event     " "${BASE}:8092/"
check_http "发布管理 release   " "${BASE}:8093/"
check_http "权限中心 iam       " "${BASE}:8094/"
check_http "演示 mock-app      " "${BASE}:8095/"
check_http "演示 direct-app    " "${BASE}:8096/"
check_http "演示 pilot-app     " "${BASE}:8097/"
check_http "演示 oidc-demo     " "${BASE}:8098/"
check_http "认证 API           " "${BASE}:8099/api/system/health"

echo ""
if [ "$FAIL" = "0" ]; then
  ok "✅ 一键恢复完成！全部系统已回到干净出厂态并可达。"
  log "   统一门户: ${BASE}:8088/"
  log "   端口说明: docs/端口分配.md"
else
  err "❌ 一键恢复完成，但部分系统冒烟未通过，请查看上方 ✗ 项。"
  exit 1
fi
