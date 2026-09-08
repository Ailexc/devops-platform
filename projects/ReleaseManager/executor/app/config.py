"""
executor 服务配置

release-executor（模拟 spug-lambda）：独立执行端，只接收 backend 签发的请求，
负责所有真实的 K8s / 容器操作。通过环境变量可覆盖默认值（为后续 OrbStack 部署预留）。
"""

import os
from pathlib import Path

# executor 包根目录（executor/）
BASE_DIR = Path(__file__).resolve().parent.parent

# backend 公钥路径（用于验证 backend 签发的 JWT）
BACKEND_PUBLIC_KEY_PATH = os.environ.get(
    "BACKEND_PUBLIC_KEY_PATH",
    str(BASE_DIR / "config" / "backend_public.pem"),
)

# 期望的 issuer —— backend 的身份标识
ISSUER = "release-system-backend"

# SSE 心跳间隔（秒）：无新日志时发送注释帧，防止连接被中间层断开
SSE_HEARTBEAT_INTERVAL = 15

# 单次执行内存日志保留上限（条数）
MAX_LOG_LINES = 2000
