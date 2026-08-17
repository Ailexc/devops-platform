from django.db import models
from django.conf import settings


STATUS_CHOICES = [
    ('active', '启用'),
    ('inactive', '停用'),
]


class BusinessLine(models.Model):
    """业务线"""
    name = models.CharField(max_length=64, verbose_name="业务线名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="业务线编码")
    description = models.TextField(blank=True, verbose_name="描述")
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="led_business_lines", verbose_name="业务线负责人"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_line"
        ordering = ["sort_order", "id"]
        verbose_name = "业务线"
        verbose_name_plural = "业务线"

    def __str__(self):
        return self.name


class Group(models.Model):
    """组织组 - 权限的基本载体"""
    name = models.CharField(max_length=64, verbose_name="组名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="组编码")
    description = models.TextField(blank=True, verbose_name="描述")
    business_line = models.ForeignKey(
        BusinessLine, on_delete=models.CASCADE, related_name="groups",
        verbose_name="所属业务线"
    )
    parent_group = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="child_groups", verbose_name="父组"
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="led_groups", verbose_name="组负责人"
    )
    role = models.ForeignKey("authz.Role", null=True, blank=True, on_delete=models.SET_NULL,
                             verbose_name="专属角色")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "`group`"  # group 是 SQL 保留字
        ordering = ["business_line", "name"]
        verbose_name = "组织组"
        verbose_name_plural = "组织组"

    def __str__(self):
        return f"{self.business_line.name} - {self.name}"