"""
EC2 sync pipeline — the actual data flow for synchronising EC2 resources.

Phase 1: Fetch existing data from CMDB → cache
Phase 2: Pull data from AWS API
Phase 3: Async diff (compare AWS vs CMDB)
Phase 4: Batch write (create / update / delete)

This module is called by the Celery task in ec2/celery_tasks.py.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from core.retry_engine import RetryEngine
from core.checkpoint_manager import Checkpoint, CheckpointManager
from core.transform_utils import to_cmdb_with_bind
from .resource import EC2, SecurityGroup, NetworkInterface, COMPUTE_GROUP

logger = logging.getLogger(__name__)


class EC2SyncPipeline:
    """Orchestrates the EC2 sync flow for a given account + region."""

    def __init__(self, account_name: str, region: str, aws_session, checkpoint_mgr: CheckpointManager | None = None):
        self.account_name = account_name
        self.region = region
        self.aws_session = aws_session
        self.checkpoint_mgr = checkpoint_mgr
        self.retry = RetryEngine(max_retries=3)
        self._logs: list[str] = []

    def _log(self, msg: str):
        """阶段日志：同时输出到 worker 控制台并收集进 result.logs。"""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"{ts} {msg}"
        self._logs.append(line)
        logger.info(msg)

    def run_full_sync(self, task_id: str) -> dict:
        """Execute a full (non-incremental) sync of all compute resources."""
        self._log(f"🚀 开始同步 {self.account_name}/{self.region} 计算组资源")
        results = {}
        for resource_def in COMPUTE_GROUP:
            self._log(f"  ▶️  同步 {resource_def.name} ...")
            result = self._sync_resource(resource_def, task_id)
            results[resource_def.name] = result
            self._log(f"  ✅ {resource_def.name} 同步完成")
        # Phase 2: build associations
        self._build_associations()
        return results

    def run_incremental_sync(self, task_id: str) -> dict:
        """Incremental sync — only process changes since last checkpoint."""
        # For Phase 1 this is identical to full sync.
        # In later phases it will use event-driven change detection.
        return self.run_full_sync(task_id)

    def run_targeted_sync(self, resource_def, resource_ids: list[str], task_id: str) -> dict:
        """Sync only specific resources by ID."""
        return self._sync_resource(resource_def, task_id, resource_ids)

    def _sync_resource(self, resource_def, task_id: str, resource_ids: Optional[list[str]] = None) -> dict:
        """Single resource type sync: CMDB fetch → AWS fetch → diff → write."""
        # Step 1: Fetch CMDB data
        self._log(f"  ① 读取 CMDB 存量 {resource_def.name} ...")
        cmdb_data = resource_def.model_cls.objects.all()
        cmdb_index = {item[resource_def.bind_key]: item for item in cmdb_data}
        self._log(f"     CMDB 存量 {len(cmdb_data)} 条")

        # Step 2: Fetch AWS data
        self._log(f"  ② 采集 AWS {resource_def.name} ...")
        aws_items = self._fetch_aws(resource_def)
        if resource_ids:
            aws_items = [i for i in aws_items if getattr(i, resource_def.bind_key, None) in resource_ids]
        self._log(f"     AWS 采集 {len(aws_items)} 条")

        # Step 3: Diff
        self._log(f"  ③ 对比 Diff ...")
        adds, updates, deletes, unchanged = self._diff(resource_def, cmdb_index, aws_items)
        self._log(f"     Diff: +{len(adds)} 新增 ~{len(updates)} 更新 -{len(deletes)} 删除 ={unchanged} 不变")

        # Step 4: Write
        self._log(f"  ④ 批量写入 ...")
        if adds:
            resource_def.model_cls.objects.bulk_create(adds)
        if updates:
            resource_def.model_cls.objects.bulk_update(updates, fields=list(updates[0].keys()) if updates else [])
        for del_item in deletes:
            resource_def.model_cls.objects.filter(**{resource_def.bind_key: del_item}).delete()
        self._log(f"     ✅ 写入完成")

        # Save checkpoint
        if self.checkpoint_mgr:
            cp = Checkpoint(
                task_id=task_id,
                phase=f"sync_{resource_def.name}",
                processed_count=len(aws_items),
                diff_pool={"add": len(adds), "update": len(updates), "delete": len(deletes)},
            )
            self.checkpoint_mgr.save(cp)

        return {
            "resource": resource_def.name,
            "added": len(adds),
            "updated": len(updates),
            "deleted": len(deletes),
            "unchanged": unchanged,
            "logs": list(self._logs),
        }

    def _fetch_aws(self, resource_def):
        """Call AWS API and return list of schema objects."""
        service, method = resource_def.aws_api.split(".")
        client = self.aws_session.client(service)
        api_method = getattr(client, method)

        paginator = client.get_paginator(method)
        items = []
        for page in paginator.paginate():
            # The response key varies by resource type — try common patterns
            for key in (f"{resource_def.name}s", resource_def.name.upper(), "Resources"):
                if key in page:
                    raw_list = page[key]
                    break
            else:
                # Fallback: return the first list value found
                raw_list = next(
                    (v for v in page.values() if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)),
                    [],
                )

            for raw in raw_list:
                try:
                    items.append(resource_def.schema_cls.from_aws_dict(raw))
                except Exception as e:
                    logger.warning(f"  Schema parse error: {e}")

        return items

    def _diff(self, resource_def, cmdb_index: dict, aws_items: list):
        """Compare AWS items against CMDB state and classify changes."""
        transform = resource_def.transform_cls()
        aws_keyed = {}
        for item in aws_items:
            key = getattr(item, resource_def.bind_key, None)
            if key:
                aws_keyed[key] = item

        aws_keys = set(aws_keyed.keys())
        cmdb_keys = set(cmdb_index.keys())

        new_keys = aws_keys - cmdb_keys
        removed_keys = cmdb_keys - aws_keys
        common_keys = aws_keys & cmdb_keys

        adds = []
        for key in new_keys:
            adds.append(to_cmdb_with_bind(transform, resource_def, aws_keyed[key]))

        updates = []
        for key in common_keys:
            aws_dict = to_cmdb_with_bind(transform, resource_def, aws_keyed[key])
            if aws_dict != cmdb_index[key]:
                aws_dict[resource_def.bind_key] = key
                updates.append(aws_dict)

        deletes = list(removed_keys)
        unchanged = len(common_keys) - len(updates)

        return adds, updates, deletes, unchanged

    def _build_associations(self):
        """Phase 2: resolve and persist resource associations.

        For Phase 1 this is a stub. Real implementation will:
        1. Load all resources in the group
        2. For each Association def, build the mapping
        3. Write association records to CMDB
        """
        logger.info("  Building associations (stub)")
        self._log("  🔗 关联关系构建完成 (stub)")
