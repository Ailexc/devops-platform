"""
Celery tasks for EC2 sync — called by the orchestrator or triggered directly.

签名（两波次编排）：
    task(account, region, mode="full", resource_ids=None, execution_id=None, resource_name=None)
  - execution_id: 父记录 ID（用于创建进程级子记录）
  - resource_name: 单资源类型（如 EC2），编排层保证一任务一资源类型
"""

from celery import shared_task
from core.account_region_manager import AccountRegionManager
from core.checkpoint_manager import CheckpointManager
from core.execution_service import create_child_record, finish_record
from .sync import EC2SyncPipeline
from .resource import EC2, SecurityGroup, NetworkInterface

import redis
from django.conf import settings

_arm = AccountRegionManager()
_redis = redis.Redis.from_url(settings.REDIS_URL)
_cpm = CheckpointManager(_redis)

_EC2_RESOURCE_MAP = {
    "EC2": EC2,
    "SecurityGroup": SecurityGroup,
    "NetworkInterface": NetworkInterface,
}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_ec2_compute(self, account_name: str, region: str, mode: str = "full",
                     resource_ids: list[str] | None = None, execution_id=None, resource_name: str | None = None):
    """Celery task: sync one EC2-module resource type for one account/region."""
    import time
    from core.result_builder import build_resource_result

    task_id = self.request.id
    start = time.time()
    session = _arm.get_session(account_name, region)
    pipeline = EC2SyncPipeline(account_name, region, session, _cpm)
    child = create_child_record(execution_id, task_id, resource_name or "EC2", account_name, region, mode, kind="resource")

    try:
        if mode == "targeted" and resource_ids:
            result = pipeline.run_targeted_sync(EC2, resource_ids, task_id)
        elif resource_name and resource_name in _EC2_RESOURCE_MAP:
            # 单资源类型（两波次编排路径）
            result = pipeline.run_targeted_sync(_EC2_RESOURCE_MAP[resource_name], None, task_id)
        elif mode == "incremental":
            result = pipeline.run_incremental_sync(task_id)
        else:
            result = pipeline.run_full_sync(task_id)

        duration = f"{time.time() - start:.2f}s"
        if isinstance(result, dict) and "added" in result:
            wrapped = build_resource_result(resource_name or "EC2", result, logs=result.get("logs"), duration=duration)
            finish_record(child, "success", result=wrapped)
        else:
            wrapped = {"status": "success", "results": result, "duration": duration}
            finish_record(child, "success", result=wrapped)

        return {
            "status": "success",
            "account": account_name,
            "region": region,
            "mode": mode,
            "results": result,
            "result": wrapped,
        }
    except Exception as exc:
        finish_record(child, "failed", error=str(exc)[:500])
        # 重试耗尽后返回失败结果而非抛异常 → wave1 组不整体失败，wave2 照常执行
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "account": account_name,
                "region": region,
                "mode": mode,
                "resource": resource_name or "EC2",
                "error": str(exc)[:500],
            }


@shared_task
def sync_ec2_full(account_name: str, region: str):
    """Convenience wrapper — trigger a full EC2 sync."""
    return sync_ec2_compute.delay(account_name, region, "full")


@shared_task
def sync_ec2_incremental(account_name: str, region: str):
    """Convenience wrapper — trigger an incremental EC2 sync."""
    return sync_ec2_compute.delay(account_name, region, "incremental")


@shared_task
def sync_ec2_targeted(account_name: str, region: str, resource_ids: list[str]):
    """Convenience wrapper — trigger a targeted EC2 sync by resource IDs."""
    return sync_ec2_compute.delay(account_name, region, "targeted", resource_ids)
