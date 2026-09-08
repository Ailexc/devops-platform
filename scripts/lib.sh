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
# 说明：业务项目统一在 projects/ 目录下；所有项目主文件为根目录 docker-compose.yml
#       （+ 可选 docker-compose.override.yml 自动叠加）；唯一例外 iam：compose 在
#       deploy/ 子目录（需成对加载 override）。
project_dir() {
  case "$1" in
    auth)     echo "projects/Authentication" ;;
    cloud)    echo "projects/CloudManager" ;;
    event)    echo "projects/EventManager" ;;
    iam)      echo "projects/PermissionCenter" ;;
    release)  echo "projects/ReleaseManager" ;;
    cmdb)     echo "projects/TaskManager" ;;
    workflow) echo "projects/WorkFlowCenter" ;;
    *)        echo "" ;;
  esac
}

project_compose_opts() {
  case "$1" in
    iam)   echo "-f deploy/docker-compose.yml -f deploy/docker-compose.override.yml" ;;
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

# ── 数据重置共享工具（重置契约 <Project>/scripts/reset.sh 与顶层 reset-all 共用）──────
# 契约规范见 docs/DevOps流程标准化梳理与改进方案.md §8.1

# 项目短名 → 统一库名
project_db() {
  case "$1" in
    auth) echo devops_auth ;;
    cloud) echo devops_cloud ;;
    event) echo devops_event ;;
    iam) echo devops_iam ;;
    release) echo devops_release ;;
    cmdb) echo devops_cmdb ;;
    workflow) echo devops_workflow ;;
    *) echo "" ;;
  esac
}

# 清空指定统一库（DROP SCHEMA → 重建；幂等）
drop_schema() {
  local db="$1"
  log "清空统一库 ${db}"
  if docker ps --format '{{.Names}}' | grep -q '^devops-postgres$'; then
    docker exec devops-postgres psql -U devops -d "$db" \
      -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" >/dev/null
    ok "  ${db} 已清空（schema 重建）"
  else
    err "统一 PostgreSQL 未运行，请先 make bootstrap"; exit 1
  fi
}

# 确保某项目的核心业务容器在运行（供 exec 使用；容器已停也先拉起）
# 用法：ensure_up <name> [services] [额外 compose 参数...]   例：ensure_up cmdb backend --force-recreate
ensure_up() {
  local name="$1" services="${2:-}" extra="${*:3}"
  local dir opts build_flag
  dir="$(project_dir "$name")"
  opts="$(project_compose_opts "$name")"
  build_flag="--build"
  [ "${NO_BUILD:-0}" = "1" ] && build_flag=""
  log "确保 ${name} 容器运行（${dir}）..."
  ( cd "$dir" && docker compose ${opts} up -d ${build_flag} ${services} ${extra} )
}

# 等待容器内初始化完成（容器 command 自带 migrate/seed，进程起来即代表完成）
# 仅看等待开始之后的新日志（--since，UTC 需 Z 后缀）。
# 注意：Django runserver 在 Docker 非 TTY 下 stdout 块缓冲，日志不刷出 → 改用 wait_http_ready。
wait_container_ready() {
  local name="$1" kw="${2:-Starting development server}" tries="${3:-120}" since i
  since="$(date -u +%Y-%m-%dT%H:%M:%S)Z"
  for i in $(seq 1 "$tries"); do
    if docker logs --since "$since" "$name" 2>&1 | grep -qE "$kw"; then
      ok "  ✓ ${name} 已就绪（migrate/seed 完成）"
      return 0
    fi
    if ! docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
      err "  ✗ ${name} 容器未在运行"; return 1
    fi
    sleep 1
  done
  err "  ✗ ${name} 未在 ${tries}s 内就绪（等待关键字 '$kw'）"
  docker logs --since "$since" "$name" 2>&1 | tail -20
  return 1
}

# HTTP 探活等待——最可靠的就绪判定（不依赖日志；容器内 python 探测，禁代理）。
# 任何 HTTP 响应（含 404/5xx）= 应用在处理请求 = 就绪。
wait_http_ready() {
  local name="$1" url="$2" tries="${3:-120}" i
  for i in $(seq 1 "$tries"); do
    if docker exec "$name" python -c '
import sys, urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    opener.open(sys.argv[1], timeout=2)
except urllib.error.HTTPError:
    pass  # 有 HTTP 响应（4xx/5xx 也算就绪）
except Exception:
    sys.exit(1)
' "$url" 2>/dev/null; then
      ok "  ✓ ${name} 已就绪（HTTP ${url} 可响应）"
      return 0
    fi
    if ! docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
      err "  ✗ ${name} 容器未在运行"; return 1
    fi
    sleep 1
  done
  err "  ✗ ${name} 未在 ${tries}s 内就绪（HTTP ${url} 无响应）"
  docker logs --tail 20 "$name" 2>&1
  return 1
}

