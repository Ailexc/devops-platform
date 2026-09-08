"""API 请求 / 响应模型（backend ↔ executor 契约）"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """一次执行请求（由 backend 提交）"""

    op: str = Field(
        ...,
        description="操作类型: build / deploy / pods / rollback / scale / restart / canary / blue_green",
    )
    namespace: Optional[str] = "release-demo"
    name: Optional[str] = None
    image: Optional[str] = None
    replicas: Optional[int] = 1
    env_vars: Optional[Dict[str, str]] = None
    labels: Optional[Dict[str, str]] = None
    version: Optional[str] = None
    release_no: Optional[str] = None
    stage: Optional[str] = None
    target_port: Optional[int] = 8080
    node_port: Optional[int] = None
    canary_percent: Optional[int] = 10
    canary_replicas: Optional[int] = 1
    params: Optional[Dict[str, Any]] = None


class LogEntry(BaseModel):
    index: int
    ts: str
    level: str
    message: str


class ExecutionStatus(BaseModel):
    id: str
    op: str
    status: str  # running / success / failed
    created_at: str
    finished_at: Optional[str] = None
    logs: List[LogEntry] = []
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
