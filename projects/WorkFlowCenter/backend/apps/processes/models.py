"""
流程引擎数据模型
"""
from django.db import models
from django.conf import settings
from django_fsm import FSMField, transition

from apps.common.models import TimeStampedModel


class InitiatorApp(TimeStampedModel):
    """发起程序（外部接入方），用于程序发起流程时的身份认证"""

    name = models.CharField('程序名称', max_length=100)
    code = models.CharField('程序标识', max_length=100, unique=True, help_text='调用接口时使用的程序编码')
    api_key_hash = models.CharField('API Key 摘要', max_length=128, blank=True, default='')
    is_active = models.BooleanField('启用', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_initiator_apps',
        verbose_name='创建人',
    )

    class Meta:
        ordering = ['id']
        verbose_name = '发起程序'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ApiCallLog(TimeStampedModel):
    """开放 API 调用日志（程序发起等外部调用）"""

    app = models.ForeignKey(
        InitiatorApp,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='api_calls',
        verbose_name='接入方',
    )
    app_code = models.CharField('程序标识', max_length=100, blank=True, default='')
    method = models.CharField('请求方法', max_length=10, default='POST')
    path = models.CharField('请求路径', max_length=255, default='')
    status_code = models.IntegerField('响应状态码', default=200)
    duration_ms = models.IntegerField('耗时(ms)', default=0)
    instance_no = models.CharField('流程单号', max_length=64, blank=True, default='')
    success = models.BooleanField('是否成功', default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '开放 API 调用日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.app_code} {self.method} {self.path} {self.status_code}'


class ProcessDefinition(TimeStampedModel):
    """流程定义"""

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PUBLISHED = 'published', '已发布'
        DISABLED = 'disabled', '已停用'

    class Category(models.TextChoices):
        GENERAL = 'general', '通用'
        HR = 'hr', '人事'
        FINANCE = 'finance', '财务'
        ADMIN = 'admin', '行政'
        IT = 'it', 'IT'

    class SubmitScope(models.TextChoices):
        ALL = 'all', '全员'
        SPECIFIC_DEPT = 'specific_dept', '指定部门'
        SPECIFIC_ROLE = 'specific_role', '指定角色'
        NONE = 'none', '不允许提交'

    class TimeoutAction(models.TextChoices):
        REMIND = 'remind', '提醒审批人'
        AUTO_APPROVE = 'auto_approve', '自动通过'
        AUTO_REJECT = 'auto_reject', '自动拒绝'

    class LaunchStatus(models.TextChoices):
        OFFLINE = 'offline', '未上线'
        DEBUG = 'debug', '调试上线'
        PRODUCTION = 'production', '正式上线'

    key = models.CharField('流程标识', max_length=100, unique=True)
    name = models.CharField('流程名称', max_length=200)
    version = models.PositiveIntegerField('版本号', default=1)
    status = models.CharField('状态', max_length=20, choices=Status.choices, default=Status.DRAFT)
    definition_json = models.JSONField('流程定义（JSON）', default=dict, help_text='节点与连线的完整定义')
    form_schema = models.JSONField('表单 Schema', default=dict, help_text='动态表单的 JSON Schema')

    # --- 基本信息扩展 ---
    category = models.CharField('流程分类', max_length=20, choices=Category.choices, default=Category.GENERAL)
    icon = models.CharField('流程图标', max_length=50, default='document')
    submit_scope = models.CharField('提交范围', max_length=20, choices=SubmitScope.choices, default=SubmitScope.ALL)
    submit_scope_ids = models.JSONField('提交范围（部门/角色 ID 列表）', default=list, blank=True)
    admin_ids = models.JSONField('流程管理员', default=list, blank=True)
    group_id = models.CharField('流程分组', max_length=50, null=True, blank=True)
    allow_withdraw = models.BooleanField('允许撤回', default=True)
    allow_transfer = models.BooleanField('允许转交', default=True)
    timeout_hours = models.IntegerField('超时时间（小时）', null=True, blank=True, default=72)
    timeout_action = models.CharField('超时动作', max_length=20, choices=TimeoutAction.choices, default=TimeoutAction.REMIND)
    # --- 发起方式与上线属性 ---
    allow_program_initiate = models.BooleanField('允许程序发起', default=False)
    initiator_app_ids = models.JSONField('可发起程序（ID 列表）', default=list, blank=True)
    launch_status = models.CharField(
        '上线状态',
        max_length=20,
        choices=LaunchStatus.choices,
        default=LaunchStatus.OFFLINE,
        help_text='未上线 / 调试上线 / 正式上线',
    )
    allow_self_approve = models.BooleanField('允许发起人自己审批', default=True)
    # --- 业务规则（方案 B · 结构化 AST） ---
    rules_json = models.JSONField(
        '业务规则（JSON）', default=list, blank=True,
        help_text='提单预检业务规则：[{id,name,level,message,suggestion,groups:[[{source,op,refType,fixed,refField,offset}]]}]',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_definitions',
        verbose_name='创建人',
    )

    class Meta:
        ordering = ['-version']
        verbose_name = '流程定义'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name} v{self.version}'


