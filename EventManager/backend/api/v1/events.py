import uuid
from datetime import datetime
from typing import Optional

from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from api.schemas.event import (
    EventCreate,
    EventListOut,
    EventLogOut,
    EventOut,
    DlqReplayRequest,
    RetryRequest,
)
from apps.event_store.models import Event, EventLog, EventStatus
from workers.tasks import process_event

router = Router()


@router.post("", response={201: EventOut})
def create_event(request, payload: EventCreate):
    """接收事件，返回 202 Accepted"""
    event = Event.objects.create(
        event_type=payload.event_type,
        source=payload.source or "api",
        detail_type=payload.detail_type,
        resource_id=payload.resource_id,
        raw_payload=payload.raw_payload,
        max_retries=payload.max_retries,
        status=EventStatus.PENDING,
    )
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.RECEIVED,
        detail={"source": payload.source or "api", "event_type": payload.event_type},
    )
    # 投递到 Celery 队列
    result = process_event.delay(str(event.id))
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.ENQUEUED,
        detail={"queue": "celery", "celery_task_id": str(result.id)},
    )
    return 201, event


@router.post("/batch", response={201: int})
def batch_create_events(request, payloads: list[EventCreate]):
    """批量投递事件"""
    events = []
    for p in payloads:
        event = Event.objects.create(
            event_type=p.event_type,
            source=p.source or "api",
            detail_type=p.detail_type,
            resource_id=p.resource_id,
            raw_payload=p.raw_payload,
            max_retries=p.max_retries,
            status=EventStatus.PENDING,
        )
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.RECEIVED,
            detail={"source": p.source},
        )
        process_event.delay(str(event.id))
        events.append(event)
    return 201, len(events)


@router.get("", response=EventListOut)
def list_events(
    request,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    search_field: Optional[str] = None,
):
    """事件列表，支持筛选和搜索

    search_field: all | id | event_type | resource_id | batch_id
    """
    qs = Event.objects.all()
    if status:
        qs = qs.filter(status=status)
    if event_type:
        qs = qs.filter(event_type__icontains=event_type)
    if source:
        qs = qs.filter(source=source)
    if search:
        search = search.strip()
        if search_field == "id":
            qs = qs.filter(Q(id__icontains=search))
        elif search_field == "event_type":
            qs = qs.filter(Q(event_type__icontains=search))
        elif search_field == "resource_id":
            qs = qs.filter(Q(resource_id__icontains=search))
        elif search_field == "batch_id":
            # 批次 ID 存于 raw_payload.batch_id
            qs = qs.filter(Q(raw_payload__batch_id__icontains=search))
        else:
            qs = qs.filter(
                Q(event_type__icontains=search)
                | Q(resource_id__icontains=search)
                | Q(id__icontains=search)
                | Q(raw_payload__batch_id__icontains=search)
            )
    total = qs.count()
    qs = qs[(page - 1) * page_size : page * page_size]
    items = [EventOut.from_orm(e) for e in qs]
    return EventListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{event_id}", response=EventOut)
def get_event(request, event_id: uuid.UUID):
    """事件详情"""
    event = get_object_or_404(Event, id=event_id)
    return event


@router.get("/{event_id}/logs", response=list[EventLogOut])
def get_event_logs(request, event_id: uuid.UUID):
    """事件处理日志/时间线"""
    event = get_object_or_404(Event, id=event_id)
    return list(event.logs.all())


@router.post("/{event_id}/retry", response=EventOut)
def retry_event(request, event_id: uuid.UUID, payload: RetryRequest = None):
    """手动重试事件"""
    event = get_object_or_404(Event, id=event_id)
    if event.status in (EventStatus.COMPLETED, EventStatus.PROCESSING):
        if not payload or not payload.force:
            return event  # 不允许重试已完成/处理中的事件
    # 重置状态
    event.status = EventStatus.PENDING
    event.retry_count = 0
    event.error_message = ""
    event.save(update_fields=["status", "retry_count", "error_message"])
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.RETRY_MANUAL,
        detail={"triggered_by": "manual", "previous_status": event.status},
    )
    result = process_event.delay(str(event.id))
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.ENQUEUED,
        detail={"queue": "celery", "celery_task_id": str(result.id), "trigger": "manual_retry"},
    )
    return event


@router.post("/dlq/replay", response=dict)
def replay_dlq(request, payload: DlqReplayRequest):
    """批量回放死信事件"""
    events = Event.objects.filter(id__in=payload.event_ids, status=EventStatus.DLQ)
    count = 0
    for event in events:
        event.status = EventStatus.PENDING
        event.retry_count = 0
        event.error_message = ""
        event.save(update_fields=["status", "retry_count", "error_message"])
        EventLog.objects.create(
            event=event,
            action=EventLog.Action.REPLAYED,
            detail={"triggered_by": "manual_replay"},
        )
        process_event.delay(str(event.id))
        count += 1
    return {"replayed": count}
