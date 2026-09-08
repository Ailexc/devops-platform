"""
release-executor —— 发布系统执行端（模拟 spug-lambda）

独立服务，负责所有真实的 K8s / 容器操作。只接受 backend 用私钥签发的请求
（见 app/auth.py 的方案B：签名 + 请求内容绑定），后端进程不再直接操作集群。

启动:  uvicorn app.main:app --host 0.0.0.0 --port 8765
API:   http://localhost:8765/docs
"""

import asyncio
import json
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from .auth import verify_backend_request
from .config import SSE_HEARTBEAT_INTERVAL
from .runner import k8s, start_execution
from .schemas import ExecutionRequest
from .store import create_execution, get_execution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("executor")

app = FastAPI(
    title="release-executor",
    description="发布系统执行端（模拟 spug-lambda）：执行所有真实的 K8s / 容器操作，"
                "仅接受 backend 私钥签发的请求",
    version="0.1.0",
)


# ── 集群健康检查（无需凭证，仅供运维探测）──────────────
@app.get("/api/v1/cluster/health")
def cluster_health():
    return {
        "code": 200,
        "data": {"simulate": k8s.is_simulating(), "message": k8s.describe()},
    }


# ── 提交执行（异步：立即返回 execution_id，后台执行）────
@app.post("/api/v1/executions", status_code=202, dependencies=[Depends(verify_backend_request)])
async def submit_execution(req: ExecutionRequest):
    ex = create_execution(req.op, req.params or {})
    start_execution(ex.id)
    logger.info(f"收到执行请求: op={req.op} execution_id={ex.id}")
    return {"code": 202, "data": {"execution_id": ex.id, "status": "running", "op": req.op}}


# ── 查询执行状态 ────────────────────────────────────────
@app.get("/api/v1/executions/{exec_id}", dependencies=[Depends(verify_backend_request)])
def execution_status(exec_id: str):
    ex = get_execution(exec_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return {
        "code": 200,
        "data": {
            "id": ex.id,
            "op": ex.op,
            "status": ex.status,
            "created_at": ex.created_at,
            "finished_at": ex.finished_at,
            "result": ex.result,
            "error": ex.error,
            "logs": ex.logs_after(-1),
        },
    }


# ── SSE 日志流 ──────────────────────────────────────────
@app.get("/api/v1/executions/{exec_id}/logs", dependencies=[Depends(verify_backend_request)])
async def execution_logs(exec_id: str, request: Request):
    ex = get_execution(exec_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    logger.info(f"SSE 日志流已建立: {exec_id}")

    async def event_gen():
        last_index = -1
        while True:
            if await request.is_disconnected():
                logger.info(f"SSE 日志流断开: {exec_id}")
                break

            # 增量推送新日志
            for entry in ex.logs_after(last_index):
                last_index = entry["index"]
                yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"

            # 执行结束：推送 done 事件后关闭
            if ex.status != "running":
                done = {
                    "event": "done",
                    "status": ex.status,
                    "result": ex.result,
                    "error": ex.error,
                }
                yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
                break

            # 无新日志：等待新日志事件，超时则发心跳
            if ex.wait_new_log(timeout=SSE_HEARTBEAT_INTERVAL):
                ex.clear_new_log_flag()
                continue
            yield ": heartbeat\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
