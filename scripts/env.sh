#!/usr/bin/env bash
# ============================================================
# env —— 环境查看 / 切换 / 门户地址（规范：环境显式声明，禁止靠猜）
# 用法：
#   scripts/env.sh               # 查看当前环境与关键地址
#   scripts/env.sh use <env>     # 切换环境（写入 .env-active）
#   scripts/env.sh portal        # 打印门户地址
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

cmd="${1:-show}"
case "$cmd" in
  show)
    load_env >/dev/null
    echo "当前环境：${ENV}（${ENV_FILE}）"
    if [ -f .env-active ]; then
      echo "声明来源：.env-active（显式声明）"
    else
      echo "声明来源：自动检测（未声明，建议 make use E=${ENV} 固化）"
    fi
    echo "门户地址：${PORTAL_URL:-http://${SERVER_IP:-localhost}:8088}"
    echo "服务器 IP：${SERVER_IP:-（未配置）}"
    echo "切换环境：make use E=local|server|cloud"
    ;;
  use)
    E="${2:-}"
    case "$E" in
      local|server|cloud) ;;
      *) err "用法：make use E=local|server|cloud（收到：'${E}'）"; exit 1 ;;
    esac
    [ -f "deploy/${E}/.env.${E}" ] || { err "缺少 deploy/${E}/.env.${E}"; exit 1; }
    printf '%s\n' "$E" > .env-active
    ok "已切换环境：${E}（写入 .env-active，下一条 make 命令生效）"
    exec bash scripts/env.sh show
    ;;
  portal)
    load_env >/dev/null
    echo "${PORTAL_URL:-http://${SERVER_IP:-localhost}:8088}"
    ;;
  *)
    err "未知子命令：$1（可用: show / use / portal）"
    exit 1
    ;;
esac
