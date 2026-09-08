"""
能力注册中心模型
"""
import uuid

from django.db import models
from django.conf import settings

from apps.common.models import TimeStampedModel


class Capability(TimeStampedModel):
    """能力定义：代表一个可被流程引擎调用的外部能力"""

    class ExecuteMode(models.TextChoices):
        SYNC = 'sync', '同步'
        ASYNC = 'async', '异步'

    code = models.CharField('能力编码', max_length=100, unique=True, help_text='如 cmdb_create_host, mail_send')
    name = models.CharField('能力名称', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    input_schema = models.JSONField('输入 Schema', default=dict, help_text='输入参数的 JSON Schema')
    output_schema = models.JSONField('输出 Schema', default=dict, help_text='输出参数的 JSON Schema')
    execute_mode = models.CharField(
        '执行模式',
        max_length=10,
        choices=ExecuteMode.choices,
        default=ExecuteMode.SYNC,
    )
    endpoint = models.CharField('端点 URL', max_length=500, blank=True, default='')
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        ordering = ['code']
        verbose_name = '能力'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name} ({self.code})'


class TaskJob(TimeStampedModel):
    """任务执行记录"""

    class Status(models.TextChoices):
        QUEUED = 'queued', '排队中'
        RUNNING = 'running', '执行中'
        SUCCEEDED = 'succeeded', '成功'
        FAILED = 'failed', '失败'

    instance = models.ForeignKey(
        'processes.ProcessInstance',
        on_delete=models.CASCADE,
        related_name='task_jobs',
        verbose_name='流程实例',
    )
    task = models.ForeignKey(
        'processes.NodeTask',
        on_delete=models.CASCADE,
        related_name='task_jobs',
        verbose_name='节点任务',
    )
    capability = models.ForeignKey(
        Capability,
        on_delete=models.CASCADE,
        related_name='jobs',
        verbose_name='能力',
    )
    job_id = models.CharField('Job ID', max_length=64, unique=True, default=uuid.uuid4)
    status = models.CharField('状态', max_length=20, choices=Status.choices, default=Status.QUEUED)
    node_key = models.CharField('节点 Key', max_length=100, blank=True, default='')
    action_key = models.CharField('动作 Key', max_length=100, blank=True, default='')
    action_name = models.CharField('动作名称', max_length=200, blank=True, default='')
    input_data = models.JSONField('输入数据', default=dict)
    output_data = models.JSONField('输出数据', default=dict)
    logs = models.JSONField('执行日志', default=list, blank=True, help_text='时间线日志：[{ts, level, message}]')
    sync = models.BooleanField('同步执行', default=False)
    error_message = models.TextField('错误信息', blank=True, default='')
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '任务执行'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Job {self.job_id} ({self.get_status_display()})'
