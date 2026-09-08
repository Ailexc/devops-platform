"""
maintenance_tasks — 运维维护任务（Celery Beat 调度）。

- cleanup_old_records: 执行明细保留 3 天、聚合表保留 30 天
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="core.maintenance_tasks.cleanup_old_records")
def cleanup_old_records():
    """每日清理：执行记录保留 3 天，DailyTaskStat 保留 30 天。"""
    from datetime import timedelta

    from django.utils import timezone

    from api.history.models import DailyTaskStat, ExecutionRecord

    cutoff = timezone.now() - timedelta(days=3)
    deleted_records, _ = ExecutionRecord.objects.filter(started_at__lt=cutoff).delete()

    stat_cutoff = timezone.localdate() - timedelta(days=30)
    deleted_stats, _ = DailyTaskStat.objects.filter(stat_date__lt=stat_cutoff).delete()

    logger.info(f"cleanup_old_records: deleted {deleted_records} records, {deleted_stats} daily stats")
    return {"deleted_records": deleted_records, "deleted_stats": deleted_stats}
