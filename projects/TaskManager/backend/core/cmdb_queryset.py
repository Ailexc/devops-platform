"""
CmdbQuerySet — Redis 持久化的虚拟 ORM（跨 prefork 进程共享的全局 CMDB 存储）。

为什么是 Redis：
  - Celery prefork 池中每个 worker 进程独立内存，进程内 dict 存储会导致
    Wave1 写入的数据在 Wave2 关系任务中不可见（"关系基于全局 CMDB"失效）
  - Redis 天然跨进程共享，且与真实架构中"CMDB 独立存储"的语义一致

存储结构：
  key: cmdb:store:{model_name}  → Redis LIST，元素为 JSON 序列化的资源 dict
  写操作通过 redis-py Lock 互斥，避免并发 region 同步相互覆盖。
"""

import json

import redis
from django.conf import settings


class CmdbQuerySet:
    """Redis 持久化的虚拟 queryset，接口与 Django QuerySet 子集一致。"""

    def __init__(self, model_name: str):
        self._model_name = model_name
        self._storage: list[dict] | None = None  # None=未过滤（全量）；非 None=过滤快照
        self._filters: dict = {}
        self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._key = f"cmdb:store:{model_name}"

    # ── 内部读写 ──

    def _read(self) -> list[dict]:
        raw = self._redis.lrange(self._key, 0, -1)
        return [json.loads(x) for x in raw]

    def _write(self, items: list[dict]) -> None:
        with self._redis.pipeline() as pipe:
            pipe.delete(self._key)
            if items:
                pipe.rpush(self._key, *[json.dumps(i, ensure_ascii=False) for i in items])
            pipe.execute()

    def _with_lock(self, fn):
        lock = self._redis.lock(f"{self._key}:lock", timeout=15, blocking_timeout=15)
        with lock:
            return fn()

    def _match(self, item: dict) -> bool:
        return all(item.get(key) == val for key, val in self._filters.items())

    # ── 查询 ──

    def all(self):
        return self._read()

    def filter(self, **kwargs):
        if self._storage is None:
            self._filters = dict(kwargs)
            items = [item for item in self._read() if self._match(item)]
        else:
            # 对已过滤快照再次过滤
            self._filters.update(kwargs)
            items = [item for item in self._storage if self._match(item)]
        qs = CmdbQuerySet(self._model_name)
        qs._storage = items
        qs._filters = dict(self._filters)
        return qs

    def get(self, **kwargs):
        result = self.filter(**kwargs).all()
        if len(result) == 0:
            raise self.model.DoesNotExist(f"{self._model_name} matching {kwargs} not found")
        if len(result) > 1:
            raise self.model.MultipleObjectsReturned(
                f"{self._model_name} matching {kwargs} returned {len(result)}"
            )
        return result[0]

    # ── 写 ──

    def create(self, **kwargs):
        record = {**kwargs}
        return self._with_lock(lambda: self._create_locked(record))

    def _create_locked(self, record: dict) -> dict:
        items = self._read()
        items.append(record)
        self._write(items)
        return record

    def bulk_create(self, records: list[dict]):
        return self._with_lock(lambda: self._bulk_create_locked(records))

    def _bulk_create_locked(self, records: list[dict]) -> list[dict]:
        # 不注入内部 id 字段：保证二次同步时转换产物与存储内容完全一致（幂等）
        items = self._read()
        items.extend(records)
        self._write(items)
        return records

    def update(self, **kwargs):
        return self._with_lock(lambda: self._update_locked(kwargs))

    def _update_locked(self, kwargs) -> int:
        items = self._read()
        count = 0
        for item in items:
            if self._match(item):
                item.update(kwargs)
                count += 1
        if count:
            self._write(items)
        return count

    def bulk_update(self, records: list[dict], fields: list[str]):
        return self._with_lock(lambda: self._bulk_update_locked(records, fields))

    def _bulk_update_locked(self, records: list[dict], fields: list[str]) -> int:
        items = self._read()
        by_cloud = {it.get("cloud_id"): it for it in items}
        count = 0
        for r in records:
            target = by_cloud.get(r.get("cloud_id"))
            if target:
                for f in fields:
                    if f in r:
                        target[f] = r[f]
                count += 1
        if count:
            self._write(items)
        return count

    def delete(self):
        """删除当前 queryset 命中的记录（未过滤则清空整表）。"""
        return self._with_lock(lambda: self._delete_locked())

    def _delete_locked(self) -> int:
        if self._storage is not None and self._filters:
            # 过滤快照：从 Redis 中移除内容一致（完全相同）的记录
            items = [it for it in self._read() if it not in self._storage]
            count = len(self._storage)
        else:
            items = []
            count = 0
        self._write(items)
        return count

    def count(self):
        return len(self._read())

    def exists(self):
        return self._redis.llen(self._key) > 0

    class model:
        class DoesNotExist(Exception):
            pass

        class MultipleObjectsReturned(Exception):
            pass
