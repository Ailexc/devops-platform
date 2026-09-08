"""
result_builder — 统一任务结果构造器。

所有任务（测试任务 / AWS 同步 / 关系任务）返回同构的标准结果结构，
前端一套代码即可渲染指标卡片、产物预览与执行日志：

    {
      "status":    "success" | "failed" | "partial",
      "summary":   "一句话摘要",
      "duration":  "3.2s",
      "logs":      ["HH:MM:SS 阶段日志", ...],
      "stats":     [{"key", "label", "value", "unit"}, ...],
      "artifacts": [{"name", "path", "kind", "size"}, ...],
      "details":   { 任务特有完整数据 }
    }
"""

import os
import time
from datetime import datetime


class ResultBuilder:
    """统一结果构造器：日志 + 指标 + 产物 + 摘要。"""

    def __init__(self, status: str = "success"):
        self._status = status
        self._logs: list[str] = []
        self._stats: list[dict] = []
        self._artifacts: list[dict] = []
        self._details: dict = {}
        self._start = time.time()

    # ── 日志 ──

    def log(self, msg: str):
        """记录一条带时间戳的执行日志（同时追加到 logs）。"""
        ts = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"{ts} {msg}")
        return self

    def merge_logs(self, logs: list[str]):
        """合并外部已收集的日志（如 sync pipeline 的 self._logs）。"""
        self._logs = list(logs or [])
        return self

    # ── 指标 ──

    def add_stat(self, key: str, label: str, value, unit: str = ""):
        self._stats.append({"key": key, "label": label, "value": value, "unit": unit})
        return self

    def add_stats(self, stats: list[dict]):
        for s in stats:
            self.add_stat(s.get("key", ""), s.get("label", s.get("key", "")), s.get("value"), s.get("unit", ""))
        return self

    # ── 产物 ──

    def add_artifact(self, path: str, kind: str = ""):
        """按路径添加产物（自动取文件名与大小）。"""
        if not path or not os.path.exists(path):
            return self
        self._artifacts.append({
            "name": os.path.basename(path),
            "path": path,
            "kind": kind or os.path.splitext(path)[1].lstrip("."),
            "size": os.path.getsize(path),
        })
        return self

    # ── 状态 ──

    def fail(self, error: str):
        self._status = "failed"
        self._details["error"] = str(error)[:500]
        return self

    def mark(self, status: str):
        self._status = status
        return self

    # ── 组装 ──

    def build(self, summary: str, duration: str | None = None, extra: dict | None = None) -> dict:
        result = {
            "status": self._status,
            "summary": summary,
            "duration": duration or f"{time.time() - self._start:.2f}s",
            "logs": self._logs,
            "stats": self._stats,
            "artifacts": self._artifacts,
            "details": {**self._details, **(extra or {})},
        }
        return result


def build_resource_result(resource_name: str, diff: dict, logs: list[str] | None = None,
                          duration: str | None = None, status: str = "success") -> dict:
    """资源同步结果的统一包装：diff 四项 → stats + details。

    供各资源模块 celery_tasks 使用，保证子记录 result 是同构标准结构。
    """
    b = ResultBuilder(status=status)
    b.merge_logs(logs)
    b.add_stats([
        {"key": "added", "label": "新增", "value": diff.get("added", 0), "unit": "条"},
        {"key": "updated", "label": "更新", "value": diff.get("updated", 0), "unit": "条"},
        {"key": "deleted", "label": "删除", "value": diff.get("deleted", 0), "unit": "条"},
        {"key": "unchanged", "label": "不变", "value": diff.get("unchanged", 0), "unit": "条"},
    ])
    summary = (
        f"{resource_name} 同步: "
        f"+{diff.get('added', 0)} 新增 ~{diff.get('updated', 0)} 更新 "
        f"-{diff.get('deleted', 0)} 删除 ={diff.get('unchanged', 0)} 不变"
    )
    return b.build(
        summary,
        duration=duration,
        extra={
            "resource": resource_name,
            "added": diff.get("added", 0),
            "updated": diff.get("updated", 0),
            "deleted": diff.get("deleted", 0),
            "unchanged": diff.get("unchanged", 0),
        },
    )
