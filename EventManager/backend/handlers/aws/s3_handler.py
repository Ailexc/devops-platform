import asyncio
import logging
import random

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult

logger = logging.getLogger(__name__)


class S3NotificationHandler(BaseEventHandler):
    """S3 对象操作事件"""

    event_type_pattern = "aws.s3.*"

    display = {
        "events": [
            {"type": "aws.s3.object-created", "desc": "对象上传/创建"},
            {"type": "aws.s3.object-deleted", "desc": "对象删除"},
            {"type": "aws.s3.object-restored", "desc": "对象从归档恢复"},
            {"type": "aws.s3.bucket-created", "desc": "新存储桶创建"},
        ],
        "schema": {
            "bucket": {"type": "string", "required": True, "desc": "S3 存储桶名称", "example": "my-app-data"},
            "object_key": {"type": "string", "required": True, "desc": "对象键值（路径）", "example": "uploads/2026/07/report.pdf"},
            "action": {"type": "string", "required": True, "desc": "操作类型", "example": "PUT"},
            "size": {"type": "integer", "required": False, "desc": "对象大小（字节）", "example": 1048576},
        },
        "example": {
            "bucket": "my-app-data",
            "object_key": "uploads/2026/07/report.pdf",
            "action": "PUT",
            "size": 1048576,
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        delay = random.uniform(0.2, 0.8)
        await asyncio.sleep(delay)

        bucket = event.raw_payload.get("bucket", "unknown-bucket")
        obj_key = event.raw_payload.get("object_key", "unknown")
        action = event.raw_payload.get("action", "PUT")

        logger.info("S3 %s %s %s (processed in %.2fs)", bucket, action, obj_key, delay)
        return HandlerResult(
            success=True,
            message=f"S3 {action} {bucket}/{obj_key}",
            data={
                "service": "s3",
                "bucket": bucket,
                "object_key": obj_key,
                "action": action,
                "size": event.raw_payload.get("size", 1024),
                "processed_delay": round(delay, 2),
            },
        )
