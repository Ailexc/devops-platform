"""
execution_service — 执行历史两级模型 & 派发流程服务。

所有粒度的执行统一入口：创建父记录 → 加锁(409) → orchestrate.delay。
资源/关系任务在 orchestrate 内部展开为子记录（同表，parent FK）。

层级触发语义统一：
  区域级   → 全资源并行 → 全关系并行
  资源组级 → 该组资源并行 → 该组源端关系并行
  资源级   → 单资源
  关系级   → 单关系
"""

from __future__ import annotations

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

# 冲突异常（API 层捕获 → 返回 409）
class TaskConflictError(Exception):
    def __init__(self, message: str, conflict: dict | None = None):
        super().__init__(message)
        self.conflict = conflict or {}


# ── 资源集合展开（供并发锁 + 树展示） ───────────────────────────────


def scope_resource_keys(account: str, region: str, scope: str, target: str) -> list[str]:
    """把任务"展开"为覆盖的资源 key 集合。

    key 格式：`{group}:{resource}`（资源）/ `{group}:rel:{source}:{target}`（关系）
    """
    from orchestrator.registry import registry

    keys: list[str] = []

    if scope == "region":
        for g in registry.list_groups():
            for res in g.resources:
                keys.append(f"{g.name}:{res.name}")
            for rel in registry.group_relations(g.name):
                keys.append(f"{g.name}:rel:{rel.source}:{rel.target}")

    elif scope == "group":
        g = registry.get_group(target)
        if g:
            for res in g.resources:
                keys.append(f"{g.name}:{res.name}")
            for rel in registry.group_relations(g.name):
                keys.append(f"{g.name}:rel:{rel.source}:{rel.target}")

    elif scope == "resource":
        g = _group_of_resource(target)
        keys.append(f"{g}:{target}" if g else f"?:{target}")

    elif scope == "relation":
        source, _, tgt = target.partition(":")
        g = _group_of_resource(source)
        keys.append(f"{g}:rel:{source}:{tgt}" if g else f"?:rel:{source}:{tgt}")

    return keys


def _group_of_resource(resource_name: str) -> str | None:
    from orchestrator.registry import registry

    for g in registry.list_groups():
        if any(res.name == resource_name for res in g.resources):
            return g.name
    return None


def task_display_name(account: str, region: str, scope: str, target: str) -> str:
    """父记录的任务展示名。"""
    if scope == "region":
        return f"{account}/{region} 区域同步"
    if scope == "group":
        return f"{account}/{region} {target}同步"
    if scope == "resource":
        return f"{account}/{region} {target}同步"
    if scope == "relation":
        source, _, tgt = target.partition(":")
        return f"{account}/{region} {source}→{tgt} 关系同步"
    return f"{account}/{region} 同步"


# ── 记录创建/更新 ───────────────────────────────────────────────────


def create_parent_record(account: str, region: str, scope: str, target: str,
                         mode: str, trigger: str, celery_task_id: str = "", resource_ids=None):
    """创建任务级父记录（params 记录派发参数，供一键重试复用）。"""
    from api.history.models import ExecutionRecord

    record = ExecutionRecord.objects.create(
        scope=scope,
        parent=None,
        task_name=task_display_name(account, region, scope, target),
        module="AWS",
        target=f"{account} / {region}",
        trigger=trigger,
        status="running",
        celery_task_id=celery_task_id,
        started_at=timezone.now(),
        detail=f"mode: {mode}",
        params={
            "account": account,
            "region": region,
            "scope": scope,
            "target": target,
            "mode": mode,
            "trigger": trigger,
            "resource_ids": resource_ids or [],
        },
    )
    return record


def create_child_record(execution_id, celery_task_id: str, name: str,
                        account: str, region: str, mode: str, kind: str = "resource"):
    """为进程级任务创建子记录（parent FK）。execution_id 为空时返回 None。

    以 celery_task_id 幂等（get_or_create）——Celery 重试会重新执行任务体，
    避免产生重复子记录；重试成功后 finish_record 会把状态从 failed 更新为 success。
    """
    if not execution_id:
        return None
    from api.history.models import ExecutionRecord

    parent = ExecutionRecord.objects.filter(pk=execution_id).first()
    if not parent:
        return None

    record, _ = ExecutionRecord.objects.get_or_create(
        celery_task_id=celery_task_id,
        defaults={
            "scope": "process",
            "parent": parent,
            "task_name": name,
            "module": "AWS",
            "target": f"{account}/{region}",
            "trigger": parent.trigger,
            "status": "running",
            "started_at": timezone.now(),
            "detail": f"{kind}: {name}, mode: {mode}",
        },
    )
    return record


