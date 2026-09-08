"""
startup — 幂等初始化（启动生命周期）。

    项目启动
      ├─ migrate（建表）
      ├─ discover_modules()        ← 能力层：收集 ResourceDef + Association
      ├─ 幂等预建 PeriodicTask     ← 调度层：对每个 (账号,区域,组,任务节点) get_or_create
      │    enabled=False, crontab=None（占位，不参与调度）
      ├─ 合并配置层账号/区域         ← 配置层：AccountRegion 播种
      └─ 服务可用

在 migrate 完成前（表不存在）调用会安全跳过，避免与 runserver/migrate 竞争。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _tables_ready() -> bool:
    """检查核心表是否已就绪（migrate 前调用会跳过）。"""
    try:
        from django.db import connection
        from django_celery_beat.models import PeriodicTask  # noqa: F401
        from core.models import AccountRegion  # noqa: F401
        connection.ensure_connection()
        tables = connection.introspection.table_names()
        return "core_accountregion" in tables and "django_celery_beat_periodictask" in tables
    except Exception:
        return False


def preprovision_all() -> int:
    """为所有 (账号,区域,资源组,任务节点) 幂等预建 PeriodicTask 占位。"""
    from core.config_service import list_account_regions
    from core.schedule_manager import (
        ensure_periodic_tasks,
        ensure_region_periodic_task,
        relation_task_type,
    )
    from orchestrator.registry import registry

    total = 0
    for acct in list_account_regions():
        account = acct["name"]
        for reg in acct["regions"]:
            region = reg["code"]
            # 区域级占位（含默认 cron 激活）
            ensure_region_periodic_task(account, region, reg.get("cron", ""))
            # 资源组/资源/关系级占位
            for g in registry.list_groups():
                nodes = [
                    {"type": "resource", "name": res.name, "task_type": res.name}
                    for res in g.resources
                ]
                nodes += [
                    {
                        "type": "relation",
                        "name": f"{rel.source}→{rel.target}",
                        "task_type": relation_task_type(rel.source, rel.target),
                    }
                    for rel in registry.group_relations(g.name)
                ]
                total += ensure_periodic_tasks(account, region, g.name, nodes)
    logger.info(f"startup: pre-provisioned {total} periodic task placeholders")
    return total


def ensure_maintenance_tasks():
    """注册维护类 Beat 任务（每日清理）。"""
    import json

    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    name = "maintenance.cleanup_old_records"
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute="30", hour="3", day_of_month="*", month_of_year="*", day_of_week="*",
        timezone="Asia/Shanghai",
    )
    PeriodicTask.objects.get_or_create(
        name=name,
        defaults={
            "task": "core.maintenance_tasks.cleanup_old_records",
            "args": json.dumps([]),
            "crontab": crontab,
            "enabled": True,
            "description": "每日 03:30 清理：执行记录保留 3 天，聚合表保留 30 天",
        },
    )


def initialize():
    """幂等初始化入口（可从 AppConfig.ready / seed 命令 / celery 启动调用）。"""
    from orchestrator.registry import discover_modules

    discover_modules()

    if not _tables_ready():
        logger.info("startup: tables not ready yet — skipping DB init")
        return

    try:
        from core.config_service import ensure_config_seeded
        ensure_config_seeded()
        preprovision_all()
        ensure_maintenance_tasks()
        logger.info("startup: initialize() completed")
    except Exception as exc:
        logger.warning(f"startup: initialize() failed (non-fatal): {exc}")
