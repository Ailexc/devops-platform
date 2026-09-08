import asyncio
import logging
import time
from datetime import datetime, timezone

from celery import shared_task
from django.db import transaction

from apps.event_store.models import Event, EventLog, EventStatus
from core.exceptions import PermanentError, TransientError
from core.router import registry
from core.handler import BaseEventHandler

logger = logging.getLogger(__name__)


def _run_async_handler(handler: BaseEventHandler, event: Event):
    """安全地运行 async handler（兼容 eager 模式）"""
    try:
        return asyncio.run(handler.handle(event))
    except RuntimeError:
        # 已在事件循环中（task_always_eager 模式下从 async view 调用）
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(handler.handle(event))


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=4,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=60,
    time_limit=120,
)
def process_event(self, event_id: str):
    """处理事件的 Celery 任务"""
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            logger.error("Event %s not found", event_id)
            return

        if event.status == EventStatus.PROCESSING:
            logger.warning("Event %s is already being processed", event_id)
            return

        # 幂等性：已完成的事件跳过
        if event.status == EventStatus.COMPLETED:
            logger.info("Event %s already completed, skipping", event_id)
            return

        # 标记处理中
        _start_time = time.monotonic()
        event.status = EventStatus.PROCESSING
        event.worker_id = self.request.hostname or "unknown"
        event.save(update_fields=["status", "worker_id"])
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.PROCESSING,
            detail={
                "worker": event.worker_id,
                "celery_task_id": self.request.id,
                "queue": getattr(self.request, "delivery_info", {}).get("routing_key", "celery"),
                "retries": self.request.retries,
            },
        )

    try:
        # 路由到 Handler
        handler_cls = registry.resolve(event.event_type)
        handler: BaseEventHandler = handler_cls()

        # 记录路由匹配
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.ROUTED,
            detail={"handler": handler_cls.__name__, "event_type": event.event_type},
        )

        # 执行 Handler（async → sync）
        _exec_start = time.monotonic()
        result = _run_async_handler(handler, event)
        _duration_ms = round((time.monotonic() - _exec_start) * 1000)

        if result.success:
            handler.on_success(event, result, duration_ms=_duration_ms)
        else:
            raise TransientError(result.message)

    except PermanentError as exc:
        _move_to_dlq(event, exc)

    except TransientError as exc:
        _handle_retry(self, event, exc)

    except Exception as exc:
        _handle_retry(self, event, exc)

    except TransientError as exc:
        _handle_retry(self, event, exc)

    except Exception as exc:
        _handle_retry(self, event, exc)


def _move_to_dlq(event: Event, exc: Exception) -> None:
    """将事件移入死信队列"""
    event.status = EventStatus.DLQ
    event.error_message = str(exc)[:1024]
    event.save(update_fields=["status", "error_message"])
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.DLQ,
        detail={"error": str(exc)[:500], "reason": "permanent"},
    )
    logger.error("Event %s moved to DLQ: %s", event.id, exc)


def _handle_retry(task, event: Event, exc: Exception) -> None:
    """处理重试逻辑"""
    event.retry_count += 1
    event.error_message = str(exc)[:1024]
    event.status = EventStatus.FAILED
    event.save(update_fields=["retry_count", "error_message", "status"])
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.FAILED,
        detail={"error": str(exc)[:500], "retry_count": event.retry_count, "max_retries": event.max_retries},
    )
    if event.retry_count < event.max_retries:
        countdown = min(2**event.retry_count * 4, 300)
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.RETRYING,
            detail={
                "countdown_s": countdown,
                "retry_count": event.retry_count,
                "max_retries": event.max_retries,
                "error": str(exc)[:300],
            },
        )
        logger.warning(
            "Event %s failed (retry %d/%d), next in %ds: %s",
            event.id, event.retry_count, event.max_retries, countdown, exc,
        )
        raise task.retry(exc=exc, countdown=countdown)
    else:
        # 重试耗尽 → 死信
        event.status = EventStatus.DLQ
        event.save(update_fields=["status"])
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.DLQ,
            detail={"error": str(exc)[:500], "reason": "retries_exhausted", "total_retries": event.retry_count},
        )
        logger.error("Event %s moved to DLQ (retries exhausted): %s", event.id, exc)
