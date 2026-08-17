"""
executor HTTP 客户端 —— backend 访问执行端的唯一入口

所有请求都携带私钥签发的服务间凭证（见 executor_auth.py），
executor 侧验签通过才会执行。
"""

import logging

import requests
from django.conf import settings

from .executor_auth import canonicalize, sign_request

logger = logging.getLogger(__name__)

EXECUTIONS_PATH = "/api/v1/executions"
STREAM_TIMEOUT = (10, 300)  # (连接超时, 读取超时)


def submit(op: str, params: dict) -> dict:
    """异步提交一次执行，返回 {execution_id, status, op}"""
    # params 嵌套在 params 字段里，避免 Pydantic 丢弃未定义字段
    payload = {"op": op, "params": params}
    body = canonicalize(payload)
    token = sign_request("POST", EXECUTIONS_PATH, body)
    resp = requests.post(
        f"{settings.EXECUTOR_URL}{EXECUTIONS_PATH}",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    logger.info(f"已提交执行: op={op} execution_id={data['execution_id']}")
    return data


def get_execution(exec_id: str) -> dict:
    """查询执行状态（含全部日志与结果）"""
    path = f"{EXECUTIONS_PATH}/{exec_id}"
    token = sign_request("GET", path, b"")
    resp = requests.get(
        f"{settings.EXECUTOR_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def stream_logs(exec_id: str):
    """
    消费 executor 的 SSE 日志流。

    逐条产出 JSON 事件：
      - {index, ts, level, message}  日志行
      - {event: "done", status, result, error}  执行结束信号
    """
    path = f"{EXECUTIONS_PATH}/{exec_id}/logs"
    token = sign_request("GET", path, b"")
    with requests.get(
        f"{settings.EXECUTOR_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=STREAM_TIMEOUT,
    ) as resp:
        resp.raise_for_status()
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            # SSE 数据帧: "data: {...}"
            if raw.startswith(":"):
                continue  # 心跳注释帧
            if raw.startswith("data:"):
                payload = raw[len("data:"):].strip()
                if payload:
                    yield payload
