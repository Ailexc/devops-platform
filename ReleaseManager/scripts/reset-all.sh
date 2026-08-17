#!/bin/bash
# =============================================================================
# 发布系统 Demo — 一键重置脚本（删除重建）
# 无论当前数据处于什么状态，本脚本都会：
#   1. 备份当前数据库（db-data 卷）到 .db-backups/
#   2. 删除所有 release 容器 + 数据卷（db-data / shared-keys）
#   3. 重新构建镜像
#   4. 重新初始化（生成密钥 + 迁移 + 种子数据 + Demo 权限）
#   5. 启动服务并做基本验证
#
# 用法:
#   ./scripts/reset-all.sh          # 完整重置（含镜像重建，会二次确认）
#   ./scripts/reset-all.sh -y       # 跳过确认直接执行
#   ./scripts/reset-all.sh --no-build   # 不重建镜像（用现有镜像，更快）
#
# 注意:
#   - 只操作当前 compose 项目（COMPOSE_PROJECT_NAME=release-system）的数据卷，
#     不会动旧项目卷（release_system_demo_db-data）。
#   - 备份保存在 .db-backups/reset-pre-<时间戳>.sqlite3
# =============================================================================

set -euo pipefail

# ── 路径 / 颜色 ─────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 参数 ────────────────────────────────────────────────────────────────────
CONFIRM=1
BUILD=1
for arg in "$@"; do
    case "$arg" in
        -y|--yes)        CONFIRM=0 ;;
        --no-build)      BUILD=0 ;;
        -h|--help)
            sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) warn "未知参数: $arg（忽略）" ;;
    esac
done

# ── 前置检查 ────────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || { err "未找到 docker，请先安装 Docker/OrbStack"; exit 1; }

# 读取 compose 项目名（.env 中定义，默认 release-system）
PROJECT_NAME=$(grep -E '^COMPOSE_PROJECT_NAME=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')
PROJECT_NAME=${PROJECT_NAME:-release-system}
DB_VOLUME="${PROJECT_NAME}_db-data"

info "项目名: ${PROJECT_NAME}"
info "数据卷: ${DB_VOLUME}"

if ! docker volume inspect "$DB_VOLUME" >/dev/null 2>&1; then
    warn "数据卷 ${DB_VOLUME} 不存在，将全新初始化"
fi

# ── 二次确认 ─────────────────────────────────────────────────────────────────
if [ "$CONFIRM" = "1" ]; then
    echo ""
    warn "本操作将【删除】当前 release 全部容器与数据卷（db-data/shared-keys）并重建！"
    read -r -p "确认继续？输入 yes 继续，其他任意键取消: " ans
    if [ "$ans" != "yes" ]; then
        info "已取消。"
        exit 0
    fi
fi

# ── 1. 备份当前数据库 ───────────────────────────────────────────────────────
mkdir -p .db-backups
if docker volume inspect "$DB_VOLUME" >/dev/null 2>&1; then
    TS=$(date +%Y%m%d-%H%M%S)
    BAK=".db-backups/reset-pre-${TS}.sqlite3"
    info "备份当前数据库 → ${BAK}"
    docker run --rm -v "${DB_VOLUME}":/data -v "$ROOT_DIR/.db-backups":/backup \
        alpine sh -c 'cp /data/db.sqlite3 /backup/'"reset-pre-${TS}"'.sqlite3 2>/dev/null || true' \
        || warn "备份失败（可能卷为空），继续..."
    [ -f "$BAK" ] && ok "备份完成: $BAK" || warn "无数据库可备份"
else
    warn "数据卷不存在，跳过备份"
fi

# ── 2. 停止并删除容器 + 数据卷 ──────────────────────────────────────────────
info "停止并删除 release 容器与数据卷..."
docker compose down -v --remove-orphans
ok "已删除容器与数据卷"

# ── 3. 重建镜像 ─────────────────────────────────────────────────────────────
if [ "$BUILD" = "1" ]; then
    info "重新构建镜像（backend/frontend/executor/init）..."
    # --profile init：确保 init 容器（统一 PG 种子）也用最新代码重建
    docker compose --profile init build
    ok "镜像构建完成"
else
    warn "--no-build：使用现有镜像，跳过构建"
fi

# ── 4. 初始化（生成密钥 + 迁移 + 种子数据 + Demo 权限）────────────────────
info "运行初始化容器（密钥 / migrate / init_seed）..."
docker compose --profile init run --rm init
ok "初始化完成"

# ── 5. 启动服务 ─────────────────────────────────────────────────────────────
info "启动全部服务..."
docker compose up -d
ok "服务已启动"

# ── 6. 等待后端就绪 ─────────────────────────────────────────────────────────
info "等待后端就绪..."
for i in $(seq 1 30); do
    if curl -sk -o /dev/null -w '%{http_code}' \
        "https://frontend.${PROJECT_NAME}.orb.local/api/v1/releases/" 2>/dev/null | grep -qE '401|200'; then
        ok "后端已就绪（${i}s）"
        break
    fi
    if [ "$i" = "30" ]; then
        err "后端 30s 内未就绪，请检查: docker compose ps / docker logs release-backend"
        exit 1
    fi
    sleep 1
done

# ── 7. 验证 Demo 应用权限 ───────────────────────────────────────────────────
info "验证 Demo 应用对张三/李四的可见性..."
docker exec release-backend python manage.py shell -c "
from apps.accounts.models import User
from apps.applications.models import Application
from apps.authz.utils import get_user_accessible_app_ids

demo_ids = list(Application.objects.filter(
    code__in=['go-app', 'node-app', 'python-app']
).values_list('id', flat=True))
demo_ids.sort()
print('Demo 应用 ids:', demo_ids)
for uname in ['zhangsan', 'lisi']:
    u = User.objects.get(username=uname)
    ids = get_user_accessible_app_ids(u)
    demo = sorted(set(ids) & set(demo_ids))
    print(f'{uname}: 可见应用 {ids} | Demo应用可见 {demo}')
    assert demo == demo_ids, f'{uname} 看不到全部 Demo 应用!'
print('OK: 张三/李四均可看到 3 个 Demo 应用')
" 2>&1 | tail -6

echo ""
ok "🎉 一键重置完成！"
echo "  前端: https://frontend.${PROJECT_NAME}.orb.local"
echo "  API : https://api.${PROJECT_NAME}.orb.local"
echo "  登录账号: zhangsan / lisi（Demo 账号，无密码）"