# 确保镜像存在（本地无则从备用源拉取后 tag 成标准名；镜像源策略集中于此）
ensure_image() {
  local img="$1" src="$2"
  docker image inspect "$img" >/dev/null 2>&1 && return 0
  log "拉取镜像 $img（备用源：$src）..."
  if docker pull "$src"; then docker tag "$src" "$img"; else docker pull "$img"; fi
}

# ── 加载部署环境变量（ENV=local|cloud|server|...，按 deploy/<env>/.env.<env> 自动发现）─
# 设计目标：环境差异靠变量实时加载而非写死代码，新增环境只需添加文件，不改脚本。
#   - 本地：    deploy/local/.env.local     （OrbStack 自动 DNS / localhost 地址）
#   - 云端：    deploy/cloud/.env.cloud     （阿里云 ECS 公网 IP 地址）
#   - 服务器：  deploy/server/.env.server   （自建服务器 / 内网 IP 地址）
# 用法：
#   load_env                      # ENV 自动检测（仓库在 /opt/DevOpsPlatform → cloud，否则 local）
#   ENV=server load_env           # 显式指定环境类型
#   ENV_FILE=xxx load_env         # 指定任意 env 文件（覆盖默认路径）
# 新增环境：只需在 deploy/<name>/.env.<name> 中定义变量，然后 ENV=<name> make xxx
# 说明：自动向上定位仓库根（含 deploy/ 的目录），因此可在任意子目录调用。
load_env() {
  # 0) 定位仓库根（向上查找含 deploy/ 且含至少一个 .env.* 的目录）
  local repo_root="$PWD"
  while [ ! -d "$repo_root/deploy" ] && [ "$repo_root" != "/" ]; do
    repo_root="$(dirname "$repo_root")"
  done
  if [ "$repo_root" = "/" ] || [ ! -d "$repo_root/deploy" ]; then
    err "未找到仓库根（缺少 deploy/ 目录）"
    exit 1
  fi

  # 1) 确定 ENV（判定顺序：显式 ENV > .env-active 显式声明 > 兜底猜测）
  #    规范：环境必须显式声明，禁止靠猜（docs/DevOps流程标准化梳理与改进方案.md §3.1）
  local env
  local active_file="$repo_root/.env-active"
  if [ -n "${ENV:-}" ]; then
    env="$ENV"
  elif [ -s "$active_file" ]; then
    env="$(head -1 "$active_file" | tr -d '[:space:]')"
    case "$env" in
      local|server|cloud) : ;;
      *)
        err ".env-active 内容非法：'${env}'（应为 local/server/cloud），已忽略并走自动检测"
        env=""
        ;;
    esac
  fi

  if [ -z "${env:-}" ]; then
    # 兜底猜测（旧逻辑保留，但不再静默）
    case "$repo_root" in
      /opt/DevOpsPlatform) env=cloud ;;
      *)
        if   [ -f "$repo_root/deploy/server/.env.server" ]; then env=server
        elif [ -f "$repo_root/deploy/cloud/.env.cloud" ];   then env=cloud
        else env=local
        fi
        ;;
    esac
    # 首次使用：交互终端弹出选择并写入声明；非交互（CI/脚本）仅警告
    if [ -t 0 ] && [ -t 2 ]; then
      echo ""
      echo "⚠️  未声明部署环境（缺少 .env-active），请选择："
      local _e
      select _e in local server cloud; do
        [ -n "$_e" ] && env="$_e" && break
      done
      printf '%s\n' "$env" > "$active_file"
      ok "已写入 .env-active（切换环境：make use E=<env>）"
    else
      echo -e "\033[1;33m[devops:警告]\033[0m 未声明部署环境，自动检测为 '${env}'（建议：make use E=${env} 显式声明）" >&2
    fi
  fi

  # 2) 确定 env 文件（支持 ENV_FILE 显式指定；否则按 deploy/<env>/.env.<env> 查找）
  local env_file="${ENV_FILE:-$repo_root/deploy/${env}/.env.${env}}"
  if [ ! -f "$env_file" ]; then
    err "缺少环境变量文件 ${env_file}（ENV=${env}）"
    err "请创建 deploy/${env}/.env.${env}，或指定 ENV_FILE=/path/to/.env"
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
