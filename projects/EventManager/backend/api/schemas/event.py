from datetime import datetime
from uuid import UUID
from typing import Optional
from ninja import Schema, ModelSchema
from apps.event_store.models import Event, EventLog, EventStatus


class EventOut(Schema):
    id: UUID
    event_type: str
    source: str
    detail_type: str
    resource_id: str
    raw_payload: dict
    status: str
    trace_id: UUID
    retry_count: int
    max_retries: int
    handler: str
    worker_id: str
    error_message: str
    received_at: datetime
    processed_at: Optional[datetime] = None


class EventCreate(Schema):
    event_type: str
    source: str = ""
    detail_type: str = ""
    resource_id: str = ""
    raw_payload: dict = {}
    max_retries: int = 5


class EventListOut(Schema):
    items: list[EventOut]
    total: int
    page: int
    page_size: int


class EventLogOut(Schema):
    id: int
    action: str
    detail: dict
    created_at: datetime


class EventStatusUpdate(Schema):
    status: str


class RetryRequest(Schema):
    force: bool = False


class DlqReplayRequest(Schema):
    event_ids: list[UUID]


class StatsOut(Schema):
    total: int
    by_status: dict[str, int]
    success_rate: float
    avg_duration: Optional[float] = None
    p99_duration: Optional[float] = None
    queue_depth: int = 0
