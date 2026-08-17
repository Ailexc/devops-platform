import asyncio
import logging
import random

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult

logger = logging.getLogger(__name__)


class EC2StateChangeHandler(BaseEventHandler):
    """EC2 实例状态变更事件"""

    event_type_pattern = "aws.ec2.*"

    display = {
        "events": [
            {"type": "aws.ec2.state-change", "desc": "实例状态变更（启动/停止/重启）"},
            {"type": "aws.ec2.instance-created", "desc": "新 EC2 实例创建完成"},
            {"type": "aws.ec2.instance-terminated", "desc": "EC2 实例终止"},
            {"type": "aws.ec2.spot-instance-interrupted", "desc": "竞价实例中断通知"},
        ],
        "schema": {
            "instance_id": {"type": "string", "required": True, "desc": "EC2 实例 ID", "example": "i-0abcd1234"},
            "state": {"type": "string", "required": True, "desc": "实例目标状态", "example": "running"},
            "region": {"type": "string", "required": False, "default": "us-east-1", "desc": "AWS 区域", "example": "ap-northeast-1"},
            "instance_type": {"type": "string", "required": False, "desc": "实例规格", "example": "t3.medium"},
        },
        "example": {
            "instance_id": "i-0abcd1234",
            "state": "running",
            "region": "ap-northeast-1",
            "instance_type": "t3.medium",
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        delay = random.uniform(0.3, 1.0)
        await asyncio.sleep(delay)

        state = event.raw_payload.get("state", "running")
        instance_id = event.raw_payload.get("instance_id", event.resource_id)

        logger.info("EC2 %s → %s (processed in %.2fs)", instance_id, state, delay)
        return HandlerResult(
            success=True,
            message=f"EC2 instance {instance_id} state changed to {state}",
            data={
                "service": "ec2",
                "instance_id": instance_id,
                "state": state,
                "region": event.raw_payload.get("region", "us-east-1"),
                "processed_delay": round(delay, 2),
            },
        )
