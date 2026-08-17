"""
工单业务层模型
"""
from django.db import models
from django.conf import settings
from django_fsm import FSMField, transition

from apps.common.models import TimeStampedModel


class TicketType(TimeStampedModel):
    """工单类型"""

    class Priority(models.IntegerChoices):
        LOW = 1, '低'
        MEDIUM = 2, '中'
        HIGH = 3, '高'
        URGENT = 4, '紧急'

    code = models.CharField('类型编码', max_length=100, unique=True)
    name = models.CharField('类型名称', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    priority_matrix = models.JSONField(
        '优先级矩阵',
        default=dict,
        help_text='基于条件自动计算优先级的规则',
    )
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        ordering = ['code']
        verbose_name = '工单类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Ticket(TimeStampedModel):
    """工单"""

    class Status(models.TextChoices):
        NEW = 'new', '新建'
        ASSIGNED = 'assigned', '已分配'
        IN_PROGRESS = 'in_progress', '处理中'
        RESOLVED = 'resolved', '已解决'
        CLOSED = 'closed', '已关闭'
        CANCELLED = 'cancelled', '已取消'
        REOPENED = 'reopened', '已重开'

    class Priority(models.IntegerChoices):
        LOW = 1, '低'
        MEDIUM = 2, '中'
        HIGH = 3, '高'
        URGENT = 4, '紧急'

    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='工单类型',
    )
    instance = models.OneToOneField(
        'processes.ProcessInstance',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ticket',
        verbose_name='关联流程实例',
    )
    form_data = models.JSONField('表单数据', default=dict)
    status = FSMField('状态', max_length=20, choices=Status.choices, default=Status.NEW, protected=True)
    priority = models.IntegerField('优先级', choices=Priority.choices, default=Priority.MEDIUM)
    title = models.CharField('标题', max_length=300)
    description = models.TextField('描述', blank=True, default='')
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tickets',
        verbose_name='创建人',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        verbose_name='处理人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    resolved_at = models.DateTimeField('解决时间', null=True, blank=True)
    closed_at = models.DateTimeField('关闭时间', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '工单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.get_status_display()}] {self.title}'

    # --- FSM Transitions ---
    @transition(field=status, source=Status.NEW, target=Status.ASSIGNED)
    def assign(self):
        pass

    @transition(field=status, source=[Status.ASSIGNED, Status.REOPENED], target=Status.IN_PROGRESS)
    def start_progress(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS, target=Status.RESOLVED)
    def resolve(self):
        pass

    @transition(field=status, source=Status.RESOLVED, target=Status.CLOSED)
    def close(self):
        pass

    @transition(field=status, source='*', target=Status.CANCELLED)
    def cancel(self):
        pass

    @transition(field=status, source=Status.RESOLVED, target=Status.REOPENED)
    def reopen(self):
        pass


class Comment(TimeStampedModel):
    """工单评论"""

    class Visibility(models.TextChoices):
        INTERNAL = 'internal', '内部可见'
        EXTERNAL = 'external', '外部可见'

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='工单',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_comments',
        verbose_name='评论人',
    )
    content = models.TextField('内容')
    visibility = models.CharField(
        '可见性',
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.INTERNAL,
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = '评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Comment by {self.user} on {self.ticket}'


class Notification(TimeStampedModel):
    """通知"""

    class Type(models.TextChoices):
        SYSTEM = 'system', '系统通知'
        TASK = 'task', '任务通知'
        TICKET = 'ticket', '工单通知'
        APPROVAL = 'approval', '审批通知'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人',
    )
    type = models.CharField('类型', max_length=20, choices=Type.choices)
    title = models.CharField('标题', max_length=300)
    content = models.TextField('内容')
    is_read = models.BooleanField('已读', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.get_type_display()}] {self.title}'
