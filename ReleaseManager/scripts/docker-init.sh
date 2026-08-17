#!/bin/bash
# =============================================================================
# 发布系统 Demo — Docker 容器初始化脚本
# 在 init 容器中运行：生成密钥 + 迁移 + 种子数据 + demo 权限
# =============================================================================

set -e

echo "🚀 开始初始化发布系统..."

# ── 生成服务间认证密钥（如果不存在）──────────────────────────
echo "📝 检查服务间认证密钥..."
mkdir -p /app/keys
python -c "
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

private_key_path = Path('/app/keys/executor_private.pem')
public_key_path = Path('/app/keys/backend_public.pem')

if private_key_path.exists() and public_key_path.exists():
    print('[OK] 密钥已存在，跳过生成')
else:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    print(f'[OK] 私钥已生成: {private_key_path}')
    print(f'[OK] 公钥已生成: {public_key_path}')
"
echo "✅ 服务间认证密钥已就绪"

# ── 数据库迁移 ──────────────────────────────────────────────
echo "📝 执行数据库迁移..."
python manage.py migrate --run-syncdb
echo "✅ 数据库迁移完成"

# ── 种子数据 ────────────────────────────────────────────────
echo "📝 初始化种子数据..."
python manage.py init_seed
echo "✅ 种子数据初始化完成"

# ── 完成 ────────────────────────────────────────────────────
echo ""
echo "🎉 发布系统初始化完成！"
