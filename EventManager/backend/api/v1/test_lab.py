"""
测试模块 API —— 人工触发 Demo 任务
"""

import json
import logging
import os
import uuid
from pathlib import Path

from ninja import Router
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from kombu.exceptions import OperationalError

from workers.demo_tasks import fetch_and_process, generate_report

logger = logging.getLogger(__name__)
router = Router()

# ─── 任务注册表 ──────────────────────────────────────

TASK_REGISTRY = {
    "fast": {
        "id": "fast",
        "name": "⚡ 快任务 — API 数据爬取",
        "description": "调用 JSONPlaceholder 公开 API 爬取帖子数据，提取关键字段并统计词频，结果写入 JSON 文件",
        "duration": "~2-5 秒/批",
        "task_fn": fetch_and_process,
        "max_count": 50,
        "default_count": 1,
    },
    "slow": {
        "id": "slow",
        "name": "🐢 慢任务 — 报告生成",
        "description": "模拟数据分析流程：读取数据源 → 数据清洗 → 统计计算 → 生成报告，支持实时进度上报",
        "duration": "~3-8 秒/条",
        "task_fn": generate_report,
        "max_count": 20,
        "default_count": 1,
    },
}


# ─── Schemas ──────────────────────────────────────

class TriggerRequest(BaseModel):
    task_id: str = Field(..., description="任务 ID: fast 或 slow")
    count: int = Field(1, ge=1, le=50, description="触发数量")


class TaskInfo(BaseModel):
    id: str
    name: str
    description: str
    duration: str
    max_count: int
    default_count: int


class TriggerResponse(BaseModel):
    task_id: str
    celery_task_id: str
    count: int
    batch_id: str
    message: str


class TaskStatusResponse(BaseModel):
    celery_task_id: str
    state: str  # PENDING / PROGRESS / SUCCESS / FAILURE
    meta: dict | None = None
    result: dict | None = None
    event_ids: list[str] = []


# ─── API ──────────────────────────────────────

@router.get("/tasks", response=list[TaskInfo])
def list_demo_tasks(request):
    """列出所有可用的测试任务"""
    return [
        TaskInfo(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            duration=t["duration"],
            max_count=t["max_count"],
            default_count=t["default_count"],
        )
        for t in TASK_REGISTRY.values()
    ]


@router.post("/trigger", response=TriggerResponse)
def trigger_task(request, payload: TriggerRequest):
    """触发测试任务 - 每个 count 触发一个独立的 Celery 任务"""
    if payload.task_id not in TASK_REGISTRY:
        return 400, {"detail": f"未知任务: {payload.task_id}，可用: {list(TASK_REGISTRY.keys())}"}

    task_def = TASK_REGISTRY[payload.task_id]
    task_fn = task_def["task_fn"]

    # 限制数量
    count = min(payload.count, task_def["max_count"])

    # 生成批次 ID，用于标识这次下发的所有任务
    batch_id = f"BATCH-{uuid.uuid4().hex[:8]}"

    # 触发 N 个独立的任务，每个任务处理 1 个批次
    task_ids = []
    for i in range(count):
        try:
            # 异步投递（broker 不可用时降级为同步执行）
            result = task_fn.delay(batch=i + 1, total=count, batch_id=batch_id)
            task_ids.append(result.id)
        except (OperationalError, ConnectionRefusedError, OSError) as exc:
            logger.warning("Broker 不可用，降级为同步执行: %s", exc)
            result = task_fn.apply(args=[], kwargs={"batch": i + 1, "total": count, "batch_id": batch_id})
            task_ids.append(result.id)

    return TriggerResponse(
        task_id=payload.task_id,
        celery_task_id=task_ids[0] if task_ids else "",
        count=count,
        batch_id=batch_id,
        message=f"已触发 {count} 个独立任务，批次号: {batch_id}",
    )


@router.get("/status/{celery_task_id}", response=TaskStatusResponse)
def get_task_status(request, celery_task_id: str):
    """查询任务执行状态（支持进度上报）"""
    result = AsyncResult(celery_task_id)

    response = TaskStatusResponse(
        celery_task_id=celery_task_id,
        state=result.state,
    )

    if result.state == "PROGRESS":
        response.meta = result.info
    elif result.state == "SUCCESS":
        response.result = result.result
    elif result.state == "FAILURE":
        response.meta = {"error": str(result.result)}
    elif result.state == "PENDING":
        # 同步执行（apply）完成后 AsyncResult 找不到结果，视为已完成
        if result._result is not None:
            response.state = "SUCCESS"
            response.result = result._result

    # 查找关联的 Event 记录
    if response.result and isinstance(response.result, dict):
        ev_ids = response.result.get("event_ids", [])
        response.event_ids = ev_ids

    return response


# ─── 产物预览 ──────────────────────────────────────

class FilePreviewResponse(BaseModel):
    filename: str
    size: int
    content: str


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(Path(__file__).resolve().parent.parent.parent.parent / "output")))


@router.get("/preview", response=FilePreviewResponse)
def preview_output_file(request, filename: str):
    """预览 output 目录下的文件内容"""
    # 安全检查：只允许读取 output 目录下的文件，防止路径穿越
    file_path = (OUTPUT_DIR / filename).resolve()
    if not str(file_path).startswith(str(OUTPUT_DIR.resolve())):
        return 400, {"detail": "非法文件路径"}
    if not file_path.exists():
        return 404, {"detail": f"文件不存在: {filename}"}

    # 限制预览大小（最大 500KB）
    size = file_path.stat().st_size
    if size > 500 * 1024:
        content = file_path.read_text(encoding="utf-8")[:500 * 1024] + "\n... (文件过大，已截断)"
    else:
        content = file_path.read_text(encoding="utf-8")

    return FilePreviewResponse(filename=filename, size=size, content=content)
