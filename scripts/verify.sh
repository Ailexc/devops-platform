#!/usr/bin/env bash
# ============================================================
# verify —— 部署冒烟验证：门户 + 7 系统多端口直测
# 网关按 Host(<IP>) 匹配路由 → Host 头 + localhost 直测，规避 NAT hairpin 不可达
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
load_env >/dev/null

SERVER_IP="${SERVER_IP:-localhost}"
PUBLIC_HOST="${PORTAL_URL#*//}"; PUBLIC_HOST="${PUBLIC_HOST%%:*}"
check_host="${PUBLIC_HOST:-$SERVER_IP}"

echo ""
echo "==================== 部署验证 ===================="
echo "── 容器状态 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops|auth|cloud|event|iam|release|cmdb|task|workflow|traefik|gateway' | sort
echo ""
echo "── 统一基础设施健康 ──"
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'devops-postgres|devops-redis|devops-rabbitmq' | grep healthy || echo "（部分基础设施未 healthy）"
echo ""
echo "── 门户 + 7 系统（纯 IP 多端口直测，免 hosts 映射）──"
check_port() {
  local name="$1" port="$2"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: ${check_host}" "http://localhost:${port}/" 2>/dev/null || echo ERR)
  printf "  %-22s HTTP %s\n" "${check_host}:${port}  ${name}" "${code}"
}
check_port "门户 Portal"           8088
check_port "任务 TaskManager"      8089
check_port "多云 CloudManager"     8090
check_port "流程 WorkFlowCenter"   8091
check_port "事件 EventManager"     8092
check_port "发布 ReleaseManager"   8093
check_port "权限 PermissionCenter" 8094
echo ""
echo "=================================================="
ok "部署完成！门户：${PORTAL_URL:-http://${SERVER_IP:-localhost}:8088}"
