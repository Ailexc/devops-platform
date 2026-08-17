"""
relation_tasks — Wave2 关系任务。

真实语义：关系任务基于**全局 CMDB**（读），不依赖本次同步的临时状态；
单资源失败不阻塞关系绑定（幂等 + 周期性修正，最终一致）。

Demo 实现：从全局 CMDB 虚拟存储读取源/目标资源，按关联 key 计算绑定
（如 EC2.vpc_id ∈ VPC.vpc_id），输出绑定清单与数量。
"""

import logging

from celery import shared_task

from .registry import registry

logger = logging.getLogger(__name__)


def compute_bindings(source: str, target: str) -> dict:
    """基于全局 CMDB 计算 source→target 绑定关系。"""
    src_def = registry.get_resource(source)
    tgt_def = registry.get_resource(target)
    rel = registry.get_relation(source, target)

    if not src_def or not tgt_def:
        return {"source": source, "target": target, "bound": 0, "unbound": 0, "bindings": [], "key": ""}

    key = rel.key if rel else src_def.bind_key
    src_items = src_def.model_cls.objects.all()
    tgt_items = tgt_def.model_cls.objects.all()
    tgt_keys = {item[tgt_def.bind_key] for item in tgt_items}

    bindings = []
    bound = 0
    for item in src_items:
        key_val = item.get(key)
        if key_val and key_val in tgt_keys:
            bound += 1
            bindings.append({"source_id": item.get(src_def.bind_key), "target_id": key_val})

    return {
        "source": source,
        "target": target,
        "key": key,
        "bound": bound,
        "unbound": len(src_items) - bound,
        "bindings": bindings[:20],
    }


@shared_task(bind=True, name="orchestrator.relation_tasks.build_relation")
def build_relation(self, account: str, region: str, execution_id=None, source: str = "", target: str = ""):
    """关系进程任务：计算 source→target 绑定并落库子记录（统一结果结构）。"""
    import time
    from core.result_builder import ResultBuilder
    from core.execution_service import create_child_record, finish_record

    task_id = self.request.id
    start = time.time()
    child = create_child_record(
        execution_id, task_id, f"{source}→{target}",
        account, region, "relation", kind="relation",
    )
    b = ResultBuilder()
    b.log(f"🔗 计算 {source}→{target} 绑定关系（基于全局 CMDB）")
    try:
        data = compute_bindings(source, target)
        bound, unbound = data["bound"], data["unbound"]
        b.log(f"  ✅ 源 {source} 共 {bound + unbound} 条, 绑定 {bound} 条 / 未绑定 {unbound} 条")
        b.add_stats([
            {"key": "bound", "label": "绑定", "value": bound, "unit": "条"},
            {"key": "unbound", "label": "未绑定", "value": unbound, "unit": "条"},
        ])
        result = b.build(
            f"{source}→{target} 绑定 {bound} / 未绑定 {unbound}",
            duration=f"{time.time() - start:.2f}s",
            extra={
                "source": source,
                "target": target,
                "key": data.get("key", ""),
                "bound": bound,
                "unbound": unbound,
            },
        )
        finish_record(child, "success", result=result)
        logger.info(f"build_relation: {account}/{region} {source}→{target} bound={bound}")
        return result
    except Exception as exc:
        logger.exception(f"build_relation failed: {source}→{target}")
        result = b.fail(str(exc)[:500]).build(f"{source}→{target} 关系计算失败")
        finish_record(child, "failed", result=result, error=str(exc)[:500])
        return result
