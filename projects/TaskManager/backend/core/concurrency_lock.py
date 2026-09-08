"""
concurrency_lock — 多级并发锁（资源集合 + Redis 交集检测）。

背景：多级下发（区域/资源组/资源）存在层级覆盖关系，同一资源同时
只能有一个同步在执行（防止 cron 与人工叠加、区域级与组级重叠）。

方案：
  1. 每个任务"展开"为覆盖的资源集合（区域级 = 全区资源+关系）
  2. 下发时遍历执行中集合，SINTER 检查交集 → 有交集拒绝(409)，无交集加锁
  3. 任务完成/失败 → 释放锁；Redis TTL 兜底防异常死锁

资源 key 格式：
  - 资源:    `{group}:{resource}`        e.g. 计算:EC2
  - 关系:    `{group}:rel:{source}:{target}`  e.g. 计算:rel:EC2:VPC
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 4 * 3600  # 4h 兜底，防异常死锁


class ConcurrencyLockManager:
    """Redis 实现的多级并发锁。"""

    def __init__(self, redis_url: str | None = None, ttl: int = DEFAULT_TTL_SECONDS):
        self._redis = redis.Redis.from_url(redis_url or settings.REDIS_URL, decode_responses=True)
        self.ttl = ttl

    # ── key 构造 ──
    def _active_key(self):
        return "cmdb:locks:active"

    def _set_key(self, lock_id: str):
        return f"cmdb:locks:set:{lock_id}"

    def _meta_key(self, lock_id: str):
        return f"cmdb:locks:meta:{lock_id}"

    # ── 核心操作 ──

    def acquire(self, account: str, region: str, resource_keys: list[str],
                scope: str = "", target: str = "", ttl: int | None = None) -> dict | None:
        """尝试加锁。成功返回锁信息 dict；冲突返回 None。

        resource_keys 为空时不加锁（无需保护）。
        """
        keys = sorted(set(resource_keys))
        if not keys:
            return {"lock_id": None, "account": account, "region": region, "resource_keys": []}

        r = self._redis
        lock_id = str(uuid.uuid4())[:12]

        # 1. 遍历所有执行中锁，检查交集
        active_ids = list(r.smembers(self._active_key()))
        conflicts = []
        for active_id in active_ids:
            # 临时把候选 keys 与活动锁集合求交集
            tmp = f"cmdb:locks:probe:{uuid.uuid4().hex}"
            try:
                r.sadd(tmp, *keys)
                r.expire(tmp, 30)
                inter = list(r.sinter(tmp, self._set_key(active_id)))
            finally:
                r.delete(tmp)
            if inter:
                conflicts.append(active_id)

        if conflicts:
            logger.info(
                f"concurrency_lock: CONFLICT {account}/{region} ({scope}/{target}) "
                f"vs locks {conflicts} over {len(inter)} shared resources"
            )
            return None

        # 2. 无交集 → 加锁
        pipe = r.pipeline()
        pipe.sadd(self._set_key(lock_id), *keys)
        pipe.expire(self._set_key(lock_id), ttl or self.ttl)
        pipe.hset(self._meta_key(lock_id), mapping={
            "lock_id": lock_id,
            "account": account,
            "region": region,
            "scope": scope,
            "target": target,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "resource_keys": json.dumps(keys, ensure_ascii=False),
        })
        pipe.expire(self._meta_key(lock_id), ttl or self.ttl)
        pipe.sadd(self._active_key(), lock_id)
        pipe.execute()

        logger.info(f"concurrency_lock: acquired {lock_id} for {account}/{region} ({scope}/{target}) {len(keys)} resources")
        return {
            "lock_id": lock_id,
            "account": account,
            "region": region,
            "scope": scope,
            "target": target,
            "resource_keys": keys,
        }

    def release(self, lock_id: str | None):
        """释放锁（任务完成/失败时调用）。lock_id 为 None 时忽略。"""
        if not lock_id:
            return
        r = self._redis
        pipe = r.pipeline()
        pipe.delete(self._set_key(lock_id))
        pipe.delete(self._meta_key(lock_id))
        pipe.srem(self._active_key(), lock_id)
        pipe.execute()
        logger.info(f"concurrency_lock: released {lock_id}")

    def is_locked(self, resource_keys: list[str]) -> dict | None:
        """查询某资源集合是否被任一锁覆盖，返回冲突锁信息或 None。"""
        keys = sorted(set(resource_keys))
        if not keys:
            return None
        r = self._redis
        tmp = f"cmdb:locks:probe:{uuid.uuid4().hex}"
        try:
            r.sadd(tmp, *keys)
            r.expire(tmp, 30)
            for active_id in list(r.smembers(self._active_key())):
                inter = list(r.sinter(tmp, self._set_key(active_id)))
                if inter:
                    return self._meta(active_id)
        finally:
            r.delete(tmp)
        return None

    def list_active(self) -> list[dict]:
        """返回所有执行中的锁（供大盘/前端展示锁状态）。"""
        r = self._redis
        result = []
        for lock_id in list(r.smembers(self._active_key())):
            meta = self._meta(lock_id)
            if meta:
                result.append(meta)
        return result

    def _meta(self, lock_id: str) -> dict | None:
        raw = self._redis.hgetall(self._meta_key(lock_id))
        if not raw:
            return None
        meta = dict(raw)
        try:
            meta["resource_keys"] = json.loads(meta.get("resource_keys") or "[]")
        except (ValueError, TypeError):
            meta["resource_keys"] = []
        return meta


# 模块级单例
lock_manager = ConcurrencyLockManager()
