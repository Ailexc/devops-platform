"""
Master Orchestrator — 两波次调度编排（真实架构的 Celery 直接翻译）。

真实模型                     Celery 实现
─────────────────────────    ────────────────────────────────
区域级任务下发                 orchestrate（顶层编排任务）
Wave1 全资源并行               group(resource_tasks)
每个资源类型一个"进程"         每个资源类型一个 Celery Task（prefork）
进程内协程对比                  Task 内部 sync 管线（asyncio）
资源全部完成 → 关系开始         chain(wave1, wave2)
Wave2 全关系并行               group(relation_tasks)
收尾（释放锁/汇总/聚合）        finalize

核心洞察：Celery prefork 池本身就是一个任务一个进程，正好等于真实场景的
"一个资源一个进程"；两波次调度用 chain(group, group) 实现"先资源后关系"的
全局顺序，同时保证两波内部最大化并行。
"""

import importlib
import logging

from celery import chord, group, shared_task

from .registry import registry

logger = logging.getLogger(__name__)

# ── Module task resolver ────────────────────────────────────────────

# 资源类型 → Celery 任务路径（同一模块的多个资源可共用同一任务函数）
_MODULE_TASK_MAP = {
    "EC2": "resource_modules.ec2.celery_tasks.sync_ec2_compute",
    "SecurityGroup": "resource_modules.ec2.celery_tasks.sync_ec2_compute",
    "NetworkInterface": "resource_modules.ec2.celery_tasks.sync_ec2_compute",
    "VPC": "resource_modules.vpc.celery_tasks.sync_vpc_network",
    "Subnet": "resource_modules.vpc.celery_tasks.sync_vpc_network",
    "RDS": "resource_modules.rds.celery_tasks.sync_rds_storage",
}


def _import_task(task_path: str):
    module_path, task_name = task_path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    return getattr(mod, task_name)


def _resolve_resource_task(res_def, account: str, region: str, mode: str, execution_id, resource_ids=None):
    """资源任务签名：task(account, region, mode, resource_ids=None, execution_id, resource_name)。"""
    task_path = _MODULE_TASK_MAP.get(res_def.name)
    if not task_path:
        logger.warning(f"No task mapping for resource type: {res_def.name}")
        return None
    task_fn = _import_task(task_path)
    return task_fn.s(account, region, mode, resource_ids, execution_id, res_def.name)


# ── 波次构建 ────────────────────────────────────────────────────────


def build_waves(account: str, region: str, scope: str, target: str, mode: str, execution_id, resource_ids=None):
    """按 scope 展开资源任务 + 关系任务（层级触发语义统一）。"""
    from .relation_tasks import build_relation

    resource_defs: list = []
    relations = []

    if scope == "region":
        for g in registry.list_groups():
            resource_defs.extend(g.resources)
            relations.extend(registry.group_relations(g.name))
    elif scope == "group":
        g = registry.get_group(target)
        if g:
            resource_defs = list(g.resources)
            relations = registry.group_relations(g.name)
    elif scope == "resource":
        res = registry.get_resource(target)
        if res:
            resource_defs = [res]
    elif scope == "relation":
        source, _, tgt = target.partition(":")
        rel = registry.get_relation(source, tgt)
        if rel:
            relations = [rel]
    else:
        raise ValueError(f"未知任务粒度: {scope}")

    resource_tasks = []
    for res_def in resource_defs:
        sig = _resolve_resource_task(res_def, account, region, mode, execution_id, resource_ids)
        if sig:
            resource_tasks.append(sig)

    relation_tasks = [
        build_relation.s(account, region, execution_id, rel.source, rel.target)
        for rel in relations
    ]

    return resource_tasks, relation_tasks


# ── 顶层编排任务 ────────────────────────────────────────────────────


