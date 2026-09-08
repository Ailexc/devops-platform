#!/usr/bin/env bash
# ============================================================
# menu —— 交互式菜单（make 裸敲进入；仅交互终端，CI 自动降级为 help）
# 原则：菜单只是命令的遥控器，每项背后仍是标准 make 目标
# ============================================================
set -uo pipefail
cd "$(dirname "$0")/.."

# 非交互（CI/管道）→ 降级打印帮助
if [ ! -t 0 ]; then
  exec make help
fi

source scripts/lib.sh

header() {
  load_env >/dev/null 2>&1 || true
  local portal="${PORTAL_URL:-http://${SERVER_IP:-localhost}:8088}"
  echo ""
  echo "━━━━━━━━━━ DevOps Platform ━━━━━━━━━━"
  echo "  当前环境: ${ENV:-未知} · 门户: ${portal}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  1) 启动全部            (make start)"
  echo "  2) 停止全部            (make down)"
  echo "  3) 恢复出厂态          (make reset)"
  echo "  4) 补齐演示数据        (make seed)"
  echo "  5) 单项目管理          (start/down/reset/logs)"
  echo "  6) 状态总览            (make status)"
  echo "  7) 端口清单            (make ports)"
  echo "  8) 门户地址            (make portal)"
  echo "  9) 切换环境            (make use)"
  echo "  q) 退出"
}

single_project() {
  local projects=(auth cloud event iam release cmdb workflow)
  echo "── 选择项目 ──"
  select p in "${projects[@]}"; do
    [ -z "$p" ] && return
    echo "── $p：1) start  2) down  3) reset  4) logs ──"
    read -rp "动作> " act
    case "$act" in
      1) make start P="$p" ;;
      2) make down P="$p" ;;
      3) make reset P="$p" ;;
      4) make logs P="$p" ;;
      *) echo "（取消）" ;;
    esac
    return
  done
}

while true; do
  header
  read -rp "选择> " choice
  case "$choice" in
    1) make start ;;
    2) make down ;;
    3) make reset ;;
    4) make seed ;;
    5) single_project ;;
    6) make status ;;
    7) make ports ;;
    8) make portal ;;
    9) read -rp "环境（local/server/cloud）> " e; make use E="$e" ;;
    q|Q|"") echo "再见"; exit 0 ;;
    *) echo "（无效选择）" ;;
  esac
  echo ""
  read -rp "回车返回菜单（q 退出）> " back
  [ "$back" = "q" ] && { echo "再见"; exit 0; }
done
