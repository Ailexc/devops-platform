#!/bin/bash
# ==============================================================
#  Cloud Manager - 一键重置 / 初始化数据库脚本
#
#  功能：清空(或备份)现有数据库 → 迁移 → 全链路种子数据 →
#        生成成本优化报告与建议，真正"一键恢复到可演示状态"。
#
#  用法：
#    ./reset_db.sh                 # 重置 SQLite 主库 + Mock 库 + 全部种子数据 + 优化报告
#    ./reset_db.sh --yes           # 跳过交互确认
#    ./reset_db.sh --no-backup     # 不备份旧库（默认自动备份到 backend/backups/）
#    ./reset_db.sh --skip-report   # 不生成成本优化报告（少跑最后一步）
#    ./reset_db.sh --help          # 查看帮助
# ==============================================================
set -e

# ---- 定位项目根目录 / backend 目录 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# ---- 解析参数 ----
CONFIRM_YES=0
DO_BACKUP=1
DO_REPORT=1
for arg in "$@"; do
  case "$arg" in
    --yes|-y)        CONFIRM_YES=1 ;;
    --no-backup)     DO_BACKUP=0 ;;
    --skip-report)   DO_REPORT=0 ;;
    -h|--help)
      echo "用法: ./reset_db.sh [--yes] [--no-backup] [--skip-report]"
      echo "  --yes         跳过交互确认"
      echo "  --no-backup   不备份旧数据库（默认备份到 backend/backups/）"
      echo "  --skip-report 跳过成本优化报告生成"
      exit 0 ;;
    *) echo "❌ 未知参数: $arg （可用: --yes --no-backup --skip-report --help）"; exit 1 ;;
  esac
done

# ---- 选择 Python：优先项目根目录 venv ----
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  PY="$SCRIPT_DIR/.venv/bin/python"
elif [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
  PY="$BACKEND_DIR/.venv/bin/python"
else
  PY="python3"
fi

# ---- 数据库信息 ----
# 尊重 settings.py 的环境变量覆盖（DB_NAME / MOCK_DB_PATH），便于指定临时库验证
# 自动检测：统一 PostgreSQL（devops-postgres）在跑时默认走 postgres 分支（容器内执行）
if [ -z "${DB_ENGINE:-}" ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^devops-postgres$'; then
  DB_ENGINE="django.db.backends.postgresql"
fi
DB_ENGINE="${DB_ENGINE:-django.db.backends.sqlite3}"
DB_FILE="${DB_NAME:-$BACKEND_DIR/db.sqlite3}"
MOCK_DB="${MOCK_DB_PATH:-$BACKEND_DIR/mock_data/mock.db}"

is_sqlite=1
is_postgres=0
case "$DB_ENGINE" in
  *mysql*) is_sqlite=0 ;;
  *postgres*) is_sqlite=0; is_postgres=1 ;;
esac

# ---- 运行 Python 的统一入口 ----
# SQLite/MySQL（本地直连）→ 直接跑；PostgreSQL（容器化统一库）→ 进容器执行
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"
runpy() {
  if [ "$is_postgres" -eq 1 ]; then
    docker compose -f "$COMPOSE_FILE" exec -T backend python "$@"
  else
    "$PY" "$@"
  fi
}

echo "============================================="
echo "  Cloud Manager - 数据库一键重置"
echo "============================================="
echo "  Python:    $PY"
echo "  DB_ENGINE: $DB_ENGINE"

# ---- 交互确认（仅 SQLite 删库前询问）----
if [ "$CONFIRM_YES" -eq 0 ] && [ "$is_sqlite" -eq 1 ]; then
  echo ""
  read -r -p "将删除并重建 $DB_FILE 与 $MOCK_DB，确认继续? [y/N] " ans || true
  case "$ans" in
    y|Y|yes|YES) ;;
    *) echo "已取消，未做任何更改。"; exit 0 ;;
  esac
fi

cd "$BACKEND_DIR"

# ---- 备份并清理 SQLite ----
if [ "$is_sqlite" -eq 1 ]; then
  if [ "$DO_BACKUP" -eq 1 ]; then
    backup_dir="$BACKEND_DIR/backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    [ -f "$DB_FILE" ] && cp "$DB_FILE" "$backup_dir/db.sqlite3" \
      && echo "✅ 已备份主库 → backend/backups/$(basename "$backup_dir")/db.sqlite3"
    [ -f "$MOCK_DB" ] && cp "$MOCK_DB" "$backup_dir/mock.db" \
      && echo "✅ 已备份 Mock 库 → backend/backups/$(basename "$backup_dir")/mock.db"
  fi
  rm -f "$DB_FILE" "$MOCK_DB"
  echo "🧹 已清除旧 SQLite 数据库（db.sqlite3 / mock.db）"
elif [ "$is_postgres" -eq 1 ]; then
  # 统一 PostgreSQL：drop schema 重建 → 全链路种子（真正"出厂态"）
  echo "🧹 检测到 PostgreSQL 引擎，清空库（DROP SCHEMA public CASCADE）..."
  if docker ps --format '{{.Names}}' | grep -q '^devops-postgres$'; then
    docker exec devops-postgres psql -U devops -d "${DB_NAME:-devops_cloud}" \
      -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" >/dev/null \
      && echo "   ✅ 已清空 ${DB_NAME:-devops_cloud}"
  else
    echo "   ⚠️ 统一 PostgreSQL 未运行？请先执行 make bootstrap"
  fi
else
  echo "⚠️  检测到 MySQL 引擎（$DB_ENGINE），脚本不会删除数据库文件，seed 以幂等方式灌入。"
  echo "   如需彻底清空请先手动执行：DROP DATABASE ...; CREATE DATABASE ...;"
fi

echo ""

# ---- 全链路初始化 ----
echo "🔄 [1/8] 执行数据库迁移..."
runpy manage.py migrate --noinput

echo "🌱 [2/8] 灌入核心种子数据 (seed_data.py)..."
runpy seed_data.py

echo "📦 [3/8] 初始化 Mock 图谱数据 (mock_data/init_mock.py)..."
runpy -m mock_data.init_mock || echo "  ⚠️  Mock 数据已存在，跳过"

echo "⚙️  [4/8] 初始化成本优化规则..."
runpy manage.py seed_rules

echo "☁️  [5/8] 补充多云模拟数据 (阿里云/AWS)..."
runpy manage.py seed_multicloud

echo "📈 [6/8] 写入资源指标摘要 (模拟采集器)..."
runpy manage.py seed_metrics

echo "📚 [7/8] 初始化系统知识库..."
runpy manage.py seed_knowledge

if [ "$DO_REPORT" -eq 1 ]; then
  echo "📊 [8/8] 生成成本优化报告与建议 (cost.engine.run_all)..."
  runpy manage.py shell -c "from cost.engine import run_all; r = run_all(trigger='manual', operator='seed'); print('  优化报告已生成: ' + r.report_no)"
else
  echo "⏭️  [8/8] 跳过成本优化报告生成 (--skip-report)"
fi

echo ""
echo "============================================="
echo "  🎉 数据重置完成！"
echo "============================================="
echo "  演示账号："
echo "    admin       / admin123 (超级管理员)"
echo "    cloud_admin / admin123 (云管理员)"
echo "    ops_user    / admin123 (运维工程师)"
echo "    readonly    / admin123 (只读用户)"
echo "============================================="
