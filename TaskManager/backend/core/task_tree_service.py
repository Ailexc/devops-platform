"""
task_tree_service — 任务树三源合并。

    GET /tasks/tree
      ① 账号/区域      ← 配置层（AccountRegion / 模拟 Apollo）
      ② 资源组/资源/关系 ← 能力层（registry dict，代码注册）
      ③ cron 状态      ← 调度层（PeriodicTask，按 name 匹配）
      ④ 锁状态         ← 并发锁（Redis）

一次性批量查询调度层，避免逐节点 N+1 查询。
"""

from __future__ import annotations

from django_celery_beat.models import PeriodicTask

from .config_service import list_account_regions
from .schedule_manager import SCHEDULED_TASK, REGION_TASK_TYPE, cron_display, relation_task_type


def _schedule_status_map() -> dict[str, dict]:
    """一次性加载所有调度任务 → {name: status}。"""
    result: dict[str, dict] = {}
    for t in PeriodicTask.objects.filter(task=SCHEDULED_TASK):
        result[t.name] = {
            "enabled": t.enabled,
            "crontab": cron_display(t.crontab),
            "periodic_id": t.id,
            "schedule_exists": True,
            "last_run_at": t.last_run_at,
        }
    return result


def build_task_tree() -> dict:
    """三源合并构建四级任务树。"""
    from .concurrency_lock import lock_manager
    from orchestrator.registry import registry

    status_map = _schedule_status_map()

    def status(name: str) -> dict:
        s = status_map.get(
            name,
            {"enabled": False, "crontab": None, "periodic_id": None, "schedule_exists": False, "last_run_at": None},
        )
        return {**s, "periodic_name": name}

    accounts = []
    for acct in list_account_regions():
        account_entry = {
            "name": acct["name"],
            "account_id": acct["account_id"],
            "regions": [],
        }
        for reg in acct["regions"]:
            region_code = reg["code"]
            region_status = status(f"{acct['name']}-{region_code}-_region-{REGION_TASK_TYPE}")

            groups = []
            for g in registry.list_groups():
                resources = []
                for res in g.resources:
                    st = status(f"{acct['name']}-{region_code}-{g.name}-{res.name}")
                    resources.append({
                        "name": res.name,
                        "cron": st["crontab"],
                        "enabled": st["enabled"],
                        "periodic_id": st["periodic_id"],
                        "periodic_name": st["periodic_name"],
                        "schedule_exists": st["schedule_exists"],
                    })
                relationships = []
                for rel in registry.group_relations(g.name):
                    tt = relation_task_type(rel.source, rel.target)
                    st = status(f"{acct['name']}-{region_code}-{g.name}-{tt}")
                    relationships.append({
                        "source": rel.source,
                        "target": rel.target,
                        "cardinality": rel.cardinality,
                        "key": rel.key,
                        "desc": rel.description,
                        "cron": st["crontab"],
                        "enabled": st["enabled"],
                        "periodic_id": st["periodic_id"],
                        "periodic_name": st["periodic_name"],
                        "schedule_exists": st["schedule_exists"],
                    })
                groups.append({"name": g.name, "resources": resources, "relationships": relationships})

            account_entry["regions"].append({
                "code": region_code,
                "endpoint": reg["endpoint"],
                "cron": reg["cron"],
                "concurrency": reg["concurrency"],
                "enabled": reg["enabled"],
                "schedule_enabled": region_status["enabled"],
                "schedule_cron": region_status["crontab"],
                "schedule_name": region_status["periodic_name"],
                "resource_groups": groups,
            })
        accounts.append(account_entry)

    return {
        "accounts": accounts,
        "active_locks": lock_manager.list_active(),
    }