def finish_record(record, status: str, result: dict | None = None, error: str = ""):
    """写入状态/耗时/结果（不追加生命周期事件，事件由 Celery 信号负责）。"""
    if record is None:
        return
    from api.history.models import ExecutionRecord

    record.status = status
    record.finished_at = timezone.now()
    if record.started_at and record.finished_at:
        secs = max(0, (record.finished_at - record.started_at).total_seconds())
        record.duration = f"{secs:.1f}s" if secs < 60 else f"{int(secs // 60)}m{int(secs % 60):02d}s"
    if result is not None:
        record.result = result
    if error:
        record.error = error[:2000]
    record.save(update_fields=["status", "finished_at", "duration", "result", "error"])


# ── 派发流程（人工/定时共用） ───────────────────────────────────────


def dispatch_execution(account: str, region: str, scope: str, target: str,
                       mode: str = "full", trigger: str = "人工", resource_ids: list[str] | None = None):
    """统一派发：校验 → 展开资源集合 → 加锁(409) → 建父记录 → orchestrate.delay。

    返回: {"record": ExecutionRecord, "async_result": AsyncResult}
    冲突时抛出 TaskConflictError（API 层转 409）。
    """
    from orchestrator.registry import registry
    from orchestrator.master_orchestrator import orchestrate
    from core.concurrency_lock import lock_manager

    # 1. 校验 scope/target 合法性
    if scope == "group" and not registry.get_group(target):
        raise ValueError(f"未知资源组: {target}")
    if scope == "resource" and not registry.get_resource(target):
        raise ValueError(f"未知资源类型: {target}")
    if scope == "relation":
        source, _, tgt = target.partition(":")
        if not source or not tgt or not registry.get_relation(source, tgt):
            raise ValueError(f"未知关联关系: {target}")

    # 2. 展开资源集合 + 加锁（冲突 → 409）
    keys = scope_resource_keys(account, region, scope, target)
    lock = lock_manager.acquire(account, region, keys, scope=scope, target=target)
    if lock is None:
        conflict = lock_manager.is_locked(keys)
        raise TaskConflictError(
            f"该范围已有任务在执行中（account: {account}, region: {region}）",
            conflict=conflict,
        )

    # 3. 创建父记录
    record = create_parent_record(account, region, scope, target, mode, trigger, resource_ids=resource_ids)

    # 4. 生命周期：created + dispatched
    from core.lifecycle_tracker import LifecycleTracker
    tracker = LifecycleTracker(record.celery_task_id)
    tracker.append("created", "任务创建", f"account: {account}, region: {region}, scope: {scope}, mode: {mode}")
    tracker.append("dispatched", "任务派发", f"orchestrate → lock: {lock['lock_id']}")

    # 5. 下发编排任务（父记录的 celery_task_id 由 orchestrate 内部回填）
    async_result = orchestrate.delay(
        record.id, account, region, scope, target, mode, trigger, lock["lock_id"], resource_ids
    )
    # orchestrate 任务 id 回填到父记录，供生命周期信号定位
    record.celery_task_id = async_result.id
    record.save(update_fields=["celery_task_id"])
    # dispatched 事件 detail 补上真实 task id
    tracker.update_last(detail=f"celery_task_id: {async_result.id[:12]}")

    logger.info(f"execution_service: dispatched {scope}/{target} {account}/{region} → {async_result.id[:12]}")
    return {"record": record, "async_result": async_result}


def summarize_children(parent) -> dict:
    """汇总子记录状态（供父记录 result 与详情页）。"""
    children = list(parent.children.all())
    summary = {
        "total": len(children),
        "success": sum(1 for c in children if c.status == "success"),
        "failed": sum(1 for c in children if c.status == "failed"),
        "running": sum(1 for c in children if c.status == "running"),
    }
    return summary


def update_daily_stat(record) -> None:
    """任务完成时增量更新按天聚合表（DailyTaskStat，保留 30 天）。"""
    if record is None or record.parent is not None:
        return
    from api.history.models import DailyTaskStat

    today = timezone.localdate()
    stat, _ = DailyTaskStat.objects.get_or_create(
        stat_date=today,
        module=record.module,
    )
    stat.total += 1
    if record.status == "success":
        stat.success += 1
    elif record.status == "failed":
        stat.failed += 1

    # 同步资源量：汇总子记录结果（统一结构 details.added/updated/deleted）
    synced = 0
    for child in record.children.all():
        result = child.result or {}
        details = result.get("details") or result  # 兼容新/旧结构
        synced += int(details.get("added") or 0)
        synced += int(details.get("updated") or 0)
        synced += int(details.get("deleted") or 0)
    stat.synced_count += synced
    stat.save()

    logger.info(f"execution_service: DailyTaskStat updated {today} {record.module}: +1 task")
