#!/usr/bin/env python3
"""
生成 backend ↔ executor 服务间认证密钥对（Ed25519，模拟 spug-lambda 的公私钥签名）

- backend 持有私钥: backend/config/executor_private.pem   （仅 backend 可签发）
- executor 持有公钥: executor/config/backend_public.pem    （executor 只验签，无法伪造 backend 请求）

用法:
    python scripts/gen_executor_keys.py [--force]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_KEY = ROOT / "backend" / "config" / "executor_private.pem"
EXECUTOR_KEY = ROOT / "executor" / "config" / "backend_public.pem"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="强制重新生成（覆盖已有密钥）")
    args = parser.parse_args()

    if BACKEND_KEY.exists() and EXECUTOR_KEY.exists() and not args.force:
        print(f"[OK] 密钥已存在，跳过生成（使用 --force 重新生成）")
        print(f"     {BACKEND_KEY}")
        print(f"     {EXECUTOR_KEY}")
        return 0

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as e:
        print(f"[ERROR] 缺少 cryptography 依赖: {e}，请先安装", file=sys.stderr)
        return 1

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    BACKEND_KEY.parent.mkdir(parents=True, exist_ok=True)
    EXECUTOR_KEY.parent.mkdir(parents=True, exist_ok=True)

    BACKEND_KEY.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    EXECUTOR_KEY.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    print(f"[OK] 私钥已生成（backend 持有）: {BACKEND_KEY}")
    print(f"[OK] 公钥已生成（executor 持有）: {EXECUTOR_KEY}")
    print("[INFO] 密钥已加入 .gitignore，不会提交到仓库")
    return 0


if __name__ == "__main__":
    sys.exit(main())
