"""
metrics_service — 大盘/健康度真实数据服务（替代 demo_store 硬编码残留）。

所有指标均从真实数据源计算，不再依赖 demo_store 内存演示数据：
  - CMDB 资源数量 / 资源构成   ← Redis CMDB 存储（registry + CmdbQuerySet）
  - Worker 状态 / 负载         ← Celery inspect（真实 worker 池）
  - 模块新鲜度                 ← ExecutionRecord 最近成功完成时间
  - 最近事件                   ← ExecutionRecord 最近记录（失败/运行中/成功）
  - AWS 资源树                 ← registry（能力层）+ AccountRegion（配置层）

与 demo_store 的关系：本服务是真实数据源；demo_store 仅保留为
seed_demo_data 管理命令 / 前端 fallback 的演示数据。
"""

import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

# 资源类型 → 展示名/图标（前端展示用，与 demo_store 展示风格一致）
RESOURCE_META = {
    "EC2": {"name": "EC2 实例", "icon": "🖥️"},
    "SecurityGroup": {"name": "安全组", "icon": "🛡️"},
    "NetworkInterface": {"name": "弹性网卡", "icon": "🔗"},
    "VPC": {"name": "VPC 网络", "icon": "🌐"},
    "Subnet": {"name": "子网", "icon": "🔗"},
    "RDS": {"name": "RDS 数据库", "icon": "🗄️"},
}


# ── CMDB 资源统计 ────────────────────────────────────────────────


def cmdb_resource_stats() -> dict:
    """统计 CMDB Redis 存储中各资源类型数量 + 总数。"""
    from orchestrator.registry import registry

    breakdown = []
    total = 0
    for res in registry.list_resources():
        try:
            count = len(res.model_cls.objects.all())
        except Exception as exc:
            logger.warning(f"cmdb_resource_stats: {res.name} count failed: {exc}")
            count = 0
        meta = RESOURCE_META.get(res.name, {"name": res.name, "icon": "🗃️"})
        breakdown.append({
            "name": meta["name"],
            "icon": meta["icon"],
            "type": res.name,
            "count": count,
        })
        total += count
    return {"breakdown": breakdown, "total": total}


def total_cmdb_resources() -> int:
    """CMDB 总资源数（大盘统计卡片）。"""
    return cmdb_resource_stats()["total"]


# ── Worker 状态 ──────────────────────────────────────────────────


def worker_status() -> dict:
    """真实 worker 池状态（Celery inspect）。

    返回: {"workers": [{name, tasks, uptime, status}], "load": "52%"}
    """
    from config.celery import app as celery_app

    try:
        insp = celery_app.control.inspect()
        stats = insp.stats() or {}
        active = insp.active() or {}
    except Exception as exc:
        logger.warning(f"worker_status: celery inspect failed: {exc}")
        return {"workers": [], "load": "0%", "error": str(exc)[:100]}

    workers = []
    active_total = 0
    for name, st in stats.items():
        uptime_s = int((st or {}).get("uptime", 0) or 0)
        active_count = len((active or {}).get(name, []) or [])
        active_total += active_count
        workers.append({
            "name": name,
            "tasks": active_count,
            "uptime": f"{uptime_s // 3600}h{((uptime_s % 3600) // 60):02d}m" if uptime_s else "-",
            "status": "online",
        })

    # 无真实 CPU 采样时，用活跃任务数近似负载（单 worker 满载按 10 个并发任务估算）
    load = min(100, active_total * 10)
    return {"workers": workers, "load": f"{load}%"}


# ── 模块新鲜度 ───────────────────────────────────────────────────


def freshness_by_module() -> dict:
    """每个模块最近一次成功完成距今时间（如 {"AWS": "2m"}）。"""
    from api.history.models import ExecutionRecord

    now = timezone.now()
    out: dict = {}
    modules = (
        ExecutionRecord.objects.exclude(module="")
        .values_list("module", flat=True)
        .distinct()
    )
    for module in modules:
        last = (
            ExecutionRecord.objects.filter(module=module, status="success", finished_at__isnull=False)
            .order_by("-finished_at")
            .first()
        )
        if not last or not last.finished_at:
            out[module] = "-"
            continue
        secs = max(0, (now - last.finished_at).total_seconds())
        if secs < 60:
            out[module] = f"{int(secs)}s"
        elif secs < 3600:
            out[module] = f"{int(secs // 60)}m"
        else:
            out[module] = f"{int(secs // 3600)}h"
    return out


# ── 最近事件 ─────────────────────────────────────────────────────


def recent_events(limit: int = 10) -> list:
    """从最近执行记录生成事件流。

    失败/部分失败 → error，运行中 → warning，成功 → success。
    格式对齐前端 recent-events 接口（time/level/source/message/task_id）。
    """
    from api.history.models import ExecutionRecord

    cutoff = timezone.now() - timedelta(days=1)
    qs = (
        ExecutionRecord.objects.filter(parent__isnull=True, started_at__gte=cutoff)
        .order_by("-started_at")[:limit]
    )

    events = []
    for r in qs:
        if r.status in ("failed", "partial"):
            level = "error"
            msg = f"{r.task_name} 失败"
            if r.error:
                msg += f": {r.error[:80]}"
        elif r.status == "running":
            level = "warning"
            msg = f"{r.task_name} 执行中"
        else:
            level = "success"
            msg = f"{r.task_name} 完成"
            if r.detail:
                msg += f" ({r.detail[:60]})"
        events.append({
            "time": r.started_at.strftime("%H:%M") if r.started_at else "-",
            "level": level,
            "source": r.module or "-",
            "message": msg[:120],
            "task_id": f"#{r.id:05d}",
        })
    return events


# ── AWS 资源树 ───────────────────────────────────────────────────


def aws_resource_tree() -> dict:
    """从 registry（能力层）+ AccountRegion（配置层）生成真实资源树。

    结构对齐前端 aws-resources 接口：
      accounts → regions → resource_groups（resources + relationships）
    不再硬编码 ELB/IAM 等未注册资源。
    """
    from orchestrator.registry import registry
    from core.config_service import list_account_regions

    accounts = []
    for acct in list_account_regions():
        regions = []
        for reg in acct["regions"]:
            groups = []
            for g in registry.list_groups():
                groups.append({
                    "name": g.name,
                    "resources": [{"name": res.name, "type": res.name} for res in g.resources],
                    "relationships": [
                        {
                            "source": rel.source,
                            "target": rel.target,
                            "cardinality": rel.cardinality,
                            "key": rel.key,
                            "desc": rel.description,
                        }
                        for rel in registry.group_relations(g.name)
                    ],
                })
            regions.append({"code": reg["code"], "resource_groups": groups})
        enabled_count = sum(1 for r in acct["regions"] if r.get("enabled"))
        accounts.append({
            "name": acct["name"],
            "account_id": acct["account_id"],
            "coverage": f"{enabled_count}/{len(acct['regions'])}",
            "regions": regions,
        })
    return {"accounts": accounts}
