#!/usr/bin/env bash
# ============================================================
# EventManager 重置契约（规范：docs/DevOps流程标准化梳理与改进方案.md §8.1）
# 幂等 / 自包含 / 自验证（init-all.sh 内含）/ 无交互
# 顶层 reset-all.sh 爆破数据层后调用；也可独立运行
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../../.."
source scripts/lib.sh
load_env >/dev/null
cd projects/EventManager

echo "── [event] 清库重建 + 演示数据（init-all.sh，Python+Go 双栈）..."
exec bash scripts/init-all.sh -c -t "${EVENT_SEED_COUNT:-1000}"
