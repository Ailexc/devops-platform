from django.db import models


class Scenario(models.Model):
    """场景定义：一组原子操作的组合模板"""
    code = models.CharField('场景编码', max_length=32, unique=True)
    name = models.CharField('场景名称', max_length=64)
    description = models.TextField('场景说明', blank=True, default='')
    icon = models.CharField('图标', max_length=32, blank=True, default='🧩')
    need_approval = models.BooleanField('是否需要审批', default=True)
    enabled = models.BooleanField('是否启用', default=True)
    version = models.CharField('版本', max_length=16, default='v1')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'scenario_definition'
        verbose_name = '场景定义'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return f'{self.name} ({self.code})'


class ScenarioStep(models.Model):
    """场景步骤：引用原子操作，支持顺序/并行依赖与回滚"""
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE,
                                 related_name='steps', verbose_name='所属场景')
    step_no = models.IntegerField('步骤序号')
    name = models.CharField('步骤名称', max_length=64)
    action_type = models.CharField('原子操作类型', max_length=32)
    action_params_template = models.JSONField('参数模板', default=dict, blank=True)
    depends_on = models.JSONField('依赖步骤', default=list, blank=True,
                                  help_text='依赖的 step_no 列表，支持并行')
    need_approval = models.BooleanField('是否需要审批', default=False)
    retry_max = models.IntegerField('最大重试次数', default=3)
    rollback_action_type = models.CharField('回滚操作类型', max_length=32, blank=True, default='')
    skip_if_missing = models.JSONField('缺参跳过', default=list, blank=True,
                                       help_text='缺少这些参数时步骤自动跳过（如无实例上下文时跳过绑定）')
    enabled = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'scenario_step'
        verbose_name = '场景步骤'
        verbose_name_plural = verbose_name
        ordering = ['scenario', 'step_no']
        unique_together = ('scenario', 'step_no')

    def __str__(self):
        return f'{self.scenario.name} #{self.step_no} {self.name}'