@shared_task(bind=True, name="orchestrator.master_orchestrator.orchestrate")
def orchestrate(self, execution_id, account: str, region: str, scope: str,
                target: str, mode: str, trigger: str, lock_id: str | None,
                resource_ids: list[str] | None = None):
    """顶层编排任务：两波次调度（chord 回调实现）。

      Wave1 全资源并行 → chord(group(resources), wave1_done)
      Wave2 全关系并行 → chord(group(relations), finalize)
      收尾              → finalize（汇总/释放锁/聚合）

    为什么不用 chain(group, group)：Celery 的 chain 会把前一组结果作为
    位置参数注入后一组任务，导致签名不兼容；chord 回调是两阶段编排的
    惯用正确实现，语义与"先资源后关系"完全一致。
    """
    from core.concurrency_lock import lock_manager
    from core.execution_service import finish_record
    from core.lifecycle_tracker import LifecycleTracker

    parent = None
    try:
        from api.history.models import ExecutionRecord
        parent = ExecutionRecord.objects.filter(pk=execution_id).first()
        if parent:
            LifecycleTracker(parent.celery_task_id).append(
                "running", "开始编排", f"scope: {scope}, target: {target or '-'}"
            )

        resource_tasks, relation_tasks = build_waves(account, region, scope, target, mode, execution_id, resource_ids)

        if resource_tasks:
            # Wave1：全资源并行，全部完成后触发 wave1_done（再启动 Wave2）
            workflow = chord(
                group(resource_tasks),
                wave1_done.s(account, region, scope, target, mode, execution_id, lock_id),
            )
        elif relation_tasks:
            # 无资源波次（关系级）：直接 Wave2 + finalize
            workflow = chord(group(relation_tasks), finalize.s(execution_id=execution_id, lock_id=lock_id))
        else:
            workflow = finalize.si(execution_id=execution_id, lock_id=lock_id)

        result = workflow.apply_async()

        logger.info(
            f"orchestrate: {account}/{region} {scope}/{target} "
            f"→ wave1={len(resource_tasks)} wave2={len(relation_tasks)}"
        )
        return {
            "status": "dispatched",
            "execution_id": execution_id,
            "wave1": len(resource_tasks),
            "wave2": len(relation_tasks),
        }
    except Exception as exc:
        logger.exception("orchestrate failed, releasing lock & marking failed")
        lock_manager.release(lock_id)
        if parent:
            finish_record(parent, "failed", error=str(exc)[:500])
        raise


@shared_task(name="orchestrator.master_orchestrator.wave1_done")
def wave1_done(results, account: str, region: str, scope: str, target: str,
               mode: str, execution_id, lock_id: str | None = None):
    """Wave1 全部资源完成 → 启动 Wave2 全关系并行 → finalize 收尾。

    results: chord header（Wave1 资源任务）的聚合结果，此处不使用。
    """
    _, relation_tasks = build_waves(account, region, scope, target, mode, execution_id)

    if not relation_tasks:
        # 该粒度没有关系波次（如资源级）→ 直接收尾
        finalize.delay(execution_id=execution_id, lock_id=lock_id)
        return {"status": "no_relations", "execution_id": execution_id}

    chord(group(relation_tasks), finalize.s(execution_id=execution_id, lock_id=lock_id)).apply_async()
    logger.info(f"wave1_done: {account}/{region} → wave2 dispatched ({len(relation_tasks)} relations)")
    return {"status": "wave2_dispatched", "execution_id": execution_id, "relations": len(relation_tasks)}


