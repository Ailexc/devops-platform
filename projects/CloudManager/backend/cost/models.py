from django.db import models


class CostBill(models.Model):
    """模拟月度账单"""
    account = models.ForeignKey('cmdb.CloudAccount', on_delete=models.CASCADE,
                                related_name='bills', verbose_name='云账号')
    bill_month = models.CharField('账单月份', max_length=7, help_text='2026-08')
    total_cost = models.DecimalField('总费用', max_digits=12, decimal_places=2, default=0)
    currency = models.CharField('币种', max_length=8, default='CNY')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cost_bill'
        verbose_name = '账单'
        verbose_name_plural = verbose_name
        unique_together = ('account', 'bill_month')
        ordering = ['-bill_month']

    def __str__(self):
        return f'{self.account.account_name} - {self.bill_month}: ¥{self.total_cost}'


class CostItem(models.Model):
    """费用明细"""
    bill = models.ForeignKey(CostBill, on_delete=models.CASCADE,
                             related_name='items', verbose_name='账单')
    resource = models.ForeignKey('cmdb.Resource', on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name='关联资源')
    service_type = models.CharField('服务类型', max_length=32)
    cost = models.DecimalField('费用', max_digits=10, decimal_places=2, default=0)
    cost_date = models.DateField('费用日期')
    # 账单分摊标签（独立于资源归属，来自云账单 Cost Allocation Tag）
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='分摊部门')
    application = models.ForeignKey('cmdb.Application', on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='分摊应用')

    class Meta:
        db_table = 'cost_item'
        verbose_name = '费用明细'
        verbose_name_plural = verbose_name


class Budget(models.Model):
    """部门预算"""
    department = models.ForeignKey('accounts.Department', on_delete=models.CASCADE,
                                   related_name='budgets', verbose_name='部门')
    month = models.CharField('预算月份', max_length=7)
    budget_amount = models.DecimalField('预算金额', max_digits=12, decimal_places=2)
    used_amount = models.DecimalField('已用金额', max_digits=12, decimal_places=2, default=0)
    alert_threshold = models.IntegerField('告警阈值(%)', default=80)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cost_budget'
        verbose_name = '预算'
        verbose_name_plural = verbose_name
        unique_together = ('department', 'month')

    @property
    def usage_percent(self):
        if self.budget_amount == 0:
            return 0
        return round(float(self.used_amount) / float(self.budget_amount) * 100, 1)

    @property
    def is_over_threshold(self):
        return self.usage_percent >= self.alert_threshold

    def __str__(self):
        return f'{self.department.name} - {self.month}: ¥{self.used_amount}/¥{self.budget_amount}'


