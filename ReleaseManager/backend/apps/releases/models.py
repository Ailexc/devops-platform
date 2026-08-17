from django.db import models
from apps.accounts.models import User
from apps.applications.models import Application, AppEnvConfig, STRATEGIES, DEPLOY_MODES
from apps.infrastructures.models import Environment


class Release(models.Model):
    """发布单"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '审批中'),
        ('approved', '审批通过'),
        ('rejected', '审批驳回'),
        ('running', '发布中'),
        ('paused', '已暂停'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('rolled_back', '已回滚'),
        ('cancelled', '已取消'),
    ]

    # 审批状态：区分"发布单状态"和"审批状态"
    # 发布单状态描述整个生命周期，审批状态只描述审批环节
    APPROVAL_STATUS_CHOICES = [
        ('not_submitted', '未发起'),      # 创建后未发起审批
        ('submitting', '审批中'),          # 已发起，等待审批
        ('passed', '审批通过'),            # 审批通过
        ('rejected', '审批驳回'),          # 审批驳回
        ('not_needed', '无需审批'),        # 不需要审批（可直接发布）
    ]

    release_no = models.CharField(max_length=32, unique=True, verbose_name="发布单号",
                                  help_text="格式: REL-YYYYMMDD-xxxx")
    title = models.CharField(max_length=128, verbose_name="发布标题")
    description = models.TextField(blank=True, verbose_name="发布描述")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="releases")
    env_config = models.ForeignKey(AppEnvConfig, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    version = models.CharField(max_length=32, verbose_name="版本号")
    commit_id = models.CharField(max_length=64, blank=True, verbose_name="Commit ID")
    commit_message = models.TextField(blank=True, verbose_name="Commit 信息")
    branch = models.CharField(max_length=128, blank=True, verbose_name="分支")
    image_tag = models.CharField(max_length=128, verbose_name="镜像 Tag")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    approval_status = models.CharField(max_length=16, choices=APPROVAL_STATUS_CHOICES,
                                        default='not_submitted', verbose_name="审批状态")
    need_approval = models.BooleanField(default=True, verbose_name="是否需要审批",
                                         help_text="创建时根据环境自动判断：prod/staging 需要审批，dev/test 不需要")
    release_mode = models.CharField(max_length=16, default='regular', verbose_name="发布方式",
                                    choices=[
                                        ('regular', '常规发布'),
                                        ('incremental', '增量发布'),
                                        ('compensation', '补偿发布'),
                                        ('quick', '快速发布'),
                                        ('rollback', '回滚发布'),
                                        ('scale', '实例伸缩'),
                                        ('restart', '重启'),
                                        ('stop', '停机'),
                                        ('start', '启动'),
                                        ('traffic', '流量管理'),
                                    ],
                                    help_text="常规=完整CI/CD, 增量=仅未发布目标, 补偿=仅失败目标, 快速=复用CI产物, 回滚=回滚到历史版本, 运维操作=重启/停机/启动/流量管理")
    deploy_strategy = models.CharField(max_length=16, choices=STRATEGIES, default='rolling')
    deploy_mode = models.CharField(max_length=8, choices=DEPLOY_MODES, default='k8s',
                                   verbose_name="部署模式",
                                   help_text="继承自应用的部署模式，k8s=镜像部署, ec2=产物部署")
    canary_percent = models.IntegerField(default=10, verbose_name="灰度比例(%)")
    selected_targets = models.JSONField(null=True, blank=True, verbose_name="选择的目标",
                                        help_text="增量/补偿发布时选择的目标主机或Pod列表")
    rollback_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='rollback_releases', verbose_name="回滚来源",
                                      help_text="回滚发布时，标记从哪个发布单回滚")
    # 实例伸缩专用字段（release_mode='scale' 时有值）
    current_replicas = models.IntegerField(null=True, blank=True, verbose_name="当前实例数")
    target_replicas = models.IntegerField(null=True, blank=True, verbose_name="目标实例数")
    # 流量管理专用字段（release_mode='traffic' 时有值）
    traffic_action = models.CharField(max_length=16, blank=True, default='',
                                      verbose_name="流量操作",
                                      choices=[('take_out', '摘流'), ('restore', '挂流')],
                                      help_text="release_mode='traffic' 时使用")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_releases",
                                verbose_name="创建人")
    current_stage = models.CharField(max_length=32, blank=True, verbose_name="当前阶段")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "release"
        ordering = ["-created_at"]
        verbose_name = "发布单"
        verbose_name_plural = "发布单"

    def __str__(self):
        return f"{self.release_no} - {self.title}"


class ReleaseTask(models.Model):
    """发布阶段任务 — Per-Environment 模型：每个发布单固定 CI + CD 两步"""
    STAGES = [
        ('ci', 'CI 构建'),
        ('cd', 'CD 部署'),
    ]

    STATUS_CHOICES = [
        ('pending', '等待'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('skipped', '跳过'),
    ]

    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="tasks")
    stage = models.CharField(max_length=32, choices=STAGES, verbose_name="阶段")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    retry_count = models.IntegerField(default=0)
    message = models.TextField(blank=True, verbose_name="结果信息")

    class Meta:
        db_table = "release_task"
        ordering = ["release", "id"]
        unique_together = [("release", "stage")]
        verbose_name = "发布阶段任务"
        verbose_name_plural = "发布阶段任务"

    def __str__(self):
        return f"{self.release.release_no} - {self.get_stage_display()}"


class TaskLog(models.Model):
    """任务执行日志"""
    LEVELS = [
        ('info', 'Info'),
        ('warn', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]

    task = models.ForeignKey(ReleaseTask, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=8, choices=LEVELS, default='info')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_log"
        ordering = ["created_at"]
        verbose_name = "任务日志"
        verbose_name_plural = "任务日志"


class ReleaseVerification(models.Model):
    """发布自动验证记录 — 发布 CD 成功后自动执行（或详情页手动重跑）"""
    STATUS_CHOICES = [
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('skipped', '跳过'),
    ]

    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="verifications")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running')
    results = models.JSONField(default=list, verbose_name="检查结果",
                               help_text="[{name, status, evidence, duration_ms}, ...]")
    summary = models.TextField(blank=True, verbose_name="汇总文案",
                               help_text="如 '5/5 通过，耗时 8.4s'")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "release_verification"
        ordering = ["-created_at"]
        verbose_name = "发布验证记录"
        verbose_name_plural = "发布验证记录"

    def __str__(self):
        return f"{self.release.release_no} - {self.get_status_display()}"