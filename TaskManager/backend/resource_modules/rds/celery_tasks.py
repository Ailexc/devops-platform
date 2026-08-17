"""
Celery tasks for RDS sync.

签名（两波次编排）：task(account, region, mode, resource_ids, execution_id, resource_name)
"""

from celery import shared_task
from core.account_region_manager import AccountRegionManager
from core.checkpoint_manager import CheckpointManager
from core.execution_service import create_child_record, finish_record
from .sync import RDSSyncPipeline
from .resource import RDS

import redis
from django.conf import settings

_arm = AccountRegionManager()
_redis = redis.Redis.from_url(settings.REDIS_URL)
_cpm = CheckpointManager(_redis)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_rds_storage(self, account_name: str, region: str, mode: str = "full",
                     resource_ids: list[str] | None = None, execution_id=None, resource_name: str | None = None):
    import time
    from core.result_builder import build_resource_result

    task_id = self.request.id
    start = time.time()
    session = _arm.get_session(account_name, region)
    pipeline = RDSSyncPipeline(account_name, region, session, _cpm)
    child = create_child_record(execution_id, task_id, resource_name or "RDS", account_name, region, mode, kind="resource")

    try:
        if resource_name == "RDS":
            result = pipeline._sync_resource(RDS, task_id)
        else:
            result = pipeline.run_full_sync(task_id)

        duration = f"{time.time() - start:.2f}s"
        if isinstance(result, dict) and "added" in result:
            wrapped = build_resource_result(resource_name or "RDS", result, logs=result.get("logs"), duration=duration)
            finish_record(child, "success", result=wrapped)
        else:
            wrapped = {"status": "success", "results": result, "duration": duration}
            finish_record(child, "success", result=wrapped)
        return {"status": "success", "account": account_name, "region": region, "mode": mode, "results": result, "result": wrapped}
    except Exception as exc:
        finish_record(child, "failed", error=str(exc)[:500])
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "account": account_name,
                "region": region,
                "mode": mode,
                "resource": resource_name or "RDS",
                "error": str(exc)[:500],
            }
