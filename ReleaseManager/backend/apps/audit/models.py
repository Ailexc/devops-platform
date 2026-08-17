from django.db import models
from apps.accounts.models import User


class AuditLog(models.Model):
    """操作审计日志"""
    ACTIONS = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('deploy', '部署'),
        ('rollback', '回滚'),
        ('approve', '审批通过'),
        ('reject', '审批驳回'),
        ('login', '登录'),
        ('grant_permission', '授权'),
        ('revoke_permission', '撤权'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    action = models.CharField(max_length=32, choices=ACTIONS, verbose_name="操作")
    resource_type = models.CharField(max_length=32, verbose_name="资源类型",
                                     help_text="application / release / permission / ...")
    resource_id = models.IntegerField(verbose_name="资源 ID")
    detail = models.JSONField(default=dict, verbose_name="操作详情")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.resource_type}"