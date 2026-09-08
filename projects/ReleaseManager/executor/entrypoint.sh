#!/bin/sh
# 修复 kubeconfig server 地址（OrbStack K8s 证书不含 host.docker.internal）
# kubectl wrapper 已在 Dockerfile 中创建，entrypoint 不再动 kubectl

ORIGINAL_KUBECONFIG="/app/config/kubeconfig"

if [ -f "$ORIGINAL_KUBECONFIG" ]; then
    cp "$ORIGINAL_KUBECONFIG" /tmp/kubeconfig-fixed
    sed -i 's|server: https://127.0.0.1:|server: https://host.docker.internal:|g' /tmp/kubeconfig-fixed
    sed -i 's|server: https://localhost:|server: https://host.docker.internal:|g' /tmp/kubeconfig-fixed
    export KUBECONFIG=/tmp/kubeconfig-fixed
fi

exec "$@"
