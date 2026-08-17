#!/bin/bash
# =============================================================================
# 发布系统 Demo — 初始化脚本（本地开发模式）
# 仅在首次设置或数据库重建后执行：迁移 + 种子数据 + demo 应用权限
# 后续启动请使用 dev.sh
# =============================================================================
# 提示：如需使用 Docker + Traefik 网关部署，请使用 docker-compose.yml
#       参考：docker compose --profile init run init  （首次初始化）
#             docker compose up -d                     （启动服务）
# =============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$ROOT_DIR/.venv"

# ── 颜色 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Python 虚拟环境 ───────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    warn "虚拟环境不存在，正在创建..."
    python3 -m venv "$VENV_DIR"
    ok "虚拟环境已创建"
fi
source "$VENV_DIR/bin/activate"
PYTHON="$(command -v python)"

# ── 数据库迁移 ────────────────────────────────────────────────────────────
info "执行数据库迁移..."
cd "$BACKEND_DIR"
$PYTHON manage.py migrate --run-syncdb 2>/dev/null
ok "数据库迁移完成"

# ── 种子数据 ──────────────────────────────────────────────────────────────
info "初始化种子数据..."
$PYTHON manage.py init_seed 2>/dev/null
ok "种子数据初始化完成"

# ── Demo 应用权限 ─────────────────────────────────────────────────────────
# 说明：Demo 应用（go-app/node-app/python-app）权限已由 init_seed 的
#   _ensure_demo_app_permissions() 兜底处理：归属 payment-dev 组（own_group），
#   组内成员张三/李四均可见。
# 历史遗留：旧的「硬编码张三个人规则 + 删除 demo 全部规则」方案，会让李四
#   （demo 应用负责人）看不到应用，造成权限错位，已移除，避免与组规则冲突。
info "Demo 应用权限已由 init_seed 兜底（payment-dev 组，张三/李四可见）"
ok "初始化完成!"

# 创建初始化标记文件
touch "$ROOT_DIR/.initialized"
ok "已创建 .initialized 标记"

echo ""
echo -e "${GREEN}可以使用 dev.sh 启动服务了${NC}"
