#!/usr/bin/env bash
# ============================================================
# deploy-server —— 本地/自建服务器一键部署 / 更新
# 用法：
#   bash scripts/deploy-server.sh            # 部署 / 更新（保留数据）
#   bash scripts/deploy-server.sh --reset    # 全量重置到出厂态后启动
#
# 与 deploy-cloud.sh 的差异（其余逻辑完全一致）：
#   - 不 clone 仓库：直接在当前仓库目录执行
#   - ENV=server：加载 deploy/server/.env.server（自建服务器变量）
#   - 无云 IP 打印：验证走 localhost:8088 + .env.server 的 SERVER_IP
#
# 前置条件：
#   - Docker + Compose 已安装
#   - deploy/server/.env.server 已配置（SERVER_IP 等）
# ============================================================
set -euo pipefail

RESET_FLAG="${1:-}"

log()  { echo -e "\033[1;36m[deploy-server]\033[0m $*"; }
err()  { echo -e "\033[1;31m[deploy-server:错误]\033[0m $*" >&2; }
ok()   { echo -e "\033[1;32m[deploy-server]\033[0m $*"; }

# 定位仓库根（脚本必须从仓库根执行，与 make 系列保持一致）
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
log "部署目录：${REPO_ROOT}"

# ---------- 加载公共库 ----------
source scripts/lib.sh
log()  { echo -e "\033[1;36m[deploy-server]\033[0m $*"; }
err()  { echo -e "\033[1;31m[deploy-server:错误]\033[0m $*" >&2; }
ok()   { echo -e "\033[1;32m[deploy-server]\033[0m $*"; }

# ---------- 1. 加载服务器环境变量（ENV=server 强制）----------
ENV=server load_env

# ---------- 2. 检查 Docker ----------
if ! docker info >/dev/null 2>&1; then err "Docker 未运行"; exit 1; fi
ok "Docker 就绪：$(docker --version)"

# ---------- 3. PermissionCenter：容器内构建（服务器无 Go/Node 工具链）----------
# 后端：Dockerfile.build 多阶段编译（GOARCH=amd64，x86_64 服务器）
# 前端：Dockerfile 容器内 npm 构建 → nginx
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

# ---------- 5.5 PermissionCenter 数据初始化 ----------
# iam-server 启动只 EnsureSchema（建表），不写用户/应用/授权模型；
# 若不 seed，SSO 网关注入的用户在本地无账号 → 授权 401（曾踩坑）
log "初始化 PermissionCenter 数据（iam-server seed：用户/应用/授权模型）..."
docker compose -f PermissionCenter/deploy/docker-compose.yml run --rm iam-server iam-server seed

# ---------- 6. 统一网关（8088）----------
log "启动统一网关（入口 :8088）"
make gateway-up

# ---------- 7. 验证 ----------
log "等待容器稳定（15s）..."
sleep 15

SERVER_IP="${SERVER_IP:-localhost}"

echo ""
echo "==================== 部署验证 ===================="
echo "── 容器状态 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops|auth|cloud|event|iam|release|cmdb|task|workflow|traefik|gateway' | sort
echo ""
echo "── 统一基础设施健康 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops-postgres|devops-redis|devops-rabbitmq' | grep healthy || echo "（部分基础设施未 healthy）"
echo ""
echo "── 门户 + 7 系统（纯 IP 多端口直测，免 hosts 映射）──"
# 网关按 Host(<SERVER_IP>) 匹配路由 → 用 Host 头 + localhost 即可在本机完成直测
check_port() {
  local name="$1" port="$2"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: ${SERVER_IP}" "http://localhost:${port}/" 2>/dev/null || echo ERR)
  printf "  %-6s  %-18s HTTP %s\n" "${SERVER_IP}:${port}" "${name}" "${code}"
}
check_port "8088 门户 Portal"        8088
check_port "8089 任务 TaskManager"   8089
check_port "8090 多云 CloudManager"  8090
check_port "8091 流程 WorkFlowCenter" 8091
check_port "8092 事件 EventManager"  8092
check_port "8093 发布 ReleaseManager" 8093
check_port "8094 权限 PermissionCenter" 8094
echo ""
echo "=================================================="
ok "部署完成！门户：http://${SERVER_IP}:8088"
ok "各系统多端口直连：8089 任务 / 8090 多云 / 8091 流程 / 8092 事件 / 8093 发布 / 8094 权限"
