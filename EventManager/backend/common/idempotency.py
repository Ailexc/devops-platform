"""
幂等性保障
基于事件 ID 的去重，防止重复处理。
"""
import logging
from contextlib import contextmanager

from django.db import IntegrityError, transaction

from apps.event_store.models import Event, EventLog, EventStatus

logger = logging.getLogger(__name__)


def is_processed(event_id: str) -> bool:
    """检查事件是否已经被处理"""
    try:
        event = Event.objects.get(id=event_id)
        return event.status == EventStatus.COMPLETED
    except Event.DoesNotExist:
        return False


def mark_processing(event_id: str) -> bool:
    """尝试标记事件为处理中，返回是否成功获取锁"""
    try:
        with transaction.atomic():
            event = Event.objects.select_for_update(nowait=True).get(id=event_id)
            if event.status == EventStatus.COMPLETED:
                return False
            event.status = EventStatus.PROCESSING
            event.save(update_fields=["status"])
            return True
    except (Event.DoesNotExist, IntegrityError):
        return False
