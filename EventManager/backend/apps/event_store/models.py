import uuid
from django.db import models


class EventStatus(models.TextChoices):
    PENDING = "pending", "待处理"
    PROCESSING = "processing", "处理中"
    COMPLETED = "completed", "已完成"
    FAILED = "failed", "失败"
    DLQ = "dlq", "死信"


class Event(models.Model):
    """核心事件模型"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField("事件类型", max_length=128, db_index=True)
    source = models.CharField("事件来源", max_length=64, db_index=True)
    detail_type = models.CharField("详细分类", max_length=64, blank=True, default="")
    resource_id = models.CharField("资源 ID", max_length=256, blank=True, default="")
    raw_payload = models.JSONField("原始数据", default=dict, blank=True)
    status = models.CharField(
        "状态", max_length=32, choices=EventStatus.choices,
        default=EventStatus.PENDING, db_index=True,
    )
    trace_id = models.UUIDField("追踪 ID", default=uuid.uuid4, editable=False, db_index=True)
    retry_count = models.IntegerField("已重试次数", default=0)
    max_retries = models.IntegerField("最大重试次数", default=5)
    handler = models.CharField("处理器", max_length=128, blank=True, default="")
    worker_id = models.CharField("工作节点", max_length=64, blank=True, default="")
    error_message = models.TextField("错误信息", blank=True, default="")
    received_at = models.DateTimeField("接收时间", auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField("处理时间", null=True, blank=True)

    class Meta:
        verbose_name = "事件"
        verbose_name_plural = "事件"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.event_type} [{self.status}]"


class EventLog(models.Model):
    """事件处理日志 (append-only)"""

    class Action(models.TextChoices):
        RECEIVED = "received", "已接收"
        ENQUEUED = "enqueued", "投递队列"
        ROUTED = "routed", "路由匹配"
        PROCESSING = "processing", "开始处理"
        RETRYING = "retrying", "自动重试"
        COMPLETED = "completed", "处理完成"
        FAILED = "failed", "处理失败"
        DLQ = "dlq", "转入死信"
        RETRY_MANUAL = "retry_manual", "手动重试"
        REPLAYED = "replayed", "已回放"

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="logs",
        db_index=True,
    )
    action = models.CharField("操作", max_length=32, choices=Action.choices)
    detail = models.JSONField("详细信息", default=dict, blank=True)
    created_at = models.DateTimeField("日志时间", auto_now_add=True)

    class Meta:
        verbose_name = "事件日志"
        verbose_name_plural = "事件日志"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.event_id} - {self.action}"


class EventHandlerConfig(models.Model):
    """Handler 注册表"""

    name = models.CharField("名称", max_length=128, unique=True)
    event_type_pattern = models.CharField("事件类型匹配", max_length=256, help_text="支持通配符, 如 aws.ec2.*")
    handler_class = models.CharField("Handler 类路径", max_length=256)
    timeout = models.IntegerField("超时(秒)", default=60)
    max_retries = models.IntegerField("最大重试次数", default=5)
    is_active = models.BooleanField("启用", default=True)
    description = models.TextField("描述", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "Handler 配置"
        verbose_name_plural = "Handler 配置"

    def __str__(self):
        return self.name
