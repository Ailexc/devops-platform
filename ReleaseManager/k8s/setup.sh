#!/bin/bash
set -e

echo "=== 初始化 K8s 集群 ==="

# 创建 kind 集群
echo ">>> 创建 kind 集群..."
kind create cluster --config kind-config.yaml

# 创建命名空间
echo ">>> 创建命名空间..."
kubectl apply -f namespace.yaml

# 部署所有应用
echo ">>> 部署应用..."
kubectl apply -f python-app.yaml
kubectl apply -f go-app.yaml
kubectl apply -f node-app.yaml

# 等待所有 Pod 就绪
echo ">>> 等待 Pod 就绪..."
kubectl wait --for=condition=ready pod -l app=python-app -n release-demo --timeout=120s
kubectl wait --for=condition=ready pod -l app=go-app -n release-demo --timeout=120s
kubectl wait --for=condition=ready pod -l app=node-app -n release-demo --timeout=120s

echo "=== 集群就绪 ==="
kubectl get pods -n release-demo
echo ""
echo "服务访问地址:"
echo "  Python App: http://localhost:30080"
echo "  Go App:     http://localhost:30081"
echo "  Node App:   http://localhost:30082"