@shared_task(name="orchestrator.master_orchestrator.finalize")
def finalize(results=None, execution_id=None, lock_id: str | None = None):
    from core.concurrency_lock import lock_manager
    from core.execution_service import finish_record, summarize_children, update_daily_stat
    from core.lifecycle_tracker import LifecycleTracker
    from core.result_builder import ResultBuilder

    try:
        from api.history.models import ExecutionRecord
        parent = ExecutionRecord.objects.get(pk=execution_id)
    except ExecutionRecord.DoesNotExist:
        lock_manager.release(lock_id)
        return {"status": "unknown", "execution_id": execution_id}

    summary = summarize_children(parent)
    if summary["total"] == 0 or summary["failed"] == 0:
        status = "success"
    elif summary["success"] == 0:
        status = "failed"
    else:
        status = "partial"

    # 统一结果结构：stats 汇总 + logs + children + params
    b = ResultBuilder(status=status)
    b.log(f"🏁 编排收尾: 共 {summary['total']} 个子进程")
    b.log(f"  ✅ 成功 {summary['success']} · ❌ 失败 {summary['failed']}"
          + (f" · ⏳ 运行中 {summary['running']}" if summary["running"] else ""))
    b.add_stats([
        {"key": "total", "label": "子进程", "value": summary["total"], "unit": "个"},
        {"key": "success", "label": "成功", "value": summary["success"], "unit": "个"},
        {"key": "failed", "label": "失败", "value": summary["failed"], "unit": "个"},
    ])
    result = b.build(
        f"子任务 {summary['total']}（✓{summary['success']} ✗{summary['failed']}）",
        extra={
            "children": summary,
            "params": parent.params or {},
        },
    )
    finish_record(parent, status, result=result)
    LifecycleTracker(parent.celery_task_id).append(
        "completed", "任务完成",
        f"子任务 {summary['total']}（✓{summary['success']} ⚠{summary['running']} ✗{summary['failed']}）",
    )
    lock_manager.release(lock_id)
    update_daily_stat(parent)

    return {"status": status, "execution_id": execution_id, "children": summary}


# ── 定时调度入口（Beat → scheduled_dispatch → 统一派发） ─────────────


@shared_task(name="orchestrator.master_orchestrator.scheduled_dispatch")
def scheduled_dispatch(account: str, region: str, group_name: str, task_type: str, mode: str = "full"):
    """PeriodicTask 定时触发入口。

    args = ["account", "region", "group_name", "task_type", "mode"]
    task_type 解析：
      region:all      → 区域级
      rel:SRC:TGT     → 关系级
      其他            → 资源级
    """
    from core.schedule_manager import REGION_TASK_TYPE, touch_last_run
    from core.execution_service import dispatch_execution

    if task_type == REGION_TASK_TYPE:
        scope, target = "region", ""
    elif task_type.startswith("rel:"):
        scope, target = "relation", task_type[len("rel:"):]
    else:
        scope, target = "resource", task_type

    # 标记最近调度时间（展示用）
    try:
        touch_last_run(f"{account}-{region}-{group_name}-{task_type}")
    except Exception:
        pass

    logger.info(f"scheduled_dispatch: {account}/{region} {scope}/{target} (mode={mode})")
    try:
        outcome = dispatch_execution(account, region, scope, target, mode, trigger="定时")
        return {"status": "dispatched", "execution_id": outcome["record"].id}
    except Exception as exc:
        logger.warning(f"scheduled_dispatch failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ── 兼容门面（旧调用方） ─────────────────────────────────────────────


class MasterOrchestrator:
    """旧版同步入口的兼容门面 — 现在统一走 execution_service.dispatch_execution。"""

    def sync_account_region(self, account_name, region, mode="full"):
        from core.execution_service import dispatch_execution
        return dispatch_execution(account_name, region, "region", "", mode, trigger="人工")["async_result"]

    def sync_resource_group(self, account_name, region, group_name, mode="full"):
        from core.execution_service import dispatch_execution
        return dispatch_execution(account_name, region, "group", group_name, mode, trigger="人工")["async_result"]

    def sync_targeted(self, account_name, region, resource_type, resource_ids):
        from core.execution_service import dispatch_execution
        return dispatch_execution(account_name, region, "resource", resource_type, "targeted", trigger="人工")["async_result"]


orchestrator = MasterOrchestrator()
