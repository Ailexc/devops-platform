import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_retry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(
    "cmdb",
    include=[
        "api.tasks.task_defs",
        "orchestrator.master_orchestrator",
        "orchestrator.relation_tasks",
        "core.maintenance_tasks",
        # resource_modules 不是 INSTALLED_APPS，需显式 include 让 worker 注册任务
        "resource_modules.ec2.celery_tasks",
        "resource_modules.vpc.celery_tasks",
        "resource_modules.rds.celery_tasks",
    ],
)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Queue routing — correspond to the three worker types in docker-compose
app.conf.task_routes = {
    "resource_modules.*": {"queue": "aws"},
    "orchestrator.*": {"queue": "default"},
    "core.maintenance_tasks.*": {"queue": "default"},
    "connector.*": {"queue": "connector"},
    "inspection.*": {"queue": "inspection"},
}
app.conf.task_default_queue = "default"

# 编排任务自身的"完成"事件延后到 finalize（子任务全部完成后）统一追加
_DEFERRED_COMPLETION_TASKS = {"orchestrator.master_orchestrator.orchestrate"}


# ── Lifecycle signals ────────────────────────────────────────────────

@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, **kwargs):
    """Worker received the task, about to execute."""
    if not task_id:
        return
    from core.lifecycle_tracker import LifecycleTracker
    tracker = LifecycleTracker(task_id)
    sender_name = sender.name if sender else "unknown"
    worker = kwargs.get("worker", "")
    tracker.append("received", f"Worker 接收", f"task: {sender_name}, worker: {worker}")


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, retval=None, **kwargs):
    """Task finished (success or failure handled separately)."""
    if not task_id:
        return
    sender_name = sender.name if sender else "unknown"
    from core.lifecycle_tracker import LifecycleTracker
    tracker = LifecycleTracker(task_id)
    state = kwargs.get("state", "")
    # 编排任务（orchestrate）的完成事件由 finalize 统一追加，避免过早标记
    if state == "SUCCESS" and sender_name not in _DEFERRED_COMPLETION_TASKS:
        tracker.append("completed", "执行完成")
    # Note: FAILURE is handled by on_task_failure for more detail


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Task failed with an exception."""
    if not task_id:
        return
    from core.lifecycle_tracker import LifecycleTracker
    tracker = LifecycleTracker(task_id)
    tracker.append("failed", "执行失败", str(exception)[:200])


@task_retry.connect
def on_task_retry(sender=None, request=None, reason=None, **kwargs):
    """Task is being retried."""
    task_id = request.id if request else None
    if not task_id:
        return
    from core.lifecycle_tracker import LifecycleTracker
    tracker = LifecycleTracker(task_id)
    tracker.append("retrying", f"自动重试 (attempt {request.retries})", str(reason)[:200])
