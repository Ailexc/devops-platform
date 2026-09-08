from django.db import models
from apps.accounts.models import User
from apps.organizations.models import Group


class Role(models.Model):
    """角色 - 数据权限规则的命名容器，不再承载功能权限"""
    ROLE_OWNER_TYPES = [
        ("group", "组角色"),
        ("user", "用户角色"),
    ]

    name = models.CharField(max_length=64, verbose_name="角色名称")
    owner_type = models.CharField(max_length=16, choices=ROLE_OWNER_TYPES, verbose_name="归属类型")
    is_system = models.BooleanField(default=False, verbose_name="系统内置")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role"
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return f"{self.name}({self.get_owner_type_display()})"


class SubjectMembership(models.Model):
    """用户与组的关系"""
    MEMBERSHIP_TYPES = [
        ('primary', '归属'),
        ('collaborator', '协作'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    membership_type = models.CharField(max_length=16, choices=MEMBERSHIP_TYPES, default='primary',
                                       verbose_name="成员类型")
    resource_scope = models.JSONField(null=True, blank=True, verbose_name="资源范围限制",
                                      help_text="协作成员可见的资源范围: {\"app_ids\": [1,2,3]}")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "subject_membership"
        unique_together = [("user", "group")]
        verbose_name = "成员关系"
        verbose_name_plural = "成员关系"

    def __str__(self):
        return f"{self.user.display_name} -> {self.group.name} ({self.get_membership_type_display()})"


class RoleDataRule(models.Model):
    """数据权限规则 - 以应用为原子授权单元"""
    GRANT_SCOPES = [
        ("own_group", "本组权限"),
        ("cross_group", "跨组协作"),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="data_rules")

    business_line_id = models.BigIntegerField(verbose_name="业务线 ID")
    owner_group_id = models.BigIntegerField(verbose_name="应用承接组 ID")
    app_id = models.BigIntegerField(verbose_name="应用 ID")

    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    is_all_envs = models.BooleanField(default=False, verbose_name="是否授权该类型下全部环境")

    allow_env_ids = models.JSONField(default=list, verbose_name="允许环境 ID 列表")
    deny_env_ids = models.JSONField(default=list, verbose_name="拒绝环境 ID 列表")

    grant_scope = models.CharField(max_length=16, choices=GRANT_SCOPES, default="own_group")
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role_data_rule"
        indexes = [
            models.Index(fields=["role", "app_id", "env_type"]),
            models.Index(fields=["app_id", "env_type"]),
            models.Index(fields=["grant_scope", "valid_to"]),
        ]
        verbose_name = "数据权限规则"
        verbose_name_plural = "数据权限规则"

    def __str__(self):
        return f"RoleDataRule(role={self.role_id}, app={self.app_id}, env_type={self.env_type})"


class EffectivePermissionCache(models.Model):
    """有效权限缓存 - 高频鉴权展开后的读模型"""
    EFFECTS = [
        ("allow", "允许"),
        ("deny", "拒绝"),
    ]

    user_id = models.BigIntegerField()
    app_id = models.BigIntegerField()
    env_id = models.BigIntegerField()
    effect = models.CharField(max_length=8, choices=EFFECTS)

    source_role_id = models.BigIntegerField()
    source_rule_id = models.BigIntegerField()
    valid_to = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "effective_permission_cache"
        indexes = [
            models.Index(fields=["user_id", "app_id", "env_id"]),
            models.Index(fields=["user_id", "env_id"]),
            models.Index(fields=["app_id", "env_id"]),
            models.Index(fields=["valid_to"]),
        ]
        verbose_name = "有效权限缓存"
        verbose_name_plural = "有效权限缓存"


class EnvironmentApprovalConfig(models.Model):
    """环境审批配置 - 按环境类型 + 授权范围配置审批策略"""
    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    grant_scope = models.CharField(
        max_length=16, choices=[("own_group", "本组"), ("cross_group", "跨组协作")],
        verbose_name="授权范围"
    )
    requires_approval = models.BooleanField(default=False, verbose_name="是否需要审批")

    # 关联审批流模板
    flow_template = models.ForeignKey(
        "ApprovalFlowTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="审批流模板",
        limit_choices_to={'category': 'permission'},
    )

    priority = models.IntegerField(default=0, verbose_name="优先级")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "env_approval_config"
        unique_together = [("env_type", "grant_scope")]
        verbose_name = "环境审批配置"
        verbose_name_plural = "环境审批配置"


class ReleaseApprovalConfig(models.Model):
    """发布策略 - 按环境类型配置发布审批"""
    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    requires_approval = models.BooleanField(default=False, verbose_name="是否需要审批")
    flow_template = models.ForeignKey(
        "ApprovalFlowTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="审批流模板",
        limit_choices_to={'category': 'release'},
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "release_approval_config"
        unique_together = [("env_type",)]
        verbose_name = "发布策略"
        verbose_name_plural = "发布策略"


class ApprovalFlowTemplate(models.Model):
    """审批流模板 - 可复用的审批流程定义"""
    CATEGORIES = [
        ('release', '发布审批'),
        ('permission', '权限审批'),
        ('app_change', '应用变更审批'),
    ]

    name = models.CharField(max_length=64, verbose_name="模板名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="模板编码")
    description = models.TextField(blank=True, verbose_name="描述")
    category = models.CharField(max_length=16, choices=CATEGORIES, default='release',
                                verbose_name="模板分类")
    steps = models.JSONField(default=list, verbose_name="审批步骤")
    """
    steps 结构:
    [
        {
            "order": 1,
            "name": "应用负责人审批",
            "dimension": "app_owner",
            "approver_resolver": "app_owner",
            "resolver_config": {},
            "required_count": 1,
            "timeout_hours": 24,
        },
    ]
    """
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approval_flow_template"
        verbose_name = "审批流模板"
        verbose_name_plural = "审批流模板"

    def __str__(self):
        return f"{self.name}({self.code})"


class AppChangeApprovalConfig(models.Model):
    """应用变更审批配置 - 全局统一，不区分环境"""
    requires_approval = models.BooleanField(default=False, verbose_name="是否需要审批")
    flow_template = models.ForeignKey(
        "ApprovalFlowTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="审批流模板",
        limit_choices_to={'category': 'app_change'},
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_change_approval_config"
        verbose_name = "应用变更审批配置"
        verbose_name_plural = "应用变更审批配置"


class PermissionRequest(models.Model):
    """权限申请"""
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    REQUEST_TYPES = [
        ('apply', '申请权限'),
        ('share', '分享协作应用'),
        ('revoke', '回收协作权限'),
        ('release', '解除协作应用'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="perm_requests")
    request_type = models.CharField(max_length=16, choices=REQUEST_TYPES, default='apply',
                                    verbose_name="申请类型")
    app_id = models.BigIntegerField(verbose_name="应用 ID")
    env_type = models.CharField(max_length=16, verbose_name="环境类型")
    is_all_envs = models.BooleanField(default=False, verbose_name="是否申请该类型下全部环境")
    env_ids = models.JSONField(default=list, verbose_name="申请环境 ID 列表")
    grant_scope = models.CharField(max_length=16, choices=RoleDataRule.GRANT_SCOPES, default="own_group",
                                   verbose_name="授权范围")
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name="生效时间")
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    reason = models.TextField(blank=True, verbose_name="申请原因")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    # 分享/回收/解除 等场景需要记录的扩展信息
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="扩展数据",
                                  help_text="例如 target_group_id, target_user_ids, revoke_rule_ids")
    # 受益人：权限申请审批通过后，实际获得/失去权限的用户/组
    beneficiary_user_ids = models.JSONField(default=list, blank=True, verbose_name="受益用户 ID 列表")
    beneficiary_group_ids = models.JSONField(default=list, blank=True, verbose_name="受益组 ID 列表")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permission_request"
        verbose_name = "权限申请"
        verbose_name_plural = "权限申请"

    def __str__(self):
        return f"PermissionRequest(user={self.user_id}, type={self.request_type}, app={self.app_id}, status={self.status})"