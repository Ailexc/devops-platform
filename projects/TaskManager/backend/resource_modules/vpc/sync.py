"""
VPC sync pipeline.
"""

import logging
from datetime import datetime
from typing import Optional

from core.retry_engine import RetryEngine
from core.checkpoint_manager import CheckpointManager
from core.transform_utils import to_cmdb_with_bind
from .resource import VPC, Subnet, NETWORK_GROUP

logger = logging.getLogger(__name__)


class VPCSyncPipeline:
    def __init__(self, account_name: str, region: str, aws_session, checkpoint_mgr: CheckpointManager | None = None):
        self.account_name = account_name
        self.region = region
        self.aws_session = aws_session
        self.checkpoint_mgr = checkpoint_mgr
        self.retry = RetryEngine(max_retries=3)
        self._logs: list[str] = []

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"{ts} {msg}")
        logger.info(msg)

    def run_full_sync(self, task_id: str) -> dict:
        self._log(f"🚀 开始同步 {self.account_name}/{self.region} 网络组资源")
        results = {}
        for resource_def in NETWORK_GROUP:
            self._log(f"  ▶️  同步 {resource_def.name} ...")
            results[resource_def.name] = self._sync_resource(resource_def, task_id)
            self._log(f"  ✅ {resource_def.name} 同步完成")
        return results

    def _sync_resource(self, resource_def, task_id: str, resource_ids: Optional[list[str]] = None) -> dict:
        self._log(f"  ① 读取 CMDB 存量 {resource_def.name} ...")
        cmdb_data = resource_def.model_cls.objects.all()
        cmdb_index = {item[resource_def.bind_key]: item for item in cmdb_data}
        self._log(f"     CMDB 存量 {len(cmdb_data)} 条")

        self._log(f"  ② 采集 AWS {resource_def.name} ...")
        service, method = resource_def.aws_api.split(".")
        client = self.aws_session.client(service)
        paginator = client.get_paginator(method)

        aws_items = []
        for page in paginator.paginate():
            for key in (f"{resource_def.name}s", resource_def.name.upper(), "Vpcs", "Subnets"):
                if key in page:
                    raw_list = page[key]
                    break
            else:
                raw_list = next(
                    (v for v in page.values() if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)),
                    [],
                )
            for raw in raw_list:
                try:
                    aws_items.append(resource_def.schema_cls.from_aws_dict(raw))
                except Exception as e:
                    logger.warning(f"  Schema parse error: {e}")

        if resource_ids:
            aws_items = [i for i in aws_items if getattr(i, resource_def.bind_key, None) in resource_ids]
        self._log(f"     AWS 采集 {len(aws_items)} 条")

        self._log(f"  ③ 对比 Diff ...")
        transform = resource_def.transform_cls()
        aws_keyed = {}
        for item in aws_items:
            key = getattr(item, resource_def.bind_key, None)
            if key:
                aws_keyed[key] = item

        aws_keys = set(aws_keyed.keys())
        cmdb_keys = set(cmdb_index.keys())

        adds = [to_cmdb_with_bind(transform, resource_def, aws_keyed[k]) for k in (aws_keys - cmdb_keys)]
        updates = []
        for k in (aws_keys & cmdb_keys):
            d = to_cmdb_with_bind(transform, resource_def, aws_keyed[k])
            if d != cmdb_index[k]:
                d[resource_def.bind_key] = k
                updates.append(d)
        deletes = list(cmdb_keys - aws_keys)
        unchanged = len(aws_keys & cmdb_keys) - len(updates)
        self._log(f"     Diff: +{len(adds)} 新增 ~{len(updates)} 更新 -{len(deletes)} 删除 ={unchanged} 不变")

        self._log(f"  ④ 批量写入 ...")
        if adds:
            resource_def.model_cls.objects.bulk_create(adds)
        if updates:
            resource_def.model_cls.objects.bulk_update(updates, fields=list(updates[0].keys()) if updates else [])
        for d in deletes:
            resource_def.model_cls.objects.filter(**{resource_def.bind_key: d}).delete()
        self._log(f"     ✅ 写入完成")

        return {
            "resource": resource_def.name,
            "added": len(adds),
            "updated": len(updates),
            "deleted": len(deletes),
            "unchanged": unchanged,
            "logs": list(self._logs),
        }
