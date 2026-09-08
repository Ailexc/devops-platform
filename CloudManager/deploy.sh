#!/bin/bash
set -e

echo "========================================="
echo "  Cloud Manager - Docker 部署"
echo "========================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop 或 OrbStack"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
fi

# 检查前端是否已构建
if [ ! -d "frontend/dist" ]; then
    echo "🔨 构建前端..."
    cd frontend && pnpm install && pnpm build && cd ..
fi

# 停止之前的容器
echo "🧹 清理旧容器..."
docker compose -f docker-compose.yml down 2>/dev/null || true

# 构建并启动
echo "🔨 构建并启动服务..."
docker compose -f docker-compose.yml up -d --build

echo ""
echo "⏳ 等待服务启动..."
echo "   MySQL 正在初始化..."
sleep 30

echo ""
echo "========================================="
echo "  ✅ 服务已启动"
echo "========================================="
echo ""
echo "  🌐 前端:  http://cloud-manager-nginx.orb.local"
echo "  📡 后端:  http://cloud-manager-backend.orb.local/api/"
echo ""
echo "  📋 演示账号: admin / admin123"
echo ""
echo "  查看日志: docker compose -f docker-compose.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.yml down"
echo "========================================="
echo "  📋 演示账号: admin / admin123"
echo ""
echo "  查看日志: $COMPOSE_CMD -f docker-compose.yml logs -f"
echo "  停止服务: $COMPOSE_CMD -f docker-compose.yml down"
echo "  重启服务: $COMPOSE_CMD -f docker-compose.yml restart"
echo "========================================="
