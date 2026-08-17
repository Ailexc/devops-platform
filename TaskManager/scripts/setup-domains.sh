#!/bin/bash
# ──────────────────────────────────────────────
# CMDB 本地开发环境 DNS 配置工具
# 使用场景：通过 cmdb.*.local 域名访问本地服务
# ──────────────────────────────────────────────

set -e

# 需要注册的本地域名列表
DOMAINS=(
  "cmdb.task.local"
  "cmdb.api.local"
  "cmdb.event.local"
  "cmdb.asset.local"
)

HOSTS_FILE="/etc/hosts"
DOCKER_COMPOSE_FILE="$(cd "$(dirname "$0")/.." && pwd)/docker-compose.yml"

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     CMDB 本地域名配置工具                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 检查 Docker 服务状态 ──
check_docker() {
  echo -e "${YELLOW}[1/3] 检查 Docker 服务状态...${NC}"
  if docker info --format '{{.ServerVersion}}' >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Docker 运行中${NC}"
  else
    echo -e "  ${RED}✗ Docker 未运行，请先启动 Docker Desktop${NC}"
    exit 1
  fi
}

# ── 配置 /etc/hosts ──
setup_hosts() {
  echo ""
  echo -e "${YELLOW}[2/3] 配置本地域名解析 (/etc/hosts)...${NC}"

  CHANGED=false
  for domain in "${DOMAINS[@]}"; do
    if grep -q "^127\.0\.0\.1\s\+$domain" "$HOSTS_FILE" 2>/dev/null; then
      echo -e "  ${GREEN}✓ $domain${NC}"
    else
      echo -e "  ${YELLOW}➕ 添加 $domain → 127.0.0.1${NC}"
      # 用 sudo 写入，如果失败则提示手动操作
      if echo "127.0.0.1 $domain" | sudo tee -a "$HOSTS_FILE" >/dev/null 2>&1; then
        CHANGED=true
        echo -e "  ${GREEN}✓ $domain 已添加${NC}"
      else
        echo -e "  ${RED}✗ 无法写入 $HOSTS_FILE${NC}"
        echo -e "  ${YELLOW}  请手动执行:${NC}"
        echo -e "  echo '127.0.0.1 $domain' | sudo tee -a /etc/hosts"
      fi
    fi
  done

  if [ "$CHANGED" = true ]; then
    # 刷新 DNS 缓存 (macOS)
    if command -v dscacheutil &>/dev/null; then
      sudo dscacheutil -flushcache 2>/dev/null
      sudo killall -HUP mDNSResponder 2>/dev/null
      echo -e "  ${GREEN}✓ DNS 缓存已刷新${NC}"
    fi
  fi
}

# ── 启动服务 ──
start_services() {
  echo ""
  echo -e "${YELLOW}[3/3] 启动反向代理服务...${NC}"

  cd "$(dirname "$0")/.."

  # 检查 reverse-proxy 是否已在运行
  if docker compose ps reverse-proxy 2>/dev/null | grep -q "Up"; then
    echo -e "  ${YELLOW}⟳ 反向代理已运行，重新加载配置...${NC}"
    docker compose exec reverse-proxy nginx -s reload 2>/dev/null || true
  else
    echo -e "  ${YELLOW}⟳ 启动 reverse-proxy...${NC}"
    docker compose up -d reverse-proxy 2>&1
  fi
  echo -e "  ${GREEN}✓ 反向代理就绪${NC}"
}

# ── 验证 ──
verify() {
  echo ""
  echo -e "${YELLOW}验证域名解析...${NC}"
  for domain in "${DOMAINS[@]}"; do
    ip=$(ping -c1 -t2 "$domain" 2>/dev/null | head -1 | awk '{print $3}' | tr -d '()' || echo "")
    if [ -n "$ip" ]; then
      echo -e "  ${GREEN}✓ $domain → $ip${NC}"
    else
      echo -e "  ${RED}✗ $domain 解析失败${NC}"
    fi
  done
}

# ── 输出访问地址 ──
print_urls() {
  echo ""
  echo -e "${BLUE}══════════════════════════════════════════${NC}"
  echo -e "${BLUE}  ✅ 配置完成！可用以下地址访问：${NC}"
  echo -e "${BLUE}══════════════════════════════════════════${NC}"
  echo ""
  echo -e "  📋  ${GREEN}http://cmdb.task.local${NC}  → 任务管理系统"
  echo -e "  🔌  ${GREEN}http://cmdb.api.local${NC}    → 后端 API"
  echo -e "  ⏳  ${YELLOW}http://cmdb.event.local${NC}  → 事件管理 (预留)"
  echo -e "  ⏳  ${YELLOW}http://cmdb.asset.local${NC}  → 资产管理 (预留)"
  echo ""
  echo -e "  💡 直接访问 ${GREEN}http://localhost${NC} 可看到服务列表"
  echo ""
}

# ── 主流程 ──
main() {
  check_docker
  setup_hosts
  start_services
  verify
  print_urls
}

main "$@"
