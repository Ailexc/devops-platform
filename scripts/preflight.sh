#!/usr/bin/env bash
# ============================================================
# preflight —— 非破坏性演示数据确保（幂等；make start / make seed / deploy 共用）
# 与重置契约（<Project>/scripts/reset.sh）的区别：不炸数据，只"缺啥补啥"。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
load_env >/dev/null

log "preflight 1/4：IAM 演示数据（用户/应用/授权模型）"
( cd projects/PermissionCenter && docker compose -f deploy/docker-compose.yml run -T --rm iam-server iam-server seed < /dev/null ) \
  && ok "  ✓ IAM seed 完成" \
  || err "  ✗ IAM seed 失败（继续；可单独重试：make seed）"

log "preflight 2/4：LDAP 身份目录 + LAM 管理台"
ensure_image "osixia/openldap:1.5.0" "docker.1ms.run/osixia/openldap:1.5.0" || true
ensure_image "ldapaccountmanager/lam:stable" "docker.1ms.run/ldapaccountmanager/lam:stable" || true
( cd projects/Authentication && docker compose --profile ldap up -d ) \
  && ok "  ✓ openldap + lam 已就绪" \
  || err "  ✗ LDAP 启动失败（继续）"

log "preflight 3/4：ReleaseManager 演示数据（RBAC/应用/发布流水线）"
docker exec release-backend python manage.py init_seed 2>/dev/null \
  && ok "  ✓ release init_seed" \
  || err "  ✗ release init_seed 跳过（容器未运行？）"
docker exec release-backend python manage.py seed_releases 2>/dev/null \
  && ok "  ✓ release seed_releases" \
  || true

log "preflight 4/4：WorkFlowCenter 演示数据（工单/待办/审批）"
docker exec workflow-api python manage.py seed_data 2>/dev/null \
  && ok "  ✓ workflow seed_data" \
  || err "  ✗ workflow seed_data 跳过（容器未运行？）"
docker exec workflow-api python manage.py seed_demo_data 2>/dev/null \
  && ok "  ✓ workflow seed_demo_data" \
  || true

ok "preflight 完成（非破坏性；恢复出厂态请用 make reset）"
