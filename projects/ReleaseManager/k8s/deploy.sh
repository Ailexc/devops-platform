#!/bin/bash
set -e

# 发布系统 Demo - K8s 部署脚本
# 用法: ./deploy.sh <app-name> <version> <env>

APP_NAME=${1:-python-app}
VERSION=${2:-latest}
ENV=${3:-dev}

echo "=== 部署 $APP_NAME (v$VERSION) 到 $ENV 环境 ==="

# 构建 Docker 镜像
echo ">>> 构建镜像..."
docker build -t release-demo/$APP_NAME:$VERSION ../demo-apps/$APP_NAME/

# 加载到 kind 集群
echo ">>> 加载镜像到 kind 集群..."
kind load docker-image release-demo/$APP_NAME:$VERSION --name release-demo

# 更新 Deployment 镜像版本
echo ">>> 更新 Deployment..."
kubectl set image deployment/$APP_NAME -n release-demo $APP_NAME=release-demo/$APP_NAME:$VERSION

# 滚动状态检查
echo ">>> 等待滚动更新完成..."
kubectl rollout status deployment/$APP_NAME -n release-demo --timeout=120s

echo "=== 部署完成 ==="
echo "服务地址:"
echo "  Python App: http://localhost:30080"
echo "  Go App:     http://localhost:30081"
echo "  Node App:   http://localhost:30082"