#!/bin/bash
set -e

echo "🔄 等待统一数据库就绪..."
python3 wait_for_db.py

echo "🔄 执行数据库迁移..."
python3 manage.py migrate --noinput

echo "🌱 灌入种子数据..."
python3 seed_data.py

echo "📦 初始化 Mock 数据..."
python3 -m mock_data.init_mock || echo "  Mock 数据已存在，跳过"

echo "⚙️ 初始化成本优化规则..."
python3 manage.py seed_rules
echo "☁️ 补充多云模拟数据..."
python3 manage.py seed_multicloud
echo "📈 写入资源指标摘要（模拟采集器）..."
python3 manage.py seed_metrics

echo "📚 初始化系统知识库..."
python3 manage.py seed_knowledge

echo "🚀 启动 Django 服务..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
