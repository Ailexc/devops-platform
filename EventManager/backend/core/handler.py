import abc
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from apps.event_store.models import Event, EventLog, EventStatus
from core.exceptions import EventError, PermanentError

logger = logging.getLogger(__name__)


@dataclass
class HandlerResult:
    """Handler 处理结果"""

    success: bool
    message: str = ""
    data: dict | None = None


class BaseEventHandler(abc.ABC):
    """事件处理器抽象基类"""

    # 匹配的事件类型模式 (支持通配符 * 和 ?)
    event_type_pattern: str = "*"

    @abc.abstractmethod
    async def handle(self, event: Event) -> HandlerResult:
        """处理事件 - 子类实现具体业务逻辑（async）"""
        ...

    def on_success(self, event: Event, result: HandlerResult, duration_ms: int = 0) -> None:
        """处理成功回调（sync）"""
        event.status = EventStatus.COMPLETED
        event.processed_at = datetime.now(timezone.utc)
        event.handler = self.__class__.__name__
        event.save(update_fields=["status", "processed_at", "handler"])
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.COMPLETED,
            detail={"result": result.message, "data": result.data, "duration_ms": duration_ms},
        )
        logger.info("Event %s processed successfully by %s (%dms)", event.id, self.__class__.__name__, duration_ms)

    def on_failure(self, event: Event, exc: Exception) -> None:
        """处理失败回调（sync）"""
        is_retryable = isinstance(exc, EventError) and exc.retryable
        if not isinstance(exc, EventError):
            is_retryable = True
        event.error_message = str(exc)[:1024]
        if is_retryable and event.retry_count < event.max_retries:
            event.status = EventStatus.FAILED
            event.save(update_fields=["status", "error_message"])
            EventLog.objects.create(
                event=event,
                action=EventLog.Action.FAILED,
                detail={"error": str(exc)[:500], "retryable": True},
            )
            logger.warning(
                "Event %s failed (retry %d/%d): %s",
                event.id, event.retry_count, event.max_retries, exc,
            )
        else:
            event.status = EventStatus.DLQ if not is_retryable else EventStatus.DLQ
            event.save(update_fields=["status", "error_message"])
            EventLog.objects.create(
                event=event,
                action=EventLog.Action.DLQ,
                detail={"error": str(exc)[:500], "reason": "retries_exhausted" if is_retryable else "permanent"},
            )
            logger.error(
                "Event %s moved to DLQ (retries exhausted): %s", event.id, exc,
            )