class OptimizationRule(models.Model):
    """可配置优化规则 —— 由运维在页面配置，平台只提供引擎能力"""
    RULE_TYPE_CHOICES = [
        ('idle', '闲置资源'),
        ('downsize', '建议降配'),
        ('unused', '未使用资源'),
        ('budget', '预算告警'),
        ('trend', '费用趋势异常'),
        ('reserved', '付费模式优化'),
        ('storage', '存储优化'),
    ]
    SEVERITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]

    name = models.CharField('规则名称', max_length=128)
    rule_type = models.CharField('规则类型', max_length=16, choices=RULE_TYPE_CHOICES)
    severity = models.CharField('优先级', max_length=8, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField('规则说明', blank=True, default='')
    # 检测范围：{cloud, account, region, resource_type} —— 关联 CloudAccount/Resource 维度
    scope = models.JSONField('检测范围', default=dict, blank=True)
    # 检测条件：声明式 JSON，如 {"status":"stopped","min_days":7} / {"metrics":{"avg_cpu_7d":{"lt":5}}}
    conditions = models.JSONField('检测条件', default=dict, blank=True)
    title_template = models.CharField('建议标题模板', max_length=128, default='{resource_name} 建议处理')
    description_template = models.TextField('描述模板', blank=True, default='')
    # 节省估算配置：{"type":"spec_ratio","percent":40} / {"type":"fixed","amount":50} / {"type":"none"}
    saving_config = models.JSONField('节省估算配置', default=dict, blank=True)
    is_enabled = models.BooleanField('启用', default=True)
    priority = models.IntegerField('执行优先级', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cost_optimization_rule'
        verbose_name = '优化规则'
        verbose_name_plural = verbose_name
        ordering = ['-priority', 'id']

    def __str__(self):
        return f'{self.name} ({self.get_rule_type_display()})'


class RuleExecutionLog(models.Model):
    """规则执行日志 —— 每次执行留痕，规则改了也能追溯"""
    rule = models.ForeignKey(OptimizationRule, on_delete=models.CASCADE,
                             related_name='executions', verbose_name='规则')
    scope_snapshot = models.JSONField('执行时范围快照', default=dict, blank=True)
    matched_count = models.IntegerField('匹配资源数', default=0)
    created_count = models.IntegerField('生成建议数', default=0)
    execution_time_ms = models.IntegerField('执行耗时(ms)', default=0)
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)

    class Meta:
        db_table = 'cost_rule_execution_log'
        verbose_name = '规则执行日志'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']

    def __str__(self):
        return f'{self.rule.name} @ {self.executed_at:%Y-%m-%d %H:%M}'


class OptimizationReport(models.Model):
    """分析报告 —— 一次检测的完整结果快照（汇总 + 层级树 + 明细）"""
    TRIGGER_CHOICES = [
        ('manual', '手动全量'),
        ('single', '单规则'),
        ('schedule', '定时'),
    ]

    report_no = models.CharField('报告单号', max_length=32, blank=True, default='')
    title = models.CharField('报告标题', max_length=128)
    operator = models.CharField('执行人', max_length=64, default='system')
    trigger = models.CharField('触发方式', max_length=16, choices=TRIGGER_CHOICES, default='manual')
    # summary: {total_rules, total_matched, total_saving, cloud_count}
    summary = models.JSONField('汇总统计', default=dict, blank=True)
    # tree_snapshot: 云→账号→区域→类型 层级聚合（V5 报告树）
    tree_snapshot = models.JSONField('层级树快照', default=dict, blank=True)
    # items_snapshot: 每条建议完整数据（冗余，导出用）
    items_snapshot = models.JSONField('明细快照', default=list, blank=True)
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)

    class Meta:
        db_table = 'cost_optimization_report'
        verbose_name = '分析报告'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']

    def __str__(self):
        return self.title


class OptimizationSuggestion(models.Model):
    """智能资源优化建议 —— 归属某次报告 + 冗余维度字段（按维度快速聚合）"""
    TYPE_CHOICES = [
        ('idle', '闲置资源'),
        ('downsize', '建议降配'),
        ('unused', '未挂载资源'),
        ('budget', '预算告警'),
        ('trend', '费用趋势异常'),
        ('reserved', '付费模式优化'),
        ('storage', '存储优化'),
    ]
    SEVERITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]

    report = models.ForeignKey(OptimizationReport, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='suggestions',
                               verbose_name='所属报告')
    rule = models.ForeignKey(OptimizationRule, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='suggestions',
                             verbose_name='命中规则')
    resource = models.ForeignKey('cmdb.Resource', on_delete=models.CASCADE,
                                 related_name='suggestions', verbose_name='关联资源',
                                 null=True, blank=True,
                                 help_text='维度级建议（预算/趋势）可为空')
    # ★ 冗余维度（避免每次 join 聚合）
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='所属部门')
    account = models.ForeignKey('cmdb.CloudAccount', on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='云账号')
    provider_type = models.CharField('云类型', max_length=16, blank=True, default='')
    region = models.CharField('区域', max_length=32, blank=True, default='')
    resource_type = models.CharField('资源类型', max_length=32, blank=True, default='')
    suggestion_type = models.CharField('建议类型', max_length=16, choices=TYPE_CHOICES)
    severity = models.CharField('优先级', max_length=8, choices=SEVERITY_CHOICES, default='medium')
    title = models.CharField('建议标题', max_length=128)
    description = models.TextField('详细描述')
    estimated_saving = models.DecimalField('预估月节省(元)', max_digits=10, decimal_places=2, default=0)
    is_resolved = models.BooleanField('已处理', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'cost_optimization_suggestion'
        verbose_name = '优化建议'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_suggestion_type_display()}] {self.title}'
