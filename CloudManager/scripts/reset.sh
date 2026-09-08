#!/usr/bin/env bash
# ============================================================
# CloudManager 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证 / 无交互
# 说明：backend entrypoint.sh 自带 migrate + 全套种子（seed_data/mock/rules/
#       multicloud/metrics/knowledge），重建容器即完成重置。不可再 exec 重复
#       migrate/seed —— schema 清空后并发会触发唯一约束竞态。
#       仅补生成成本优化报告（entrypoint 未覆盖的 [8/8]）。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/lib.sh
load_env >/dev/null

echo "── [cloud] 重建 backend 容器（entrypoint 自带 migrate + seed）..."
ensure_up cloud backend --force-recreate

echo "── [cloud] 等待就绪..."
wait_container_ready cloud_manager_backend "Booting worker|Listening at|Application startup complete" 240

echo "── [cloud] 生成成本优化报告..."
( cd CloudManager && docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "from cost.engine import run_all; r = run_all(trigger='manual', operator='seed'); print('  ✓ 优化报告已生成: ' + r.report_no)" )

ok "  ✓ cloud 重置完成"
