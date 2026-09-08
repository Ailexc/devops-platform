"""
reset_data — 完全重置所有业务数据并重新播种。

用法:
    python manage.py reset_data          # 清空全部业务数据 → 重新播种
    python manage.py reset_data --dry    # 仅展示将要清空的内容，不执行
    python manage.py reset_data --no-seed # 清空后不自动播种（仅清空）

说明:
    覆盖范围:
      1. 执行记录 (ExecutionRecord)
      2. 日聚合统计 (DailyTaskStat)
      3. 账号区域配置 (AccountRegion)
      4. 周期调度任务 (PeriodicTask + CrontabSchedule)
      5. Celery 任务结果 (TaskResult)
      6. 内存演示数据 (DemoStore)

    执行后系统回到出厂状态，等同于首次 clone 项目后 migrate + seed。
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "完全重置所有业务数据（含配置、调度、历史、内存），可选重新播种。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="仅展示将要清空的内容，不执行删除。",
        )
        parser.add_argument(
            "--no-seed",
            action="store_true",
            help="清空后不自动重新播种演示数据。",
        )

    # ── 表清单 ────────────────────────────────────────────────────

    @staticmethod
    def _business_tables() -> list[tuple[str, str]]:
        """返回 (模型路径, 表名) 列表，顺序保证外键依赖正确。"""
        return [
            ("api.history.ExecutionRecord", "api_history_executionrecord"),
            ("api.history.DailyTaskStat", "api_history_dailytaskstat"),
            ("core.AccountRegion", "core_accountregion"),
            # django-celery-beat: PeriodicTask 依赖 CrontabSchedule
            ("django_celery_beat.PeriodicTask", "django_celery_beat_periodictask"),
            ("django_celery_beat.CrontabSchedule", "django_celery_beat_crontabschedule"),
            ("django_celery_beat.IntervalSchedule", "django_celery_beat_intervalschedule"),
            ("django_celery_beat.ClockedSchedule", "django_celery_beat_clockedschedule"),
            ("django_celery_beat.SolarSchedule", "django_celery_beat_solarschedule"),
            # django-celery-results
            ("django_celery_results.TaskResult", "django_celery_results_taskresult"),
            ("django_celery_results.GroupResult", "django_celery_results_groupresult"),
        ]

    def _table_exists(self, table_name: str) -> bool:
        return table_name in connection.introspection.table_names()

    # ── 主逻辑 ────────────────────────────────────────────────────

    def handle(self, *args, **options):
        dry = options["dry"]
        no_seed = options["no_seed"]

        tables = self._business_tables()
        existing = [(path, tbl) for path, tbl in tables if self._table_exists(tbl)]

        if not existing:
            self.stdout.write(self.style.WARNING("⚠ 无业务表存在（可能尚未 migrate）。"))
            return

        # ── 1. 展示计划 ──
        self.stdout.write(self.style.HTTP_INFO("── 数据重置计划 ──"))
        for model_path, table_name in existing:
            count = self._count_table(table_name)
            self.stdout.write(f"  · {model_path:<45} → {count} 行")

        if dry:
            self.stdout.write(self.style.WARNING("\n(Dry Run) 以上内容未执行任何删除。"))
            return

        # ── 2. 清空（按外键依赖逆序删除） ──
        self.stdout.write("")
        for model_path, table_name in reversed(existing):
            if self._table_exists(table_name):
                count = self._count_table(table_name)
                connection.cursor().execute(f'TRUNCATE TABLE "{table_name}" CASCADE')
                self.stdout.write(self.style.WARNING(f"  ✂  已清空 {table_name} ({count} 行)"))

        # 清空内存演示数据
        from core.demo_store import demo_store
        demo_store.reset()
        self.stdout.write(self.style.WARNING("  ✂  已清空内存演示数据 (DemoStore)"))

        # ── 3. 重新播种 ──
        if not no_seed:
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO("── 重新播种演示数据 ──"))
            from django.core.management import call_command
            call_command("seed_demo_data", stdout=self.stdout, style=self.style)

        # ── 4. 汇总 ──
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ 数据重置完成。系统已恢复至出厂状态。"))

    def _count_table(self, table_name: str) -> int:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                return cursor.fetchone()[0]
        except Exception:
            return -1