class ProcessInstance(TimeStampedModel):
    """流程实例（运行时）"""

    class Status(models.TextChoices):
        RUNNING = 'running', '运行中'
        SUSPENDED = 'suspended', '已挂起'
        COMPLETED = 'completed', '已完成'
        TERMINATED = 'terminated', '已终止'

    definition = models.ForeignKey(
        ProcessDefinition,
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name='流程定义',
    )
    instance_no = models.CharField('实例编号', max_length=50, unique=True)
    status = FSMField('状态', max_length=20, choices=Status.choices, default=Status.RUNNING, protected=True)
    current_node_key = models.CharField('当前节点 Key', max_length=100, blank=True, default='')
    variables = models.JSONField('流程变量', default=dict)
    # unique + null：无业务键的普通发起存 NULL（Postgres 允许多个 NULL），避免第二个空键实例冲突
    business_key = models.CharField('业务主键', max_length=200, unique=True, null=True, blank=True, default='')
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='started_instances',
        verbose_name='发起人',
    )
    started_at = models.DateTimeField('开始时间', auto_now_add=True)
    ended_at = models.DateTimeField('结束时间', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = '流程实例'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.instance_no} ({self.get_status_display()})'

    # --- FSM Transitions ---
    @transition(field=status, source=Status.RUNNING, target=Status.SUSPENDED)
    def suspend(self):
        pass

    @transition(field=status, source=Status.SUSPENDED, target=Status.RUNNING)
    def resume(self):
        pass

    @transition(field=status, source=Status.RUNNING, target=Status.COMPLETED)
    def complete(self):
        pass

    @transition(field=status, source='*', target=Status.TERMINATED)
    def terminate(self):
        pass


