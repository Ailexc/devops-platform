"""等待数据库就绪（统一 PostgreSQL）—— 跨项目可复用。

用法（Docker 容器启动时）：
    python /srv/auth/app/wait_for_db.py && uvicorn app.main:app ...

环境变量：
    WAIT_DB_HOST   默认 devops-postgres
    WAIT_DB_PORT   默认 5432
    WAIT_DB_TIMEOUT 默认 120 秒
"""
import os
import socket
import sys
import time

host = os.environ.get("WAIT_DB_HOST", "devops-postgres")
port = int(os.environ.get("WAIT_DB_PORT", "5432"))
timeout = float(os.environ.get("WAIT_DB_TIMEOUT", "120"))

start = time.time()
while time.time() - start < timeout:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[wait-for-db] {host}:{port} 就绪")
            sys.exit(0)
    except OSError:
        time.sleep(1)

print(f"[wait-for-db] 等待 {host}:{port} 超时", file=sys.stderr)
sys.exit(1)
