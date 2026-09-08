import asyncio
import logging
import random

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult

logger = logging.getLogger(__name__)


class RDSEventHandler(BaseEventHandler):
    """RDS 数据库事件"""

    event_type_pattern = "aws.rds.*"

    display = {
        "events": [
            {"type": "aws.rds.instance-created", "desc": "新 RDS 实例创建"},
            {"type": "aws.rds.backup-completed", "desc": "自动备份完成"},
            {"type": "aws.rds.failover", "desc": "主备故障转移"},
            {"type": "aws.rds.instance-resized", "desc": "实例规格扩缩容"},
            {"type": "aws.rds.maintenance", "desc": "维护事件"},
        ],
        "schema": {
            "db_instance": {"type": "string", "required": True, "desc": "RDS 实例标识符", "example": "db-prod-01"},
            "category": {"type": "string", "required": True, "desc": "事件分类", "example": "backup"},
            "region": {"type": "string", "required": False, "default": "us-east-1", "desc": "AWS 区域", "example": "eu-west-1"},
            "storage": {"type": "integer", "required": False, "desc": "存储容量 GB", "example": 500},
        },
        "example": {
            "db_instance": "db-prod-01",
            "category": "backup",
            "region": "eu-west-1",
            "storage": 500,
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        # RDS 事件一般较慢
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)

        db_id = event.raw_payload.get("db_instance", event.resource_id)
        category = event.raw_payload.get("category", "notification")

        logger.info("RDS %s [%s] (processed in %.2fs)", db_id, category, delay)
        return HandlerResult(
            success=True,
            message=f"RDS {db_id} event processed",
            data={
                "service": "rds",
                "db_instance": db_id,
                "category": category,
                "region": event.raw_payload.get("region", "us-east-1"),
                "processed_delay": round(delay, 2),
            },
        )
