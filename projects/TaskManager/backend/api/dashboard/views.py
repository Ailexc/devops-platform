from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response

from api.history.models import DailyTaskStat, ExecutionRecord
from core import metrics_service


def _last_days(n: int):
    today = timezone.localdate()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


@extend_schema(
    summary="大盘摘要",
    description="今日/7天/30天 任务统计、成功率、同步量、运行中任务、CMDB 资源总数（聚合表驱动）",
    responses={200: OpenApiTypes.OBJECT},
)
class DashboardStatsView(APIView):
    """GET /api/v1/dashboard/stats — 大盘摘要（聚合表驱动）。"""

    def get(self, request):
        today = timezone.localdate()
        week_ago = today - timedelta(days=6)
        month_ago = today - timedelta(days=29)

        # 今日
        today_stat = DailyTaskStat.objects.filter(stat_date=today).aggregate(
            total=Sum("total"), success=Sum("success"), failed=Sum("failed"), synced=Sum("synced_count")
        )
        # 7 天
        week_stat = DailyTaskStat.objects.filter(stat_date__gte=week_ago).aggregate(
            total=Sum("total"), success=Sum("success"), failed=Sum("failed"), synced=Sum("synced_count")
        )
        # 30 天累计
        month_stat = DailyTaskStat.objects.filter(stat_date__gte=month_ago).aggregate(
            total=Sum("total"), success=Sum("success"), failed=Sum("failed"), synced=Sum("synced_count")
        )

        def rate(stat):
            total = stat.get("total") or 0
            success = stat.get("success") or 0
            return f"{(success / total * 100):.1f}%" if total else "—"

        running_now = ExecutionRecord.objects.filter(status="running", parent__isnull=True).count()

        return Response({
            "today_tasks": today_stat.get("total") or 0,
            "success_rate_24h": rate(today_stat),
            "success_rate_7d": rate(week_stat),
            "weekly_total": week_stat.get("total") or 0,
            "monthly_total": month_stat.get("total") or 0,
            "cumulative_synced": month_stat.get("synced") or 0,
            "running_now": running_now,
            "pending_errors": today_stat.get("failed") or 0,
            "total_cmdb_resources": metrics_service.total_cmdb_resources(),
        })


@extend_schema(
    summary="Worker 池状态",
    description="真实 worker 池状态（Celery inspect）+ 负载",
    responses={200: OpenApiTypes.OBJECT},
)
class WorkerStatusView(APIView):
    """GET /api/v1/dashboard/workers — worker pool status."""

    def get(self, request):
        return Response(metrics_service.worker_status())


@extend_schema(
    summary="模块健康度",
    description="聚合表 30 天成功率 + 各模块最近同步新鲜度（真实数据）",
    responses={200: OpenApiTypes.OBJECT},
)
class ResourceHealthView(APIView):
    """GET /api/v1/dashboard/resource-health — 模块健康度（聚合表 30 天成功率）。"""

    def get(self, request):
        month_ago = timezone.localdate() - timedelta(days=29)
        rows = (
            DailyTaskStat.objects.filter(stat_date__gte=month_ago)
            .values("module")
            .annotate(total=Sum("total"), failed=Sum("failed"), synced=Sum("synced_count"))
        )
        modules = []
        for row in rows:
            total = row["total"] or 0
            failed = row["failed"] or 0
            rate = f"{((total - failed) / total * 100):.1f}%" if total else "—"
            modules.append({
                "name": row["module"],
                "rate": rate,
                "failed": failed,
                "total": total,
                "synced": row["synced"] or 0,
            })
        return Response({
            "modules": modules,
            "freshness": metrics_service.freshness_by_module(),
        })