class NodeTask(TimeStampedModel):
    """节点任务（流程节点产生的待办）"""

    class NodeType(models.TextChoices):
        START = 'start', '开始'
        APPROVE = 'approve', '审批'
        HANDLE = 'handle', '办理'
        SERVICE = 'service', '服务调用'
        CC = 'cc', '抄送'
        CONDITION = 'condition', '条件判断'
        END = 'end', '结束'

    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        CLAIMED = 'claimed', '已签收'
        RUNNING = 'running', '执行中'
        ABNORMAL = 'abnormal', '异常'
        COMPLETED = 'completed', '已完成'
        CANCELLED = 'cancelled', '已取消'
        SKIPPED = 'skipped', '已跳过'

    class ApprovalType(models.TextChoices):
        SINGLE = 'single', '单人审批'
        COUNTERSIGN = 'countersign', '会签（全部通过）'
        OR_SIGN = 'or_sign', '或签（一人通过）'

    instance = models.ForeignKey(
        ProcessInstance,
        on_delete=models.CASCADE,
        related_name='node_tasks',
        verbose_name='流程实例',
    )
    node_key = models.CharField('节点 Key', max_length=100)
    node_name = models.CharField('节点名称', max_length=200, blank=True, default='')
    node_type = models.CharField('节点类型', max_length=20, choices=NodeType.choices)
    approval_type = models.CharField('审批类型', max_length=20, choices=ApprovalType.choices, default=ApprovalType.SINGLE)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        verbose_name='处理人',
    )
    candidate_users = models.JSONField('候选处理人', default=list, help_text='用户 ID 列表')
    status = models.CharField('状态', max_length=20, choices=Status.choices, default=Status.PENDING)
    result = models.CharField('处理结果', max_length=50, blank=True, default='')
    opinion = models.TextField('审批意见', blank=True, default='')
    due_at = models.DateTimeField('截止时间', null=True, blank=True)
    countersign = models.JSONField('会签信息', default=dict, help_text='记录各候选人的审批状态')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '节点任务'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.node_name} ({self.get_status_display()})'


class TaskInstance(TimeStampedModel):
    """任务实例（审批动作的具体记录）"""
    task = models.ForeignKey(
        NodeTask,
        on_delete=models.CASCADE,
        related_name='task_instances',
        verbose_name='节点任务',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_instances',
        verbose_name='处理人',
    )
    status = models.CharField('状态', max_length=20, choices=NodeTask.Status.choices, default=NodeTask.Status.PENDING)
    result = models.CharField('处理结果', max_length=50, blank=True, default='')
    opinion = models.TextField('审批意见', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '任务实例'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'TaskInstance({self.task.node_key} -> {self.assignee})'


class ApprovalRecord(TimeStampedModel):
    """审批记录"""
    ACTION_CHOICES = [
        ('approve', '通过'),
        ('reject', '驳回'),
        ('delegate', '转办'),
        ('cc', '抄送'),
        ('comment', '评论'),
    ]

    # 发起来源：人员发起为空；程序发起记录程序标识（如 'cmdb_sync'）
    initiator_source = models.CharField('发起来源', max_length=100, blank=True, default='')
    instance = models.ForeignKey(
        ProcessInstance,
        on_delete=models.CASCADE,
        related_name='approval_records',
        verbose_name='流程实例',
    )
    task = models.ForeignKey(
        NodeTask,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approval_records',
        verbose_name='节点任务',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_records',
        verbose_name='操作人',
    )
    action = models.CharField('操作', max_length=20, choices=ACTION_CHOICES)
    opinion = models.TextField('意见', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '审批记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user} {self.get_action_display()} on {self.instance.instance_no}'


class TestScenarioRun(TimeStampedModel):
    """测试场景运行记录（流程测试模块）"""

    class Mode(models.TextChoices):
        COMPLETED = 'completed', '正常完成'
        RUNNING = 'running', '流程进行中'
        ABNORMAL = 'abnormal', '流程异常'
        REJECTED = 'rejected', '审批驳回'

    definition = models.ForeignKey(
        ProcessDefinition,
        on_delete=models.CASCADE,
        related_name='scenario_runs',
        verbose_name='流程定义',
    )
    instance = models.ForeignKey(
        ProcessInstance,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='scenario_runs',
        verbose_name='流程实例',
    )
    scenario_key = models.CharField('场景 Key', max_length=100)
    scenario_name = models.CharField('场景名称', max_length=200)
    scenario_mode = models.CharField('场景模式', max_length=20, choices=Mode.choices, default=Mode.COMPLETED)
    ok = models.BooleanField('是否通过', default=False)
    summary = models.JSONField('结果摘要', default=dict, blank=True)
    duration_ms = models.IntegerField('耗时（毫秒）', default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '测试场景运行'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.definition.key} · {self.scenario_name} ({self.get_scenario_mode_display()})'
