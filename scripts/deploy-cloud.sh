#!/usr/bin/env bash
# ============================================================
# deploy-cloud —— 阿里云 ECS 一键部署 / 更新（Phase 4）
# 用法：
#   bash scripts/deploy-cloud.sh            # 部署 / 更新（保留数据）
#   bash scripts/deploy-cloud.sh --reset    # 全量重置到出厂态后启动
#
# 前置条件（已在 ECS 准备）：
#   - SSH + Gitee 密钥（id_ed25519_gitee）已认证
#   - Docker + Compose 已安装；镜像加速已配置
#   - 安全组放行 8088
#
# 说明：
#   - PermissionCenter 为宿主预编译二进制 → 必须在 ECS(x86_64) 上用 GOARCH=amd64 重编
#   - 其余 6 项目均为容器内多阶段构建（ECS 自动按 amd64 编译）
#   - 统一网关暴露 8088（本地一致），Host 头路由 + IP 兜底直达门户
# ============================================================
set -euo pipefail

# ---------- 配置 ----------
GIT_REPO="git@gitee.com:ailexc-code/dev-ops-platform.git"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/DevOpsPlatform}"
RESET_FLAG="${1:-}"

log()  { echo -e "\033[1;36m[deploy-cloud]\033[0m $*"; }
err()  { echo -e "\033[1;31m[deploy-cloud:错误]\033[0m $*" >&2; }
ok()   { echo -e "\033[1;32m[deploy-cloud]\033[0m $*"; }

# ---------- 0. 确保仓库就绪（首次 clone / 之后 pull）----------
if [ ! -d "$DEPLOY_DIR/.git" ]; then
  log "首次部署：clone 仓库到 $DEPLOY_DIR"
  mkdir -p "$(dirname "$DEPLOY_DIR")"
  git clone "$GIT_REPO" "$DEPLOY_DIR"
fi
cd "$DEPLOY_DIR"
log "拉取最新代码（$(git log --oneline -1)）"
git pull --rebase

# ---------- 加载公共库（load_env 等），保持本脚本 [deploy-cloud] 前缀 ----------
source scripts/lib.sh
log()  { echo -e "\033[1;36m[deploy-cloud]\033[0m $*"; }
err()  { echo -e "\033[1;31m[deploy-cloud:错误]\033[0m $*" >&2; }
ok()   { echo -e "\033[1;32m[deploy-cloud]\033[0m $*"; }

# ---------- 1. 加载云端环境变量（统一入口，ENV=cloud 强制）----------
ENV=cloud load_env

# ---------- 2. 检查 Docker ----------
if ! docker info >/dev/null 2>&1; then err "Docker 未运行"; exit 1; fi
ok "Docker 就绪：$(docker --version)"

# ---------- 3. PermissionCenter：容器内构建（ECS 无 Go/Node 工具链）----------
# 后端：Dockerfile.build 多阶段编译（GOARCH=amd64，x86_64 ECS）
# 前端：Dockerfile 容器内 npm 构建 → nginx（已改造，与 CloudManager 一致）
log "构建 PermissionCenter 镜像（GOARCH=amd64，容器内多阶段）..."
docker build -f PermissionCenter/backend/Dockerfile.build --build-arg GOARCH=amd64 -t iam-backend PermissionCenter/backend
docker build -f PermissionCenter/frontend/Dockerfile -t iam-frontend PermissionCenter/frontend

# ---------- 4. 统一基础设施（PG + Redis + RabbitMQ + 建库）----------
log "启动统一基础设施并创建业务库"
make bootstrap

# ---------- 5. 全量启动（含各项目镜像构建）----------
if [ "$RESET_FLAG" = "--reset" ]; then
  log "RESET_ON_START=true：全量重置到出厂态后启动"
  RESET_ON_START=true make start
else
  log "普通启动（保留现有数据）"
  make start
fi

# ---------- 6. 统一网关（8088）----------
log "启动统一网关（入口 :8088）"
make gateway-up

# ---------- 7. 验证 ----------
log "等待容器稳定（15s）..."
sleep 15

echo ""
echo "==================== 部署验证 ===================="
echo "── 容器状态 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops|auth|cloud|event|iam|release|cmdb|task|workflow|traefik|gateway' | sort
echo ""
echo "── 统一基础设施健康 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops-postgres|devops-redis|devops-rabbitmq' | grep healthy || echo "（部分基础设施未 healthy）"
echo ""
echo "── 门户 + 7 系统（Host 头直测）──"
BASE="http://localhost:8088"
for h in devops portal cloud event iam release cmdb workflow api.auth; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: ${h}.devops.orb.local" "$BASE/" 2>/dev/null || echo ERR)
  echo "  ${h}.devops.orb.local  →  ${code}"
done
echo ""
echo "── IP 直达门户 ──"
echo "  http://114.55.244.220:8088 → $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8088/ 2>/dev/null || echo ERR)"
echo ""
echo "=================================================="
ok "部署完成！公网访问：http://114.55.244.220:8088（各系统见 docs/commands.md Host 头映射）"