@extend_schema(
    summary="7 天任务趋势",
    description="按天聚合的 7 天执行趋势（DailyTaskStat）",
    responses={200: OpenApiTypes.OBJECT},
)
class TaskTrendView(APIView):
    """GET /api/v1/dashboard/task-trend — 7 天执行趋势（按天，匹配日级任务节奏）。"""

    def get(self, request):
        days = _last_days(7)
        stats = {
            d: DailyTaskStat.objects.filter(stat_date=d).aggregate(
                total=Sum("total"), success=Sum("success"), failed=Sum("failed")
            )
            for d in days
        }
        return Response([
            {
                "date": d.strftime("%m-%d"),
                "total": stats[d].get("total") or 0,
                "success": stats[d].get("success") or 0,
                "failed": stats[d].get("failed") or 0,
            }
            for d in days
        ])


@extend_schema(
    summary="任务健康度排行",
    description="近 3 天失败 TOP 模块 + 耗时 TOP 任务",
    responses={200: OpenApiTypes.OBJECT},
)
class HealthRankingView(APIView):
    """GET /api/v1/dashboard/health-ranking — 任务健康度排行（失败 TOP / 耗时 TOP）。"""

    def get(self, request):
        cutoff = timezone.now() - timedelta(days=3)
        recent = ExecutionRecord.objects.filter(
            parent__isnull=True, started_at__gte=cutoff
        ).exclude(status="running")

        # 失败 TOP（按模块失败数）
        failed_rows = (
            recent.filter(status__in=["failed", "partial"])
            .values("module")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        # 耗时 TOP
        def _duration_secs(r):
            if not r.finished_at or not r.started_at:
                return 0
            return (r.finished_at - r.started_at).total_seconds()

        duration_top = [
            {"task": r.task_name, "target": r.target, "duration": r.duration}
            for r in sorted(
                recent.filter(status="success"),
                key=_duration_secs,
                reverse=True,
            )[:5]
        ]
        return Response({
            "top_failed_modules": list(failed_rows),
            "top_duration": duration_top,
        })


@extend_schema(
    summary="当前执行中任务",
    description="执行中任务列表 + 并发锁状态",
    responses={200: OpenApiTypes.OBJECT},
)
class CurrentRunningView(APIView):
    """GET /api/v1/dashboard/current — 当前执行中任务 + 锁状态。"""

    def get(self, request):
        from core.concurrency_lock import lock_manager

        running = list(
            ExecutionRecord.objects.filter(status="running", parent__isnull=True).order_by("-started_at")[:10]
        )
        return Response({
            "running": [
                {
                    "id": f"#{r.id:05d}",
                    "task": r.task_name,
                    "target": r.target,
                    "scope": r.scope,
                    "trigger": r.trigger,
                    "start": r.started_at.strftime("%H:%M:%S") if r.started_at else "-",
                }
                for r in running
            ],
            "locks": lock_manager.list_active(),
        })


@extend_schema(
    summary="最近事件",
    description="最近执行记录生成的事件流（失败→error / 运行中→warning / 成功→success）",
    responses={200: OpenApiTypes.OBJECT},
)
class RecentEventsView(APIView):
    """GET /api/v1/dashboard/recent-events — recent alerts & events (真实数据)。"""

    def get(self, request):
        return Response(metrics_service.recent_events(limit=10))


@extend_schema(
    summary="资源构成",
    description="CMDB 存储中各资源类型数量统计（真实数据）",
    responses={200: OpenApiTypes.OBJECT},
)
class ResourceBreakdownView(APIView):
    """GET /api/v1/dashboard/resource-breakdown — resource type counts (真实数据)。"""

    def get(self, request):
        return Response(metrics_service.cmdb_resource_stats()["breakdown"])


@extend_schema(
    summary="AWS 资源树",
    description="由 registry（能力层）+ AccountRegion（配置层）生成的真实资源树",
    responses={200: OpenApiTypes.OBJECT},
)
class AWSResourcesView(APIView):
    """GET /api/v1/dashboard/aws-resources — AWS account/region/resource tree (真实数据)。"""

    def get(self, request):
        return Response(metrics_service.aws_resource_tree())
