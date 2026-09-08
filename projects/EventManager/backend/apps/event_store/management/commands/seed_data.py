"""
刷数据脚本 — 生成模拟事件数据

用法:
  python manage.py seed_data                       # 默认 1000 条
  python manage.py seed_data --total 5000          # 指定数量
  python manage.py seed_data --real 10             # 其中 10 条走真实 API 处理
  python manage.py seed_data --clear               # 先清空再刷
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.utils import timezone as tz

from apps.event_store.models import Event, EventLog, EventHandlerConfig, EventStatus


# ── 事件模板数据 ──────────────────────────────────────

EVENT_TEMPLATES = [
    # (event_type, source, detail_type, resource_prefix, status_weights, payload_builder)
    # status_weights: [completed%, failed%, dlq%, processing%, pending%]

    # AWS EC2
    {
        "pattern": "aws.ec2.*",
        "source": "aws",
        "events": [
            {"type": "aws.ec2.state-change", "resources": ["i-", "i-"]},
            {"type": "aws.ec2.instance-created", "resources": ["i-", "i-"]},
            {"type": "aws.ec2.instance-terminated", "resources": ["i-", "i-"]},
        ],
        "status_weights": [75, 10, 5, 5, 5],
        "payload": lambda: {
            "instance_id": f"i-{uuid.uuid4().hex[:8]}",
            "state": random.choice(["running", "stopped", "stopping", "pending", "terminated"]),
            "region": random.choice(["us-east-1", "ap-northeast-1", "eu-west-1", "us-west-2"]),
            "instance_type": random.choice(["t3.medium", "t3.large", "m5.large", "c5.xlarge"]),
        },
    },
    # AWS RDS
    {
        "pattern": "aws.rds.*",
        "source": "aws",
        "events": [
            {"type": "aws.rds.backup-completed", "resources": ["db-", "db-"]},
            {"type": "aws.rds.instance-created", "resources": ["db-", "db-"]},
            {"type": "aws.rds.failover", "resources": ["db-", "db-"]},
            {"type": "aws.rds.maintenance", "resources": ["db-", "db-"]},
        ],
        "status_weights": [80, 8, 4, 4, 4],
        "payload": lambda: {
            "db_instance": f"db-{random.choice(['prod', 'staging', 'dev'])}-{random.randint(1, 99):02d}",
            "category": random.choice(["backup", "maintenance", "creation", "failover", "resize"]),
            "region": random.choice(["us-east-1", "eu-west-1", "ap-southeast-1"]),
            "storage": random.choice([100, 200, 500, 1000]),
        },
    },
    # AWS S3
    {
        "pattern": "aws.s3.*",
        "source": "aws",
        "events": [
            {"type": "aws.s3.object-created", "resources": ["bucket-", "file-"]},
            {"type": "aws.s3.object-deleted", "resources": ["bucket-", "file-"]},
            {"type": "aws.s3.object-restored", "resources": ["bucket-", "file-"]},
        ],
        "status_weights": [85, 5, 2, 4, 4],
        "payload": lambda: {
            "bucket": f"app-{random.choice(['data', 'logs', 'backups', 'assets'])}-{random.randint(1, 99):02d}",
            "object_key": f"{random.choice(['uploads', 'docs', 'images', 'exports'])}/{uuid.uuid4().hex[:12]}.{random.choice(['pdf', 'jpg', 'json', 'csv'])}",
            "action": random.choice(["PUT", "POST", "DELETE", "COPY"]),
            "size": random.randint(1024, 10 * 1024 * 1024),
        },
    },
    # GitHub Webhook
    {
        "pattern": "webhook.github.*",
        "source": "github",
        "events": [
            {"type": "webhook.github.push", "resources": ["repo-"]},
            {"type": "webhook.github.pull_request", "resources": ["repo-"]},
            {"type": "webhook.github.issues", "resources": ["repo-"]},
            {"type": "webhook.github.release", "resources": ["repo-"]},
        ],
        "status_weights": [88, 5, 2, 3, 2],
        "payload": lambda: {
            "github_event": random.choice(["push", "pull_request", "issues", "release", "star"]),
            "repository": f"{random.choice(['my-org', 'team-a', 'open-source'])}/{random.choice(['frontend', 'backend', 'docs', 'infra'])}",
            "ref": random.choice(["main", "develop", "feature/new-api", "fix/bug-123"]),
            "commits": random.randint(1, 10),
        },
    },
    # Internal Health
    {
        "pattern": "internal.health",
        "source": "scheduler",
        "events": [
            {"type": "internal.health", "resources": ["svc-"]},
        ],
        "status_weights": [98, 1, 0, 0, 1],
        "payload": lambda: {
            "component": random.choice(["api", "celery-worker", "postgres", "redis", "rabbitmq"]),
            "check": random.choice(["ping", "db-connectivity", "queue-depth", "memory-usage"]),
        },
    },
    # Echo Test
    {
        "pattern": "echo.*",
        "source": "manual",
        "events": [
            {"type": "echo.test", "resources": ["test-"]},
            {"type": "echo.error", "resources": ["test-"]},
        ],
        "status_weights": [60, 20, 10, 5, 5],
        "payload": lambda: {
            "message": f"Test event #{random.randint(1, 9999)}",
            "simulate_error": random.random() < 0.2,
        },
    },
]


def pick_status(weights: list[int]) -> str:
    """根据权重随机选择状态"""
    statuses = [EventStatus.COMPLETED, EventStatus.FAILED, EventStatus.DLQ, EventStatus.PROCESSING, EventStatus.PENDING]
    r = random.randint(1, 100)
    cumulative = 0
    for i, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return statuses[i]
    return EventStatus.COMPLETED


def random_past_time(hours_back: int = 24) -> datetime:
    """生成过去 N 小时内的随机时间"""
    now = tz.now()
    seconds = random.randint(0, hours_back * 3600)
    return now - timedelta(seconds=seconds)


class Command(BaseCommand):
    help = "刷入模拟事件数据"

    def add_arguments(self, parser):
        parser.add_argument("--total", type=int, default=1000, help="总事件数 (默认 1000)")
        parser.add_argument("--real", type=int, default=0, help="走真实 API 处理的事件数 (默认 0)")
        parser.add_argument("--clear", action="store_true", help="先清空现有数据")

    def handle(self, *args, **options):
        total = options["total"]
        real_count = options["real"]
        do_clear = options["clear"]

        if do_clear:
            self.stdout.write("🗑️  清空现有数据...")
            Event.objects.all().delete()
            EventLog.objects.all().delete()
            self.stdout.write("   ✅ 已清空")

        self.stdout.write(f"\n📦 开始生成 {total} 条模拟事件...\n")

        # 批量创建（直接写 DB，不走 Celery）
        batch_size = 100
        events_batch = []
        logs_batch = []

        for i in range(1, total + 1):
            template = random.choice(EVENT_TEMPLATES)
            event_info = random.choice(template["events"])
            resource_id = event_info["resources"][0] + uuid.uuid4().hex[:10]
            received_at = random_past_time()
            status = pick_status(template["status_weights"])
            payload = template["payload"]()

            # 如果是 echo.error 类型且有 simulate_error，状态直接置为 failed
            if payload.get("simulate_error"):
                status = EventStatus.FAILED

            event = Event(
                event_type=event_info["type"],
                source=template["source"],
                detail_type=event_info["type"].split(".")[-1],
                resource_id=resource_id,
                raw_payload=payload,
                status=status,
                received_at=received_at,
                processed_at=received_at + timedelta(seconds=random.uniform(0.1, 3.0)) if status in (EventStatus.COMPLETED, EventStatus.FAILED, EventStatus.DLQ) else None,
                retry_count=random.randint(0, 3) if status == EventStatus.FAILED else (random.randint(3, 5) if status == EventStatus.DLQ else 0),
                max_retries=5,
                handler=template["pattern"].replace("*", "").rstrip(".").upper() + "Handler" if status == EventStatus.COMPLETED else "",
                worker_id=f"worker-{random.randint(1, 8):02d}" if status != EventStatus.PENDING else "",
                error_message="Simulated processing error" if status in (EventStatus.FAILED, EventStatus.DLQ) else "",
            )
            events_batch.append(event)

            # 生成对应的 EventLog
            logs_batch.append(EventLog(event=event, action=EventLog.Action.RECEIVED, detail={"source": template["source"]}, created_at=received_at))
            if status != EventStatus.PENDING:
                logs_batch.append(EventLog(event=event, action=EventLog.Action.PROCESSING, detail={"worker": event.worker_id}, created_at=received_at + timedelta(seconds=0.1)))
            if status == EventStatus.COMPLETED:
                logs_batch.append(EventLog(event=event, action=EventLog.Action.COMPLETED, detail={"result": "OK"}, created_at=event.processed_at))
            elif status == EventStatus.FAILED:
                logs_batch.append(EventLog(event=event, action=EventLog.Action.FAILED, detail={"error": event.error_message, "retry_count": event.retry_count}, created_at=event.processed_at or (received_at + timedelta(seconds=1))))
            elif status == EventStatus.DLQ:
                logs_batch.append(EventLog(event=event, action=EventLog.Action.FAILED, detail={"error": event.error_message, "retry_count": event.retry_count}, created_at=event.processed_at or (received_at + timedelta(seconds=1))))
                logs_batch.append(EventLog(event=event, action=EventLog.Action.DLQ, detail={"error": event.error_message, "reason": "retries_exhausted"}, created_at=(event.processed_at or (received_at + timedelta(seconds=1))) + timedelta(seconds=0.1)))

            # 批量写入
            if len(events_batch) >= batch_size:
                self._bulk_insert(events_batch, logs_batch, i, total)
                events_batch = []
                logs_batch = []

        # 剩余数据
        if events_batch:
            self._bulk_insert(events_batch, logs_batch, total, total)

        # Handler 注册表配置
        if not EventHandlerConfig.objects.exists():
            EventHandlerConfig.objects.create(
                name="EchoHandler",
                event_type_pattern="*",
                handler_class="handlers.internal.echo_handler.EchoHandler",
                timeout=60,
                max_retries=5,
                is_active=True,
                description="兜底 Handler",
            )

        self.stdout.write(f"\n✅ 完成! 共生成 {total} 条事件")
        self.stdout.write(f"   📊 状态分布: ", ending="")
        for s, c in Event.objects.values("status").annotate(count=models.Count("id")).values_list("status", "count"):
            self.stdout.write(f"{s}={c} ", ending="")
        self.stdout.write("")

    def _bulk_insert(self, events, logs, current, total):
        with transaction.atomic():
            Event.objects.bulk_create(events, ignore_conflicts=True)
            EventLog.objects.bulk_create(logs, ignore_conflicts=True)
        self.stdout.write(f"   📝 已写入 {current}/{total} 条...", ending="\r")
        self.stdout.flush()