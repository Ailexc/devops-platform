#!/usr/bin/env bash
# ============================================================
# deploy —— 一键部署核心（唯一实现；deploy-server/deploy-cloud 为薄壳）
# 用法：
#   bash scripts/deploy.sh --env server [--reset]
#   bash scripts/deploy.sh --env cloud [--reset] [--pull]
#   bash scripts/deploy.sh                # --env 缺省时读 .env-active
# 步骤：IAM 镜像构建 → bootstrap → start（含 preflight 演示数据）→ 网关 → 冒烟验证
# ============================================================
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
source scripts/lib.sh

RESET_FLAG=""; PULL=0; DEPLOY_ENV=""
while [ $# -gt 0 ]; do
  case "$1" in
    --reset) RESET_FLAG="--reset" ;;
    --pull)  PULL=1 ;;
    --env)   DEPLOY_ENV="${2:-}"; shift ;;
    *) err "未知参数 '$1'"; exit 1 ;;
  esac
  shift
done

if [ -z "$DEPLOY_ENV" ]; then
  [ -f .env-active ] && DEPLOY_ENV="$(head -1 .env-active | tr -d '[:space:]')" \
    || { err "未声明环境：先 make use E=<env> 或传 --env <env>"; exit 1; }
fi

# ---------- 0. 云上可选：拉取最新代码 ----------
if [ "$PULL" = "1" ]; then
  GIT_REPO="git@gitee.com:ailexc-code/dev-ops-platform.git"
  DEPLOY_DIR="${DEPLOY_DIR:-/opt/DevOpsPlatform}"
  if [ ! -d "$DEPLOY_DIR/.git" ]; then
    log "首次部署：clone 仓库到 $DEPLOY_DIR"
    mkdir -p "$(dirname "$DEPLOY_DIR")"
    git clone "$GIT_REPO" "$DEPLOY_DIR"
  fi
  cd "$DEPLOY_DIR"
  log "拉取最新代码（$(git log --oneline -1)）"
  git pull --rebase
  source scripts/lib.sh
fi

ENV="$DEPLOY_ENV" load_env

# ---------- 1. Docker 检查 ----------
check_docker
ok "Docker 就绪：$(docker --version)"

# ---------- 2. PermissionCenter：容器内多阶段构建 ----------
# GOARCH 按环境注入（.env.server=amd64 / .env.local=arm64），不再硬编码（规范 R1 同族）
log "构建 PermissionCenter 镜像（GOARCH=${GOARCH:-amd64}，容器内多阶段）..."
docker build -f PermissionCenter/backend/Dockerfile.build --build-arg GOARCH="${GOARCH:-amd64}" -t iam-backend PermissionCenter/backend
docker build -f PermissionCenter/frontend/Dockerfile -t iam-frontend PermissionCenter/frontend

# ---------- 3. 基础设施 + 全量启动（含 preflight 演示数据）----------
log "启动统一基础设施并创建业务库"
make bootstrap

if [ "$RESET_FLAG" = "--reset" ]; then
  log "RESET_ON_START=true：全量重置到出厂态后启动"
  RESET_ON_START=true make start
else
  log "普通启动（保留现有数据）"
  make start
fi

# ---------- 4. 统一网关 ----------
log "启动统一网关（入口 :8088）"
make gateway-up

# ---------- 5. 冒烟验证 ----------
log "等待容器稳定（15s）..."
sleep 15
bash scripts/verify.sh
