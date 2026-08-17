import asyncio
import logging

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult
from core.exceptions import TransientError

logger = logging.getLogger(__name__)


class EchoHandler(BaseEventHandler):
    """回显 Handler - 用于 Demo 测试"""
    event_type_pattern = "*"

    display = {
        "events": [
            {"type": "echo.test", "desc": "基础回显测试"},
            {"type": "echo.error", "desc": "模拟处理失败（测试重试/DLQ）"},
            {"type": "echo.timeout", "desc": "模拟处理超时"},
        ],
        "schema": {
            "message": {"type": "string", "required": False, "desc": "回显消息", "example": "Hello World"},
            "simulate_error": {"type": "boolean", "required": False, "desc": "设为 true 模拟处理失败", "example": False},
            "simulate_timeout": {"type": "boolean", "required": False, "desc": "设为 true 模拟超时", "example": False},
        },
        "example": {
            "message": "Hello World",
            "simulate_error": False,
            "simulate_timeout": False,
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        """模拟事件处理：短暂延迟后返回成功"""
        # 模拟处理耗时
        delay = 0.5
        if event.raw_payload.get("simulate_timeout"):
            delay = 5.0  # 模拟超时
        if event.raw_payload.get("simulate_error"):
            raise TransientError("Simulated transient error for testing")

        await asyncio.sleep(delay)

        logger.info("EchoHandler processed event %s (type=%s)", event.id, event.event_type)
        return HandlerResult(
            success=True,
            message=f"Echo processed in {delay}s",
            data={
                "echo": True,
                "event_type": event.event_type,
                "source": event.source,
                "delay": delay,
            },
        )
