"""
事件总线模型
"""
import uuid

from django.db import models

from apps.common.models import TimeStampedModel


class EventLog(TimeStampedModel):
    """事件日志"""
    instance = models.ForeignKey(
        'processes.ProcessInstance',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='events',
        verbose_name='流程实例',
    )
    task = models.ForeignKey(
        'processes.NodeTask',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='events',
        verbose_name='节点任务',
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='events',
        verbose_name='工单',
    )
    type = models.CharField('事件类型', max_length=100, help_text='如 process.started, task.completed')
    payload = models.JSONField('事件数据', default=dict)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '事件日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.type} @ {self.created_at}'


class WebhookSubscription(TimeStampedModel):
    """Webhook 订阅"""

    class Direction(models.TextChoices):
        RECEIVE = 'receive', '接收订阅'
        PUSH = 'push', '推送上报'

    url = models.URLField('回调 URL', max_length=500)
    name = models.CharField('订阅名称', max_length=200)
    events = models.JSONField('订阅的事件类型', default=list, help_text='事件类型列表')
    secret = models.CharField('签名密钥', max_length=200, blank=True, default='')
    direction = models.CharField('方向', max_length=20, choices=Direction.choices, default='push')
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook 订阅'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name} -> {self.url}'


class WebhookDelivery(TimeStampedModel):
    """Webhook 投递记录"""

    class Status(models.TextChoices):
        PENDING = 'pending', '待投递'
        DELIVERED = 'delivered', '已投递'
        FAILED = 'failed', '投递失败'

    subscription = models.ForeignKey(
        WebhookSubscription,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='订阅',
    )
    event = models.ForeignKey(
        EventLog,
        on_delete=models.CASCADE,
        related_name='webhook_deliveries',
        verbose_name='事件',
    )
    attempt = models.IntegerField('尝试次数', default=0)
    status = models.CharField('状态', max_length=20, choices=Status.choices, default=Status.PENDING)
    last_response = models.TextField('最近一次响应', blank=True, default='')
    last_attempt_at = models.DateTimeField('最近尝试时间', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook 投递'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Delivery {self.id} ({self.get_status_display()})'
