#!/usr/bin/env bash
# ============================================================
# seed —— 补齐演示数据（非破坏性幂等 = preflight）
# 语义区分：make reset = 爆破重建（出厂态）；make seed = 缺啥补啥
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash scripts/preflight.sh
