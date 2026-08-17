"""
发布审批策略 —— 按环境定义审批规则

真实 Spug 中，不同环境有不同的审批要求：
- dev/test: 通常无需审批或快速审批
- staging: 需要 TL 审批
- prod: 需要 TL + 业务线负责人审批

Demo 中仅模拟 dev/test。
"""
from django.db import models
from apps.accounts.models import User
from apps.infrastructures.models import Environment


class ReleaseApprovalStrategy(models.Model):
    """发布审批策略 —— 每个环境一条"""

    APPROVAL_MODES = [
        ('none', '无需审批'),
        ('single', '单人审批'),
        ('multi', '多级审批'),
    ]

    APPROVER_SOURCES = [
        ('app_owner', '应用负责人'),
        ('group_leader', '组负责人'),
        ('bl_leader', '业务线负责人'),
    ]

    environment = models.OneToOneField(
        Environment, on_delete=models.CASCADE,
        related_name="release_approval_strategy",
        verbose_name="环境",
    )
    mode = models.CharField(
        max_length=16, choices=APPROVAL_MODES, default='none',
        verbose_name="审批模式",
    )
    # 审批人来源：动态解析，不再绑定固定用户
    approver_source = models.CharField(
        max_length=16, choices=APPROVER_SOURCES, default='app_owner',
        verbose_name="审批人来源",
        help_text="app_owner=应用负责人, group_leader=组负责人, bl_leader=业务线负责人",
    )
    # multi 模式：每步的审批人来源（JSON 数组）
    step_sources = models.JSONField(
        default=list, blank=True,
        verbose_name="审批步骤",
        help_text='如 [{"name":"TL 审批","source":"group_leader"},...]',
    )
    description = models.TextField(blank=True, verbose_name="说明")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "release_approval_strategy"
        verbose_name = "发布审批策略"
        verbose_name_plural = "发布审批策略"

    def __str__(self):
        return f"{self.environment.name} - {self.get_mode_display()}"
