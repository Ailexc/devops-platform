#!/usr/bin/env bash
# ============================================================
# WorkFlowCenter 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证 / 无交互
# 说明：api 容器 command 自带 migrate --noinput（幂等），先 force-recreate
#       （DB 重建后旧进程仍连旧 schema）并等就绪，再 exec reset_demo
#       （migrate+flush+loaddata+seed，幂等）——避免并发 migrate 冲突。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/lib.sh
load_env >/dev/null

echo "── [workflow] 重建 api 容器..."
ensure_up workflow api --force-recreate

echo "── [workflow] 等待就绪（HTTP 探活，规避 stdout 缓冲）..."
wait_http_ready workflow-api http://127.0.0.1:8000/ 180

echo "── [workflow] 演示数据（reset_demo）..."
( cd projects/WorkFlowCenter && docker compose exec -T api python manage.py reset_demo )

ok "  ✓ workflow 重置完成"
