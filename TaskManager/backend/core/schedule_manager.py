"""
schedule_manager — 调度层（PeriodicTask）管理服务。

任务树「调度层」数据源。核心设计（方案1·预建占位）：

  阶段            enabled   crontab    Beat 行为
  初始化预建      False     None       完全不加载（安全）
  前端设置 cron   True      cron       正常调度
  前端取消 cron   False     None       不再调度

命名规则：`{account}-{region}-{group}-{task_type}`
  - resource 任务: task_type = 资源名（如 EC2）
  - relation 任务: task_type = `rel:{source}:{target}`（如 rel:EC2:VPC）
  - 区域级任务:    task_type = `region:all`

args = ["{account}", "{region}", "{scope}", "{target}"]，执行时由调度器
传递进 `scheduled_dispatch`，任务函数是纯函数、参数进来直接用。
"""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

logger = logging.getLogger(__name__)

# 被调度执行的统一入口任务（见 orchestrator/master_orchestrator.py）
SCHEDULED_TASK = "orchestrator.master_orchestrator.scheduled_dispatch"

# 区域级任务的 task_type 固定值
REGION_TASK_TYPE = "region:all"

# 哨兵 cron：2月31日不存在 → 永不触发。预建占位用它满足 django-celery-beat
# 的 validate_unique 校验（必须有一个 schedule），同时 enabled=False 保证
# Beat 在用户配置前不加载。展示层将哨兵映射为“未配置”(None)。
SENTINEL_CRON = "0 0 31 2 *"


def cron_display(crontab) -> str | None:
    """CrontabSchedule → cron 字符串；哨兵（未配置）返回 None。"""
    if not crontab:
        return None
    cron = (
        f"{crontab.minute} {crontab.hour} {crontab.day_of_month} "
        f"{crontab.month_of_year} {crontab.day_of_week}"
    )
    return None if cron == SENTINEL_CRON else cron


def relation_task_type(source: str, target: str) -> str:
    return f"rel:{source}:{target}"


def _parse_cron(cron: str) -> dict:
    """'0 2 * * *' → {minute, hour, day_of_month, month_of_year, day_of_week}."""
    parts = (cron or "0 2 * * *").split()
    parts += ["*"] * (5 - len(parts))
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day_of_month": parts[2],
        "month_of_year": parts[3],
        "day_of_week": parts[4],
    }


def _get_crontab(cron: str) -> CrontabSchedule:
    fields = _parse_cron(cron)
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=fields["minute"],
        hour=fields["hour"],
        day_of_month=fields["day_of_month"],
        month_of_year=fields["month_of_year"],
        day_of_week=fields["day_of_week"],
        timezone=settings.CELERY_TIMEZONE,
    )
    return crontab


# ── 预建占位 ────────────────────────────────────────────────────────


def ensure_periodic_tasks(account: str, region: str, group_name: str, nodes: list[dict]):
    """为 (账号,区域,资源组) 下的所有任务节点幂等预建 PeriodicTask 占位。

    nodes: [{"type": "resource"|"relation", "name": 展示名, "task_type": 唯一标识}, ...]
    预建时 enabled=False, crontab=None，用户在配置 cron 前不会被 Beat 加载。
    """
    created = 0
    for node in nodes:
        name = f"{account}-{region}-{group_name}-{node['task_type']}"
        _, was_created = PeriodicTask.objects.get_or_create(
            name=name,
            defaults={
                "task": SCHEDULED_TASK,
                "args": json.dumps([account, region, group_name, node["task_type"], "full"]),
                "crontab": _get_crontab(SENTINEL_CRON),
                "enabled": False,
                "description": f"{account}/{region}/{group_name}/{node['name']}（预建占位，配置 cron 后启用）",
            },
        )
        if was_created:
            created += 1
    if created:
        logger.info(f"schedule_manager: pre-provisioned {created} periodic tasks for {account}/{region}/{group_name}")
    return created


def ensure_region_periodic_task(account: str, region: str, cron: str = ""):
    """区域级预建占位（含默认 cron 激活）。"""
    group_name = "_region"
    name = f"{account}-{region}-{group_name}-{REGION_TASK_TYPE}"
    task, was_created = PeriodicTask.objects.get_or_create(
        name=name,
        defaults={
            "task": SCHEDULED_TASK,
            "args": json.dumps([account, region, group_name, REGION_TASK_TYPE, "full"]),
            "crontab": _get_crontab(SENTINEL_CRON),
            "enabled": False,
            "description": f"{account}/{region} 区域级定时同步",
        },
    )
    if cron and was_created:
        set_cron(name, cron)
    return task


# ── 查询 ────────────────────────────────────────────────────────────


def get_task_status(name: str) -> dict:
    """返回调度状态：{enabled, crontab, exists}。"""
    try:
        task = PeriodicTask.objects.get(name=name)
    except PeriodicTask.DoesNotExist:
        return {"enabled": False, "crontab": None, "exists": False}
    return {"enabled": task.enabled, "crontab": cron_display(task.crontab), "exists": True, "id": task.id}


def get_status_by_args(account: str, region: str, group_name: str, task_type: str) -> dict:
    return get_task_status(f"{account}-{region}-{group_name}-{task_type}")


# ── 修改（前端 cron 配置入口） ───────────────────────────────────────


def set_cron(name: str, cron: str) -> dict:
    """启用 + 设置 crontab。"""
    task = PeriodicTask.objects.get(name=name)
    task.crontab = _get_crontab(cron)
    task.enabled = True
    task.save(update_fields=["crontab", "enabled"])
    logger.info(f"schedule_manager: enabled cron for {name}: {cron}")
    return get_task_status(name)


def clear_cron(name: str) -> dict:
    """取消 cron：禁用 + 回退到哨兵（Beat 不再加载）。"""
    task = PeriodicTask.objects.get(name=name)
    task.enabled = False
    task.crontab = _get_crontab(SENTINEL_CRON)
    task.save(update_fields=["crontab", "enabled"])
    logger.info(f"schedule_manager: disabled cron for {name}")
    return get_task_status(name)


# ── 清理 ────────────────────────────────────────────────────────────


def reconcile_disabled_accounts(enabled_accounts: set[str]):
    """账号下线对账：禁用配置中不存在的账号对应的任务（可选的运维能力）。"""
    from django_celery_beat.models import PeriodicTask

    qs = PeriodicTask.objects.filter(task=SCHEDULED_TASK, enabled=True)
    updated = 0
    for task in qs:
        try:
            args = json.loads(task.args)
        except (ValueError, TypeError):
            continue
        if args and args[0] not in enabled_accounts:
            task.enabled = False
            task.crontab = _get_crontab(SENTINEL_CRON)
            task.save(update_fields=["enabled", "crontab"])
            updated += 1
    if updated:
        logger.info(f"schedule_manager: disabled {updated} tasks for removed accounts")
    return updated


def touch_last_run(name: str):
    """记录最近一次调度执行时间（展示用）。"""
    try:
        task = PeriodicTask.objects.get(name=name)
    except PeriodicTask.DoesNotExist:
        return
    task.last_run_at = timezone.now()
    task.save(update_fields=["last_run_at"])
