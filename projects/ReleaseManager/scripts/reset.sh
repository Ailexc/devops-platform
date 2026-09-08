#!/usr/bin/env bash
# ============================================================
# ReleaseManager 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证（内部脚本含）/ 无交互
# 顶层 reset-all.sh 爆破数据层后调用；也可独立运行
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/lib.sh
load_env >/dev/null
cd projects/ReleaseManager

# 快速模式（NO_BUILD=1，顶层 make reset 默认）复用现有镜像；默认 -y 跳过确认
ARGS="-y"
[ "${NO_BUILD:-0}" = "1" ] && ARGS="$ARGS --no-build"

echo "── [release] 恢复出厂态（reset-all.sh $ARGS）..."
exec bash scripts/reset-all.sh $ARGS
