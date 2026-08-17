"""
执行记录内存存储（demo 级：进程内，随服务重启清空）

为每次执行维护：
- 状态机：running → success / failed
- 日志环形缓冲（带自增 index，供增量读取 / SSE 消费）
- 新日志事件信号（让 SSE 流能"即时"推送而非固定轮询）
"""

import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import MAX_LOG_LINES


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Execution:
    def __init__(self, op: str, params: Dict[str, Any]):
        self.id = uuid.uuid4().hex
        self.op = op
        self.params = params
        self.status = "running"
        self.created_at = _now_iso()
        self.finished_at: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

        self._logs: deque = deque(maxlen=MAX_LOG_LINES)
        self._log_index = 0
        self._lock = threading.Lock()
        self._new_log = threading.Event()
        self._done_event = threading.Event()

        self.log("info", f"[executor] 收到执行请求 op={op}")

    # ── 日志 ────────────────────────────────────────────
    def log(self, level: str, message: str):
        with self._lock:
            entry = {"index": self._log_index, "ts": _now_iso(), "level": level, "message": message}
            self._log_index += 1
            self._logs.append(entry)
        self._new_log.set()

    def logs_after(self, index: int) -> list:
        with self._lock:
            return [e for e in self._logs if e["index"] > index]

    def wait_new_log(self, timeout: float) -> bool:
        """等待新日志；超时返回 False"""
        return self._new_log.wait(timeout)

    def clear_new_log_flag(self):
        self._new_log.clear()

    # ── 状态 ────────────────────────────────────────────
    def finish(self, status: str, result: Optional[dict] = None, error: Optional[str] = None):
        with self._lock:
            self.status = status
            self.result = result
            self.error = error
            self.finished_at = _now_iso()
        self._new_log.set()
        self._done_event.set()

    def wait_done(self, timeout: Optional[float] = None):
        self._done_event.wait(timeout)


# 全局执行记录表
_store: Dict[str, Execution] = {}
_store_lock = threading.Lock()


def create_execution(op: str, params: dict) -> Execution:
    ex = Execution(op, params)
    with _store_lock:
        _store[ex.id] = ex
    return ex


def get_execution(exec_id: str) -> Optional[Execution]:
    with _store_lock:
        return _store.get(exec_id)
