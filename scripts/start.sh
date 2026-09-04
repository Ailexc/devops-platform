#!/usr/bin/env bash
# ============================================================
# start —— 统一启动入口（Phase 2：统一 start 与 RESET_ON_START 语义）
# 用法：
#   make start                    # 启动全部 7 个项目（infra 缺失则先 bootstrap）
#   make start P=auth             # 只启动 Authentication
#   RESET_ON_START=true make start P=auth   # 先重置该项目（出厂态）再启动
#   RESET_ON_START=true make start          # 先全量重置再启动全部
#
# 语义：
#   - 普通启动 = 幂等启动（restart: unless-stopped 的服务直接 up）
#   - RESET_ON_START=true|1|yes|on → 启动前先走统一 reset
#     （drop schema → migrate → 幂等种子，数据回到出厂态）
#   - 统一处理各项目 compose 文件差异（cloud/iam）
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
# 加载部署环境变量（ENV=local|cloud 自动检测；云端 /opt/DevOpsPlatform → cloud）
load_env

P="${1:-}"
RESET_ON_START="${RESET_ON_START:-false}"

is_reset() {
  case "$RESET_ON_START" in
    true|TRUE|1|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

# ---- 1. 确保统一基础设施就绪（幂等）----
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^devops-postgres$'; then
  ok "统一基础设施已就绪（devops-postgres / devops-redis）"
else
  log "统一基础设施未启动，先执行 bootstrap"
  bash scripts/bootstrap.sh
fi

# ---- 2. 可选：RESET_ON_START=true → 先重置（回到出厂态）----
if is_reset; then
  log "RESET_ON_START=true：先重置数据（回到出厂态）"
  if [ -n "${P}" ]; then
    bash scripts/reset-all.sh "${P}"
  else
    bash scripts/reset-all.sh
  fi
else
  ok "RESET_ON_START 未开启 → 普通启动（保留现有数据）"
fi

# ---- 3. 启动 ----
start_one() {
  local name="$1" dir opts
  dir="$(project_dir "$name")"
  opts="$(project_compose_opts "$name")"
  echo "==> start ${name} (${dir})"
  ( cd "$dir" && docker compose ${opts} up -d --build )
}

if [ -n "${P}" ]; then
  require_project "${P}"
  start_one "${P}"
  log "已启动: ${P}"
else
  for p in auth cloud event iam release cmdb workflow; do
    start_one "${p}" || true
  done
  log "全部项目已启动"
fi

# 就绪提示按环境区分：本地 OrbStack 用 orb.local 域名；服务器用 SERVER_IP:8088
if [ "${ENV:-}" = "server" ] || [ "${ENV:-}" = "cloud" ]; then
  log "启动完成。统一门户: ${PORTAL_URL:-http://${SERVER_IP:-localhost}:8088}"
else
  log "启动完成。统一门户: http://portal.authentication.orb.local"
fi
