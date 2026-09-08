#!/bin/bash
# =============================================================================
# 发布系统 Demo — 启动脚本（本地开发模式）
# 启动 Executor(8765) + Django 后端(8000) + Vite 前端(5173)
# 首次使用请先运行 init.sh
# =============================================================================
# 提示：如需使用 Docker 部署（OrbStack 原生路由），请使用 docker-compose.yml
#       域名：frontend.release-system.orb.local / api.release-system.orb.local / executor.release-system.orb.local
#       参考：docker compose up -d          （启动服务）
#             docker compose --profile init run init  （首次初始化）
# =============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
EXECUTOR_DIR="$ROOT_DIR/executor"
VENV_DIR="$ROOT_DIR/.venv"

# ── 颜色 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 清理函数 ──────────────────────────────────────────────────────────────
cleanup() {
    info "正在停止服务..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && ok "后端已停止"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && ok "前端已停止"
    [ -n "$EXECUTOR_PID" ] && kill "$EXECUTOR_PID" 2>/dev/null && ok "执行端已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# ── 检查环境 ──────────────────────────────────────────────────────────────
info "检查运行环境..."

PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    err "未找到 Python，请先安装 Python 3.9+"
    exit 1
fi

NODE=$(command -v node)
if [ -z "$NODE" ]; then
    err "未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

ok "Python: $($PYTHON --version)"
ok "Node:   $($NODE --version)"

# ── Python 虚拟环境 ───────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    warn "虚拟环境不存在，正在创建..."
    $PYTHON -m venv "$VENV_DIR"
    ok "虚拟环境已创建"
fi

source "$VENV_DIR/bin/activate"

# 激活后重新解析解释器，确保后续 $PYTHON 都指向 venv（避免误用系统 Python）
PYTHON="$(command -v python)"

# ── 安装依赖 ──────────────────────────────────────────────────────────────
if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    err "未找到 backend/requirements.txt"
    exit 1
fi

info "检查 Python 依赖..."
pip install -r "$BACKEND_DIR/requirements.txt" -q 2>/dev/null
pip install -r "$EXECUTOR_DIR/requirements.txt" -q 2>/dev/null
ok "Python 依赖已就绪"

# ── 服务间认证密钥（backend ↔ executor）────────────────────────────────
info "检查服务间认证密钥..."
$PYTHON "$ROOT_DIR/scripts/gen_executor_keys.py"
ok "服务间认证密钥已就绪"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    info "安装前端依赖（首次启动较慢）..."
    cd "$FRONTEND_DIR"
    npm install
    cd "$ROOT_DIR"
fi
ok "Node 依赖已就绪"

# ── 检查是否已初始化 ────────────────────────────────────────────────────
if [ ! -f "$ROOT_DIR/.initialized" ]; then
    warn "系统未初始化，请先运行: ./init.sh"
    info "继续启动（可能缺少种子数据）..."
fi

# ── 启动 Executor ────────────────────────────────────────────────────────
OLD_EX_PIDS=$(lsof -ti:8765 2>/dev/null || true)
if [ -n "$OLD_EX_PIDS" ]; then
    warn "端口 8765 已被占用 (PID: $OLD_EX_PIDS)，正在清理..."
    echo "$OLD_EX_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
    ok "端口 8765 已释放"
fi

info "启动 executor 执行端 (port 8765)..."
cd "$EXECUTOR_DIR"
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8765 &
EXECUTOR_PID=$!
cd "$ROOT_DIR"

# 等待 executor 启动（最多10秒）
for i in $(seq 1 10); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/api/v1/cluster/health 2>/dev/null | grep -q '200'; then
        break
    fi
    sleep 1
done

if kill -0 "$EXECUTOR_PID" 2>/dev/null; then
    ok "executor 已启动 (PID: $EXECUTOR_PID)"
else
    err "executor 启动失败，请检查端口 8765 是否被占用"
    exit 1
fi

# ── 启动后端 ──────────────────────────────────────────────────────────────
# 先清理已有进程（可能有多个）
OLD_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
    warn "端口 8000 已被占用 (PID: $OLD_PIDS)，正在清理..."
    echo "$OLD_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
    ok "端口 8000 已释放"
fi

info "启动 Django 后端 (port 8000)..."
cd "$BACKEND_DIR"
$PYTHON manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd "$ROOT_DIR"

# 等待后端启动（最多10秒）
for i in $(seq 1 10); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users/ 2>/dev/null | grep -q '200'; then
        break
    fi
    sleep 1
done

if kill -0 "$BACKEND_PID" 2>/dev/null; then
    ok "后端已启动 (PID: $BACKEND_PID)"
else
    err "后端启动失败，请检查端口 8000 是否被占用"
    exit 1
fi

# ── 启动前端 ──────────────────────────────────────────────────────────────
OLD_FE_PIDS=$(lsof -ti:5173 2>/dev/null || true)
if [ -n "$OLD_FE_PIDS" ]; then
    warn "端口 5173 已被占用 (PID: $OLD_FE_PIDS)，正在清理..."
    echo "$OLD_FE_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

info "启动 Vite 前端 (port 5173)..."
cd "$FRONTEND_DIR"
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
cd "$ROOT_DIR"

# 等待前端启动（最多15秒）
for i in $(seq 1 15); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null | grep -q '200'; then
        break
    fi
    sleep 1
done

if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    ok "前端已启动 (PID: $FRONTEND_PID)"
else
    err "前端启动失败，请检查端口 5173 是否被占用"
    exit 1
fi

# ── 完成 ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  发布系统 Demo 已启动${NC}"
echo -e "${GREEN}  ───────────────────────────────────────────${NC}"
echo -e "${GREEN}  前端:    http://localhost:5173${NC}"
echo -e "${GREEN}  后端:    http://localhost:8000${NC}"
echo -e "${GREEN}  执行端:  http://localhost:8765/docs${NC}"
echo -e "${GREEN}  退出:    按 Ctrl+C${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""

# 等待子进程
wait
