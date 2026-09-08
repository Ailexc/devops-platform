#!/usr/bin/env bash
# ============================================================
# PermissionCenter 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证 / 无交互
# 说明：--reset 清空后按最新 seed 重建（用户/应用/授权模型）。
#       run -T 且 stdin </dev/null —— 无 TTY 环境（nohup/管道）防挂起。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/lib.sh
load_env >/dev/null

echo "── [iam] seed --reset（用户/应用/授权模型）..."
ensure_up iam iam-server
( cd projects/PermissionCenter && docker compose -f deploy/docker-compose.yml run -T --rm iam-server iam-server seed --reset < /dev/null )

ok "  ✓ iam 重置完成"
