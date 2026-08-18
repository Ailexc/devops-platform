#!/bin/bash
# 统一认证中心 - 数据库重置脚本
# 用途：一键重置所有数据库到初始状态（删除数据库文件 + 重启服务）
# 使用：./reset.sh [--full]
#   --full: 同时重置 LDAP 数据卷（需要重新导入种子数据）

set -e  # 遇到错误立即退出

# 加载部署环境变量（本地/云端统一：ENV=local|cloud 自动检测）
# 由 reset-all.sh 调用时父进程已导出，此处幂等重载；独立运行也能正确识别环境。
if [ -f ../scripts/lib.sh ]; then
    source ../scripts/lib.sh
    load_env
fi

echo "🔄 统一认证中心 - 数据库重置"
echo "================================="

# 1. 停止所有服务
echo "1️⃣  停止所有服务..."
docker compose down

# 2. 重置统一 PostgreSQL 中的认证库（drop schema → 重启后自动建表+种子）
echo "2️⃣  重置统一认证数据库（devops_auth）..."
if docker ps --format '{{.Names}}' | grep -q '^devops-postgres$'; then
    docker exec devops-postgres psql -U devops -d devops_auth -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null
    echo "   ✅ 已重置 devops_auth（重启后自动重建表结构 + 种子数据）"
else
    echo "   ⚠️ 统一 PostgreSQL 未运行？请先执行 make bootstrap"
fi
# 清理遗留的本地 SQLite 文件（已不再使用，仅作卫生清理）
rm -f auth.db
rm -f data/auth.db

# 3. 检查是否需要重置 LDAP
if [[ "$1" == "--full" ]]; then
    echo "3️⃣  重置 LDAP 数据卷（--full 模式）..."
    docker volume rm authentication_ldap-data 2>/dev/null || true
    docker volume rm authentication_ldap-config 2>/dev/null || true
    echo "   ✅ 已删除 LDAP 数据卷"
else
    echo "3️⃣  跳过 LDAP 重置（如需重置，请使用 --full 参数）"
fi

# 4. 可选：删除 JWT 密钥（重新生成）
echo "4️⃣  保留 JWT 密钥（保持 token 有效性）..."
# 如果需要重新生成密钥，取消下面的注释：
# rm -rf backend/.jwt_keys/
# echo "   ✅ 已删除 JWT 密钥"

# 5. 重启服务
echo "5️⃣  重启服务..."
if [ "${NO_BUILD:-0}" = "1" ]; then
    docker compose up -d
else
    docker compose up -d --build
fi

# 6. 等待服务启动
echo "6️⃣  等待服务启动..."
CID=$(docker compose ps -q auth-backend)
for i in $(seq 1 30); do
    state=$(docker inspect -f '{{.State.Running}}' "$CID" 2>/dev/null || echo "false")
    [ "$state" = "true" ] && break
    sleep 2
done

# 7. 验证服务状态
echo "7️⃣  验证服务状态..."
if docker inspect -f '{{.State.Running}}' "$CID" 2>/dev/null | grep -q true; then
    echo "   ✅ 认证中心运行正常"
else
    echo "   ❌ 认证中心启动失败，请检查日志：docker compose logs auth-backend"
    exit 1
fi

echo ""
echo "🎉 重置完成！"
echo "================================="
echo "📍 访问地址："
echo "   门户：http://portal.authentication.orb.local"
echo "   API：http://api.authentication.orb.local/docs"
echo ""
echo "👤 测试账号："
echo "   admin/admin1234 (管理员)"
echo "   zhangsan/demo1234 (普通用户)"
echo "   lisi/demo1234 (普通用户)"
echo "   wangwu/demo1234 (普通用户)"
echo ""
echo "💡 提示：数据库将在首次访问时自动重建（表结构 + 种子数据）"