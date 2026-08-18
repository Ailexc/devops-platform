from django.db import models


class ServiceCategory(models.Model):
    """服务分类"""
    name = models.CharField('分类名称', max_length=64)
    icon = models.CharField('图标', max_length=32, blank=True, default='📦')
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'catalog_category'
        verbose_name = '服务分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class ServiceItem(models.Model):
    """服务目录项"""
    STATUS_CHOICES = [
        ('active', '可用'),
        ('inactive', '停用'),
    ]

    name = models.CharField('服务名称', max_length=64)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE,
                                 related_name='items', verbose_name='所属分类')
    description = models.TextField('描述', blank=True, default='')
    icon = models.CharField('图标', max_length=32, blank=True, default='🖥️')
    # 申请模板：定义可选规格、地域等
    spec_options = models.JSONField('可选规格', default=list, blank=True,
                                    help_text='[{label, value, cpu, memory, price}]')
    region_options = models.JSONField('可选地域', default=list, blank=True)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'catalog_service_item'
        verbose_name = '服务目录项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Quota(models.Model):
    """部门配额"""
    department = models.ForeignKey('accounts.Department', on_delete=models.CASCADE,
                                   related_name='quotas', verbose_name='部门')
    service_item = models.ForeignKey(ServiceItem, on_delete=models.CASCADE,
                                     related_name='quotas', verbose_name='服务项')
    quota_limit = models.IntegerField('配额上限', default=10)
    used = models.IntegerField('已使用', default=0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'catalog_quota'
        verbose_name = '配额'
        verbose_name_plural = verbose_name
        unique_together = ('department', 'service_item')

    @property
    def available(self):
        return self.quota_limit - self.used

    def __str__(self):
        return f'{self.department.name} - {self.service_item.name}: {self.used}/{self.quota_limit}'
