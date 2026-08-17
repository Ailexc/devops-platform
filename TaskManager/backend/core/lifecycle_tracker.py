"""
Lifecycle tracker — append lifecycle events to ExecutionRecord.

Usage:
    from core.lifecycle_tracker import LifecycleTracker

    # In API view (task created & dispatched):
    tracker = LifecycleTracker(celery_task_id=task_id)
    tracker.append("created", "任务创建", "API 收到请求")
    tracker.append("dispatched", "任务派发", f"queue: {queue}")

    # In Celery task signals (worker received, retrying, etc.):
    tracker = LifecycleTracker.from_celery_task(task_id)
    tracker.append("received", "Worker 接收", f"worker: {worker}")
"""

from datetime import datetime


# Event definitions: (event_key, label, icon, color)
EVENT_DEFS = {
    "created":    ("📥 任务创建",   "var(--blue)"),
    "dispatched": ("🚀 任务派发",   "var(--purple)"),
    "received":   ("🏃 Worker 接收", "var(--teal)"),
    "retrying":   ("⚠️ 自动重试",   "var(--orange)"),
    "running":    ("⚙️ 开始执行",   "var(--blue)"),
    "completed":  ("✅ 执行完成",   "var(--teal)"),
    "failed":     ("❌ 执行失败",   "#c0392b"),
    "timeout":    ("⏰ 执行超时",   "var(--orange)"),
}


class LifecycleTracker:
    """Append lifecycle events to an ExecutionRecord by celery_task_id."""

    def __init__(self, celery_task_id: str):
        self.celery_task_id = celery_task_id

    @classmethod
    def from_record(cls, record) -> "LifecycleTracker":
        """Create tracker from an ExecutionRecord instance."""
        tracker = cls(record.celery_task_id)
        return tracker

    def append(self, event: str, label: str = "", detail: str = ""):
        """Append a lifecycle event to the record."""
        from api.history.models import ExecutionRecord

        # filter().first()：对历史遗留重复记录健壮，避免 MultipleObjectsReturned
        record = (
            ExecutionRecord.objects.filter(celery_task_id=self.celery_task_id)
            .order_by("-started_at")
            .first()
        )
        if not record:
            return

        event_label, color = EVENT_DEFS.get(event, (event, "var(--t2)"))
        if label:
            event_label = f"{event_label.split(' ')[0]} {label}"

        now = datetime.now()
        entry = {
            "ts": now.strftime("%H:%M:%S."),
            "ts_ms": f"{now.strftime('%H:%M:%S')}.{now.microsecond // 1000:03d}",
            "event": event,
            "label": event_label,
            "detail": detail,
            "color": color,
        }

        events = record.lifecycle_events or []
        events.append(entry)
        record.lifecycle_events = events
        record.save(update_fields=["lifecycle_events"])

    def update_last(self, **kwargs):
        """Update the last event in the list (e.g. add detail after completion)."""
        from api.history.models import ExecutionRecord

        record = (
            ExecutionRecord.objects.filter(celery_task_id=self.celery_task_id)
            .order_by("-started_at")
            .first()
        )
        if not record:
            return

        events = record.lifecycle_events or []
        if events:
            events[-1].update(kwargs)
            record.lifecycle_events = events
            record.save(update_fields=["lifecycle_events"])
