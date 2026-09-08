#!/usr/bin/env bash
# ============================================================
# TaskManager 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证 / 无交互
# 说明：backend 容器 command 自带 migrate + seed_demo_data（幂等），
#       重建容器即完成重置。不可再 exec 重复 migrate —— schema 清空后
#       并发 migrate 会触发 pg_type_typname_nsp_index 唯一约束竞态。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/lib.sh
load_env >/dev/null

echo "── [cmdb] 重建 backend 容器（自带 migrate + seed）..."
ensure_up cmdb backend --force-recreate

echo "── [cmdb] 等待就绪（HTTP 探活，规避 runserver stdout 缓冲）..."
wait_http_ready cmdb-task-backend http://127.0.0.1:8000/ 180

ok "  ✓ cmdb 重置完成"
