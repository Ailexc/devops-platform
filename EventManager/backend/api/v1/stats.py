import logging
from datetime import timedelta

from django.db.models import Avg, F, Count
from django.db.models.functions import TruncHour
from django.utils import timezone
from ninja import Router

from api.schemas.event import StatsOut
from apps.event_store.models import Event, EventLog, EventStatus

logger = logging.getLogger(__name__)

router = Router()


@router.get("", response=StatsOut)
def get_stats(request):
    """事件统计概览"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    total = Event.objects.count()
    by_status = dict(
        Event.objects.values("status").annotate(count=Count("id")).values_list("status", "count")
    )
    recent = Event.objects.filter(received_at__gte=one_hour_ago)
    recent_total = recent.count()
    recent_success = recent.filter(status=EventStatus.COMPLETED).count()
    success_rate = (recent_success / recent_total * 100) if recent_total > 0 else 0.0
    duration_avg = recent.filter(
        processed_at__isnull=False, status=EventStatus.COMPLETED
    ).annotate(
        duration=Avg(F("processed_at") - F("received_at"))
    ).aggregate(avg=Avg("duration"))
    avg_seconds = duration_avg["avg"].total_seconds() if duration_avg.get("avg") else None
    return StatsOut(
        total=total,
        by_status=by_status,
        success_rate=round(success_rate, 2),
        avg_duration=round(avg_seconds, 2) if avg_seconds else None,
        p99_duration=None,
        queue_depth=by_status.get("pending", 0) + by_status.get("processing", 0),
    )


@router.get("/queues", response=list[dict])
def queue_stats(request):
    """各队列深度（用事件状态模拟队列深度）"""
    status_map = [
        ("events", EventStatus.PENDING, "主队列"),
        ("events.high", "processing", "高优处理中"),
        ("events.retry", EventStatus.FAILED, "重试队列"),
        ("events.dlq", EventStatus.DLQ, "死信队列"),
        ("events.completed", EventStatus.COMPLETED, "已完成"),
    ]
    result = []
    for name, status, label in status_map:
        count = Event.objects.filter(status=status).count()
        result.append({"name": name, "label": label, "depth": count})
    return result


@router.get("/workers", response=dict)
def worker_stats(request):
    """Worker 状态概览（真实数据）"""
    from config.celery_app import app

    try:
        # 通过 Celery 控制命令获取 worker 信息
        inspect = app.control.inspect(timeout=2.0)

        # 获取活跃任务
        active = inspect.active() or {}
        # 获取 Worker 统计信息
        stats = inspect.stats() or {}
        # 获取心跳信息
        ping = inspect.ping() or {}

        total_workers = len(stats)
        online_workers = len(ping)

        # 计算活跃任务数
        active_tasks = sum(len(tasks) for tasks in active.values())

        # 构建 worker 列表
        workers = []
        for worker_id, stat_info in stats.items():
            is_online = worker_id in ping
            workers.append({
                "id": worker_id,
                "status": "online" if is_online else "offline",
                "hostname": stat_info.get("hostname", worker_id),
                "active_tasks": len(active.get(worker_id, [])),
                "pool": stat_info.get("pool", {}).get("implementation", "unknown"),
                "concurrency": stat_info.get("pool", {}).get("max-concurrency", 0),
            })

        # 排队任务数从数据库查询
        pending = Event.objects.filter(status=EventStatus.PENDING).count()

        return {
            "total": total_workers,
            "online": online_workers,
            "active_tasks": active_tasks,
            "queued_tasks": pending,
            "workers": workers,
        }

    except Exception as exc:
        logger.warning("获取 Worker 状态失败: %s", exc)
        # 降级：从数据库查询基本信息
        processing = Event.objects.filter(status=EventStatus.PROCESSING).count()
        pending = Event.objects.filter(status=EventStatus.PENDING).count()
        return {
            "total": 0,
            "online": 0,
            "active_tasks": processing,
            "queued_tasks": pending,
            "workers": [],
        }


@router.get("/throughput", response=list[dict])
def throughput_stats(request):
    """过去 24 小时每小时事件吞吐量"""
    day_ago = timezone.now() - timedelta(hours=24)
    hourly = (
        Event.objects
        .filter(received_at__gte=day_ago)
        .annotate(hour=TruncHour("received_at"))
        .values("hour", "status")
        .annotate(count=Count("id"))
        .order_by("hour")
    )
    # 整理为按小时聚合
    hour_buckets: dict[str, dict] = {}
    for row in hourly:
        hour_key = row["hour"].strftime("%Y-%m-%d %H:00")
        if hour_key not in hour_buckets:
            hour_buckets[hour_key] = {"hour": hour_key, "total": 0, "completed": 0, "failed": 0, "other": 0}
        hour_buckets[hour_key]["total"] += row["count"]
        if row["status"] == EventStatus.COMPLETED:
            hour_buckets[hour_key]["completed"] += row["count"]
        elif row["status"] in (EventStatus.FAILED, EventStatus.DLQ):
            hour_buckets[hour_key]["failed"] += row["count"]
        else:
            hour_buckets[hour_key]["other"] += row["count"]
    return sorted(hour_buckets.values(), key=lambda x: x["hour"])


@router.get("/recent-failures", response=list[dict])
def recent_failures(request):
    """最近失败事件"""
    limit = int(request.GET.get("limit", 5))
    events = (
        Event.objects
        .filter(status__in=[EventStatus.FAILED, EventStatus.DLQ])
        .order_by("-received_at")[:limit]
    )
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "status": e.status,
            "error_message": e.error_message[:100],
            "retry_count": e.retry_count,
            "max_retries": e.max_retries,
            "received_at": e.received_at.isoformat(),
        }
        for e in events
    ]
