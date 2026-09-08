from django.db import models
from apps.accounts.models import User
from apps.releases.models import Release
from apps.authz.models import PermissionRequest


class Approval(models.Model):
    """审批记录 - 支持多步骤审批流"""
    ACTIONS = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]

    APPROVAL_TYPES = [
        ('release', '发布审批'),
        ('permission', '权限申请'),
        ('scale', '实例伸缩'),
        ('ops', '运维操作'),
    ]

    approval_type = models.CharField(max_length=16, choices=APPROVAL_TYPES, default='release')
    release = models.ForeignKey(Release, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="approvals")
    permission_request = models.ForeignKey(PermissionRequest, on_delete=models.CASCADE, null=True, blank=True,
                                           related_name="approvals")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approvals",
                                 verbose_name="审批人")
    action = models.CharField(max_length=16, choices=ACTIONS, default='pending')
    comment = models.TextField(blank=True, verbose_name="审批意见")

    # 扩展数据（JSON）
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="扩展数据",
                                  help_text="存储非发布审批的额外信息，如实例伸缩参数")

    # 多步骤审批流支持
    step_order = models.IntegerField(default=1, verbose_name="审批步骤序号")
    step_name = models.CharField(max_length=64, blank=True, verbose_name="审批步骤名称")
    total_steps = models.IntegerField(default=1, verbose_name="总审批步骤数")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approval"
        ordering = ["-created_at"]
        verbose_name = "审批记录"
        verbose_name_plural = "审批记录"

    def __str__(self):
        return f"{self.get_approval_type_display()}-步骤{self.step_order}-{self.approver.display_name}"