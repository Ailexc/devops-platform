"""
Checkpoint Manager — enables resume / continuation for long-running sync jobs.

Each sync pipeline records checkpoints at key stages so that if the process
is interrupted, it can resume from the last checkpoint rather than restarting.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
import redis


@dataclass
class Checkpoint:
    task_id: str
    phase: str                      # e.g. "cmdb_fetch", "aws_fetch", "diff", "write"
    cursor: Optional[str] = None    # pagination token / page number
    processed_count: int = 0
    diff_pool: dict = field(default_factory=lambda: {"add": [], "update": [], "delete": []})
    timestamp: float = field(default_factory=time.time)


class CheckpointManager:
    """Stores and retrieves checkpoints in Redis."""

    KEY_PREFIX = "checkpoint:sync:"

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def save(self, cp: Checkpoint):
        key = f"{self.KEY_PREFIX}{cp.task_id}"
        self._redis.hset(key, cp.phase, json.dumps(asdict(cp)))
        self._redis.expire(key, 86400)  # 24h TTL

    def load(self, task_id: str, phase: str) -> Optional[Checkpoint]:
        key = f"{self.KEY_PREFIX}{task_id}"
        raw = self._redis.hget(key, phase)
        if raw is None:
            return None
        data = json.loads(raw)
        return Checkpoint(**data)

    def delete(self, task_id: str):
        key = f"{self.KEY_PREFIX}{task_id}"
        self._redis.delete(key)

    def list_phases(self, task_id: str) -> list[str]:
        key = f"{self.KEY_PREFIX}{task_id}"
        return [p.decode() for p in self._redis.hkeys(key)]
