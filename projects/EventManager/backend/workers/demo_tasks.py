"""
Demo 任务 —— 用于测试模块的人工触发任务
这些是真实可运行的 Celery 任务，模拟不同耗时的场景
"""

import json
import logging
import os
import random
import ssl
import time
import uuid
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from celery import shared_task

logger = logging.getLogger(__name__)

# ─── 输出目录 ──────────────────────────────────────
# 支持通过环境变量 OUTPUT_DIR 覆盖（Docker 中共享卷挂载在 /output）
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(Path(__file__).resolve().parent.parent.parent / "output")))


def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def _write_artifact(filename: str, data: dict) -> str:
    """将任务产物写入 output 目录，返回文件名"""
    _ensure_output_dir()
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("[Demo] 产物已写入: %s", filename)
    return filename


def _create_event(event_type: str, source: str, detail_type: str, raw_payload: dict) -> str:
    """在 Event 表中创建一条记录，返回 event_id"""
    from apps.event_store.models import Event, EventLog, EventStatus

    event = Event.objects.create(
        id=uuid.uuid4(),
        event_type=event_type,
        source=source,
        detail_type=detail_type,
        resource_id=f"test-lab-{event_type}",
        raw_payload=raw_payload,
        status=EventStatus.COMPLETED,
        handler="demo-task",
        worker_id="test-lab",
    )
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.RECEIVED,
        detail={"source": source, "trigger": "test-lab"},
    )
    EventLog.objects.create(
        event=event,
        action=EventLog.Action.COMPLETED,
        detail={"source": source},
    )
    return str(event.id)


def _update_event(event_id: str, **kwargs) -> None:
    """更新 Event 记录"""
    from apps.event_store.models import Event

    try:
        Event.objects.filter(id=event_id).update(**kwargs)
    except Exception:
        logger.warning("更新 Event %s 失败", event_id)


# ═══════════════════════════════════════════════════════
# 快任务：从公开 API 爬取数据并写入文件
# ═══════════════════════════════════════════════════════

