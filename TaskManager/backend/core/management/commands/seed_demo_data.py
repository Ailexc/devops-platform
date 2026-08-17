"""
seed_demo_data — 向内存演示存储和数据库中播种/刷新演示数据。

用法:
    python manage.py seed_demo_data          # 播种默认演示数据
    python manage.py seed_demo_data --reset  # 先清空再播种

说明:
    - 内存数据（Dashboard/Worker 等）：进程内存，重启后自动重新播种
    - 执行历史：写入 PostgreSQL，持久化保存
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.demo_store import demo_store

# ── 初始演示历史记录 ──────────────────────────────────────────────
SEED_HISTORY = [
    {"task_name": "生产-apne1 全量", "module": "AWS", "target": "生产 / apne1", "trigger": "Cron", "status": "success", "duration": "2m34s", "detail": "EC2↑5✏️3↓1, VPC不变"},
    {"task_name": "钉钉审批增量", "module": "内部", "target": "钉钉 OAPI", "trigger": "定时(15min)", "status": "success", "duration": "45s", "detail": "审批实例↑3✏️8"},
    {"task_name": "Sentinel 告警", "module": "内部", "target": "Sentinel API", "trigger": "定时(5min)", "status": "success", "duration": "6s", "detail": "2 活跃告警同步"},
    {"task_name": "生产-apse1 全量", "module": "AWS", "target": "生产 / apse1", "trigger": "Cron", "status": "running", "duration": "-", "detail": "运行中"},
    {"task_name": "生产-IAM 增量", "module": "AWS", "target": "生产 / global", "trigger": "人工", "status": "failed", "duration": "1m12s", "error": "AssumeRole 凭据过期", "detail": "IAM 全量同步失败"},
    {"task_name": "闲置资源检测", "module": "巡检", "target": "EC2/EBS/ELB", "trigger": "Cron", "status": "failed", "duration": "30m+", "error": "执行超时", "detail": "AssumeRole 轮换导致超时"},
    {"task_name": "GitLab 仓库全量", "module": "内部", "target": "GitLab API", "trigger": "Cron", "status": "failed", "duration": "-", "error": "Token 过期", "detail": "连接失败 — Token 过期"},
    {"task_name": "数据完整性检查", "module": "巡检", "target": "CMDB 全域", "trigger": "Cron", "status": "success", "duration": "4m20s", "detail": "23 条缺失关联"},
    {"task_name": "企业微信全量", "module": "内部", "target": "企微 API", "trigger": "Cron", "status": "success", "duration": "1m40s", "detail": "用户↑5✏️12↓1"},
    {"task_name": "SonarQube 全量", "module": "内部", "target": "SonarQube API", "trigger": "Cron", "status": "success", "duration": "2m12s", "detail": "42 项目报告"},
    {"task_name": "Lark 通讯录全量", "module": "内部", "target": "Lark Open API", "trigger": "Cron", "status": "success", "duration": "2m18s", "detail": "用户↑12✏️34↓2"},
    {"task_name": "安全组开放端口审计", "module": "巡检", "target": "1,250 安全组", "trigger": "Cron", "status": "success", "duration": "3m08s", "detail": "5 个安全组存在 0.0.0.0/0 入口"},
    {"task_name": "Jira 工单同步", "module": "内部", "target": "Jira REST API", "trigger": "每30min", "status": "success", "duration": "1m05s", "detail": "Issue↑8✏️15"},
    {"task_name": "Jenkins 构建同步", "module": "内部", "target": "Jenkins API", "trigger": "每10min", "status": "success", "duration": "8s", "detail": "156 Job·1,234 构建"},
    {"task_name": "成本异常分析", "module": "巡检", "target": "全账号 12 个", "trigger": "Cron", "status": "success", "duration": "1m12s", "detail": "生产周环比+12%"},
]


class Command(BaseCommand):
    help = "Seed demo data into in-memory store and PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset the store and history table before seeding.",
        )

    def handle(self, *args, **options):
        # ── 0. 幂等初始化（配置层播种 + 调度层 PeriodicTask 预建） ──
        from core.startup import initialize
        initialize()

        # ── 1. 内存演示数据（Dashboard/Worker 等） ──
        if options["reset"]:
            demo_store.reset()
            self.stdout.write(self.style.WARNING("已清空内存存储"))

        demo_store.seed_defaults()

        # ── 2. 执行历史 → PostgreSQL ──
        from api.history.models import DailyTaskStat, ExecutionRecord

        if options["reset"]:
            # 按外键依赖逆序清理全部业务表
            from core.models import AccountRegion
            from django_celery_beat.models import CrontabSchedule, PeriodicTask
            from django.db import connection

            ExecutionRecord.objects.all().delete()
            DailyTaskStat.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空执行历史表与聚合表"))

            PeriodicTask.objects.all().delete()
            CrontabSchedule.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空调度任务与 Crontab"))

            AccountRegion.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空账号区域配置"))

        created = 0
        now = timezone.now()
        for i, item in enumerate(SEED_HISTORY):
            # 错开时间，模拟真实执行时间线
            started = now - timedelta(hours=1, minutes=i * 4)
            finished = started + timedelta(seconds=30) if item["status"] in ("success", "failed") else None
            ExecutionRecord.objects.get_or_create(
                task_name=item["task_name"],
                module=item["module"],
                started_at__date=started.date(),
                defaults={
                    **item,
                    "celery_task_id": f"seed-{i:04d}",
                    "started_at": started,
                    "finished_at": finished,
                },
            )
            created += 1

        # ── 3. 聚合表 DailyTaskStat（近 7 天，供大盘趋势/可靠性观察） ──
        seeded_stats = self._seed_daily_stats()

        # ── 4. 汇总输出 ──
        from core.config_service import list_account_regions
        from core.schedule_manager import SCHEDULED_TASK
        from django_celery_beat.models import PeriodicTask

        periodic_count = PeriodicTask.objects.filter(task=SCHEDULED_TASK).count()

        self.stdout.write(self.style.SUCCESS("✅ 演示数据播种完成："))
        self.stdout.write(f"   账号/区域配置: {len(list_account_regions())} 个账号")
        self.stdout.write(f"   PeriodicTask 预建: {periodic_count} 条（含维护任务）")
        self.stdout.write(f"   执行历史: {created} 条（写入 PostgreSQL）")
        self.stdout.write(f"   聚合统计: {seeded_stats} 天（DailyTaskStat）")
        self.stdout.write(f"   Worker 数: {len(demo_store.get_workers())}")

    def _seed_daily_stats(self, days: int = 7):
        """播种近 N 天聚合统计（确定性数据，展示 7 天趋势 + 多模块健康度）。"""
        from api.history.models import DailyTaskStat

        today = timezone.localdate()
        # 每日基线：今天任务少（真实），前几天多（夜间批量）
        base = [46, 58, 52, 61, 44, 57, 12]
        # 模块构成：AWS 为主，内部系统/巡检为辅（健康度环形图更完整）
        module_mix = {"AWS": 1.0, "内部系统": 0.35, "巡检": 0.25}
        seeded = 0
        for i in range(days):
            date = today - timedelta(days=days - 1 - i)
            for module, ratio in module_mix.items():
                total = int((base[i] if i < len(base) else 40) * ratio)
                success = int(total * (0.96 if i % 3 else 0.93))
                failed = total - success
                stat, was_created = DailyTaskStat.objects.get_or_create(
                    stat_date=date,
                    module=module,
                    defaults={
                        "total": total,
                        "success": success,
                        "failed": failed,
                        "total_duration": total * 90.0,
                        "synced_count": total * 26,
                    },
                )
                if was_created:
                    seeded += 1
        return seeded
