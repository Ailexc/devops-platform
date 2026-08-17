#!/usr/bin/env bash
# ============================================================
# 公共函数库
# ============================================================

log()  { echo -e "\033[1;36m[devops]\033[0m $*"; }
err()  { echo -e "\033[1;31m[devops:错误]\033[0m $*" >&2; }
ok()   { echo -e "\033[1;32m[devops]\033[0m $*"; }

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    err "未找到 docker，请先安装 Docker / OrbStack"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    err "Docker 未运行，请先启动 Docker / OrbStack"
    exit 1
  fi
}

# 等待容器 healthy（最多 N 秒）
wait_container_healthy() {
  local name="$1" tries="${2:-60}"
  for _ in $(seq 1 "$tries"); do
    local state
    state="$(docker inspect -f '{{.State.Health.Status}}' "$name" 2>/dev/null || echo missing)"
    if [ "$state" = "healthy" ]; then
      ok "  ${name} 就绪"
      return 0
    fi
    sleep 2
  done
  err "容器 ${name} 未在 ${tries}x2 秒内就绪（当前状态: ${state}）"
  exit 1
}

# ── 项目短名 → 目录 / compose 参数（统一映射，全脚本共用）──────────
# 说明：cloud 的 compose 在 docker-compose.prod.yml；iam 在 deploy/ 子目录。
# 其余项目均用根目录默认 docker-compose.yml。
project_dir() {
  case "$1" in
    auth)     echo "Authentication" ;;
    cloud)    echo "CloudManager" ;;
    event)    echo "EventManager" ;;
    iam)      echo "PermissionCenter" ;;
    release)  echo "ReleaseManager" ;;
    cmdb)     echo "TaskManager" ;;
    workflow) echo "WorkFlowCenter" ;;
    *)        echo "" ;;
  esac
}

project_compose_opts() {
  case "$1" in
    cloud) echo "-f docker-compose.prod.yml" ;;
    iam)   echo "-f deploy/docker-compose.yml" ;;
    *)     echo "" ;;
  esac
}

# 校验项目短名（不存在则报错退出）
require_project() {
  if [ -z "$(project_dir "$1")" ]; then
    err "未知项目 '$1'（可用: auth/cloud/event/iam/release/cmdb/workflow）"
    exit 1
  fi
}
