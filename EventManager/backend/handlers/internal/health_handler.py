import asyncio
import logging

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseEventHandler):
    """内部健康检查事件"""

    event_type_pattern = "internal.health"

    display = {
        "events": [
            {"type": "internal.health", "desc": "定时健康检查"},
        ],
        "schema": {
            "component": {"type": "string", "required": False, "default": "api", "desc": "被检查的组件名", "example": "celery-worker"},
            "check": {"type": "string", "required": False, "default": "ping", "desc": "检查类型", "example": "db-connectivity"},
        },
        "example": {
            "component": "celery-worker",
            "check": "ping",
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        await asyncio.sleep(0.05)

        check_type = event.raw_payload.get("check", "ping")
        component = event.raw_payload.get("component", "api")

        logger.info("Health check %s/%s OK", component, check_type)
        return HandlerResult(
            success=True,
            message=f"{component} {check_type} OK",
            data={
                "service": "health",
                "component": component,
                "check": check_type,
                "status": "healthy",
            },
        )
