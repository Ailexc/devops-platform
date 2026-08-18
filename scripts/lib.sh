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

# ── 加载部署环境变量（ENV=local|cloud，单一事实来源）─────────────────
# 设计目标：本地与云端共用一套代码逻辑，环境差异靠变量实时加载而非写死。
#   - 本地：  deploy/local/.env.local   （OrbStack 自动 DNS / localhost 地址）
#   - 云端：  deploy/cloud/.env.cloud   （阿里云 ECS 公网 IP 地址）
# 用法：
#   load_env                      # ENV 自动检测（仓库在 /opt/DevOpsPlatform → cloud，否则 local）
#   ENV=cloud load_env            # 显式指定环境
#   ENV_FILE=xxx load_env         # 指定任意 env 文件（覆盖默认路径）
# 说明：自动向上定位仓库根（含 deploy/ 的目录），因此可在任意子目录调用
#       （如 ( cd Authentication && ./reset.sh ) 内也能正确加载）。
# 原理：set -a 导出全部变量，使 docker compose 的 ${VAR:-default} 插值
#       与 seed.py 的 os.environ 都能读到 → 门户跳转地址按环境实时生效。
load_env() {
  # 0) 定位仓库根（向上查找含 deploy/local 或 deploy/cloud 的目录）
  local repo_root="$PWD"
  while [ ! -f "$repo_root/deploy/local/.env.local" ] && [ ! -f "$repo_root/deploy/cloud/.env.cloud" ] && [ "$repo_root" != "/" ]; do
    repo_root="$(dirname "$repo_root")"
  done
  if [ "$repo_root" = "/" ]; then
    err "未找到仓库根（缺少 deploy/local/.env.local 或 deploy/cloud/.env.cloud）"
    exit 1
  fi

  # 1) 确定 ENV（local|cloud）
  local env
  if [ -z "${ENV:-}" ]; then
    case "$repo_root" in
      /opt/DevOpsPlatform) env=cloud ;;
      *) env=local ;;
    esac
  else
    env="$ENV"
  fi
  case "$env" in
    local|cloud) ;;
    *) err "ENV 取值必须是 local 或 cloud（当前: ${env}）"; exit 1 ;;
  esac

  # 2) 确定 env 文件（支持 ENV_FILE 显式指定）
  local env_file="${ENV_FILE:-$repo_root/deploy/${env}/.env.${env}}"
  if [ ! -f "$env_file" ]; then
    err "缺少环境变量文件 ${env_file}（ENV=${env}）"
    err "请确认仓库含 deploy/local/.env.local 或 deploy/cloud/.env.cloud"
    exit 1
  fi

  # 3) 加载并导出（供 docker compose / 子进程读取）
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  export ENV="$env"
  export ENV_FILE="$env_file"
  ok "部署环境：${env}（${env_file}）"
}
