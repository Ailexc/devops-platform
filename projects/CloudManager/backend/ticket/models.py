from django.db import models


class TicketOrder(models.Model):
    """工单"""
    TYPE_CHOICES = [
        ('create_instance', '创建主机'),
        ('start', '启动'),
        ('stop', '停止'),
        ('resize', '变更规格'),
        ('release', '下线'),
        ('apply_quota', '申请配额'),
        ('scenario', '场景工单'),
        ('relation_change', '关系变更'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approving', '审批中'),
        ('executing', '待执行'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('rejected', '已驳回'),
        ('cancelled', '已取消'),
    ]

    ticket_no = models.CharField('工单号', max_length=32, unique=True)
    ticket_type = models.CharField('工单类型', max_length=32, choices=TYPE_CHOICES)
    title = models.CharField('工单标题', max_length=128)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='pending')
    applicant = models.CharField('申请人', max_length=64)
    applicant_id = models.IntegerField('申请人ID', default=0)
    approver = models.CharField('审批人', max_length=64, blank=True, default='')
    resource_id = models.CharField('目标资源ID', max_length=64, blank=True, default='')
    resource_name = models.CharField('目标资源名', max_length=128, blank=True, default='')
    provider_type = models.CharField('云类型', max_length=16, blank=True, default='')
    scenario_id = models.IntegerField('场景ID', default=0)
    scenario_code = models.CharField('场景编码', max_length=32, blank=True, default='')
    request_content = models.JSONField('申请内容', default=dict, blank=True)
    result_content = models.JSONField('执行结果', default=dict, blank=True)
    fail_reason = models.CharField('失败原因', max_length=255, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    finished_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'ticket_order'
        verbose_name = '工单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticket_no} - {self.title}'


class TicketApproval(models.Model):
    """审批记录"""
    ACTION_CHOICES = [
        (1, '同意'),
        (2, '驳回'),
    ]

    ticket = models.ForeignKey(TicketOrder, on_delete=models.CASCADE,
                               related_name='approvals', verbose_name='工单')
    approver = models.CharField('审批人', max_length=64)
    approver_id = models.IntegerField('审批人ID', default=0)
    action = models.SmallIntegerField('审批动作', choices=ACTION_CHOICES)
    comment = models.CharField('审批意见', max_length=255, blank=True, default='')
    approved_at = models.DateTimeField('审批时间', auto_now_add=True)

    class Meta:
        db_table = 'ticket_approval'
        verbose_name = '审批记录'
        verbose_name_plural = verbose_name
        ordering = ['-approved_at']


class TicketTask(models.Model):
    """自动化任务"""
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    ticket = models.ForeignKey(TicketOrder, on_delete=models.CASCADE,
                               related_name='tasks', verbose_name='工单')
    task_type = models.CharField('任务类型', max_length=32)
    provider_type = models.CharField('目标云', max_length=16)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField('已重试次数', default=0)
    max_retry = models.IntegerField('最大重试次数', default=3)
    request_id = models.CharField('幂等请求ID', max_length=64, unique=True)
    exec_log = models.TextField('执行日志', blank=True, default='')
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    finished_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'ticket_task'
        verbose_name = '自动化任务'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.ticket.ticket_no} - {self.task_type}'