@shared_task(bind=True, soft_time_limit=30, time_limit=60)
def fetch_and_process(self, batch: int = 1, total: int = 1, batch_id: str = ""):
    """
    快任务：从 JSONPlaceholder API 爬取帖子数据（单个批次）

    每个任务只处理 1 个批次，多个任务并发执行实现并行处理
    """
    _ensure_output_dir()
    task_id = self.request.id

    logger.info("[Demo] fetch_and_process 开始，batch=%d/%d, task_id=%s, batch_id=%s", batch, total, task_id, batch_id)

    # 为这批数据创建 Event 记录
    event_id = _create_event(
        event_type="demo.fetch_posts",
        source="test-lab",
        detail_type="fast-task",
        raw_payload={"batch": batch, "total": total, "task_id": task_id, "batch_id": batch_id},
    )

    try:
        # 真实 HTTP 请求
        url = f"https://jsonplaceholder.typicode.com/posts?_limit=10&_start={(batch - 1) * 10}"
        req = urllib.request.Request(url, headers={"User-Agent": "EventFlow-Demo/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as resp:
            posts = json.loads(resp.read().decode())

        # 提取 & 处理
        processed = []
        all_words = []
        for post in posts:
            words = post["title"].split()
            all_words.extend(words)
            processed.append({
                "id": post["id"],
                "title": post["title"],
                "body_length": len(post["body"]),
                "word_count": len(post["title"].split()),
                "user_id": post["userId"],
            })

        # 词频统计
        word_freq = {}
        for w in all_words:
            w_lower = w.lower().strip(".,!?:;")
            if len(w_lower) > 2:
                word_freq[w_lower] = word_freq.get(w_lower, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:5]

        # 更新进度
        self.update_state(
            state="PROGRESS",
            meta={"current": batch, "total": total, "status": f"批次 {batch}/{total} 完成"},
        )

        # 写入产物文件（JSON）
        filename = f"fetched_posts_{batch_id or 'batch'}_{batch:03d}.json"
        _write_artifact(filename, {
            "task_id": task_id,
            "batch_id": batch_id,
            "batch": batch,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
            "total_posts": len(posts),
            "posts": processed,
            "top_words": top_words,
        })

        result = {
            "success": True,
            "batch": batch,
            "total": total,
            "batch_id": batch_id,
            "event_id": event_id,
            "output_filename": filename,
            "total_posts": len(posts),
            "top_words": top_words,
            "source_url": url,
        }

    except Exception as exc:
        result = {"success": False, "batch": batch, "error": str(exc)}
        logger.error("[Demo] 批次 %d 失败: %s", batch, exc)

    # 更新 Event 记录（写入结果与产物文件名，供详情页展示）
    _update_event(event_id, raw_payload={
        "result": result,
        "task_id": task_id,
        "batch": batch,
        "batch_id": batch_id,
        "output_filename": result.get("output_filename", ""),
    })

    logger.info("[Demo] fetch_and_process 完成，batch=%d/%d", batch, total)
    return result


# ═══════════════════════════════════════════════════════
# 慢任务：模拟数据处理 / 报告生成
# ═══════════════════════════════════════════════════════

@shared_task(bind=True, soft_time_limit=300, time_limit=600)
def generate_report(self, batch: int = 1, total: int = 1, batch_id: str = ""):
    """
    慢任务：模拟生成分析报告（单条报告）

    每个任务只生成 1 条报告，多个任务并发执行实现并行处理
    """
    _ensure_output_dir()
    task_id = self.request.id

    logger.info("[Demo] generate_report 开始，batch=%d/%d, task_id=%s, batch_id=%s", batch, total, task_id, batch_id)

    # 为这条报告创建 Event 记录
    event_id = _create_event(
        event_type="demo.generate_report",
        source="test-lab",
        detail_type="slow-task",
        raw_payload={"report_index": batch, "total": total, "task_id": task_id, "batch_id": batch_id},
    )

    step_duration = random.uniform(3, 8)

    # 模拟多步骤处理
    steps = ["读取数据源", "数据清洗", "统计计算", "生成报告"]
    for step_idx, step_name in enumerate(steps):
        time.sleep(step_duration / len(steps))
        self.update_state(
            state="PROGRESS",
            meta={
                "current": batch,
                "total": total,
                "step": step_name,
                "step_progress": f"{step_idx + 1}/{len(steps)}",
                "elapsed_sec": round(step_duration * (step_idx + 1) / len(steps), 1),
            },
        )

    # 生成模拟报告内容
    ts = datetime.now().strftime("%Y%m%d")
    report_id = f"RPT-{ts}-{batch:03d}"
    report = {
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_points": random.randint(500, 5000),
        "metrics": {
            "avg_response_time_ms": round(random.uniform(10, 200), 2),
            "error_rate": round(random.uniform(0, 0.05), 4),
            "throughput_rps": round(random.uniform(50, 500), 1),
            "p99_latency_ms": round(random.uniform(100, 1000), 2),
        },
        "summary": f"在 {step_duration:.1f} 秒内处理了 {random.randint(500, 5000)} 个数据点",
    }

    # 写入产物文件（JSON）
    filename = f"report_{batch_id or 'batch'}_{batch:03d}.json"
    _write_artifact(filename, {
        "task_id": task_id,
        "batch_id": batch_id,
        "batch": batch,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "total_reports": 1,
        "reports": [report],
    })

    # 更新 Event 记录（写入报告与产物文件名，供详情页展示）
    _update_event(event_id, raw_payload={
        "report": report,
        "task_id": task_id,
        "batch": batch,
        "batch_id": batch_id,
        "output_filename": filename,
    })

    logger.info("[Demo] generate_report 完成，batch=%d/%d, report_id=%s", batch, total, report_id)
    return {
        "success": True,
        "batch": batch,
        "total": total,
        "batch_id": batch_id,
        "event_id": event_id,
        "output_filename": filename,
        "total_reports": 1,
        "report_id": report_id,
        "data_points": report["data_points"],
        "metrics": report["metrics"],
    }
