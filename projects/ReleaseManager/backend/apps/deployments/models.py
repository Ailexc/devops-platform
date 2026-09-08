from django.db import models
from apps.accounts.models import User
from apps.releases.models import Release
from apps.applications.models import Application
from apps.infrastructures.models import Environment


class DeployHistory(models.Model):
    """部署历史"""
    ACTIONS = [
        ('deploy', '部署'),
        ('rollback', '回滚'),
        ('restart', '重启'),
        ('scale', '扩缩容'),
    ]

    STATUS_CHOICES = [
        ('pending', '等待'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="deploy_histories")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="+")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    version = models.CharField(max_length=32, verbose_name="版本")
    image_tag = models.CharField(max_length=128, verbose_name="镜像 Tag")
    action = models.CharField(max_length=16, choices=ACTIONS, verbose_name="操作类型")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    strategy = models.CharField(max_length=16, verbose_name="部署策略")
    canary_percent = models.IntegerField(null=True, blank=True, verbose_name="灰度比例")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "deploy_history"
        ordering = ["-created_at"]
        verbose_name = "部署历史"
        verbose_name_plural = "部署历史"

    def __str__(self):
        return f"{self.application.name} - {self.version} - {self.get_action_display()}"


class PodInstance(models.Model):
    """部署后的 Pod 状态快照"""
    STATUSES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown'),
    ]

    deploy_history = models.ForeignKey(DeployHistory, on_delete=models.CASCADE, related_name="pods")
    pod_name = models.CharField(max_length=128, verbose_name="Pod 名称")
    node_name = models.CharField(max_length=128, blank=True, verbose_name="节点名称")
    ip = models.CharField(max_length=32, blank=True, verbose_name="Pod IP")
    status = models.CharField(max_length=16, choices=STATUSES, verbose_name="Pod 状态")
    image = models.CharField(max_length=256, blank=True, verbose_name="镜像")
    started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pod_instance"
        verbose_name = "Pod 实例"
        verbose_name_plural = "Pod 实例"

    def __str__(self):
        return self.pod_name


class RollbackRecord(models.Model):
    """回滚记录"""
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="rollbacks")
    deploy_history = models.ForeignKey(DeployHistory, on_delete=models.CASCADE, related_name="+")
    from_version = models.CharField(max_length=32, verbose_name="回滚前版本")
    to_version = models.CharField(max_length=32, verbose_name="回滚目标版本")
    reason = models.TextField(blank=True, verbose_name="回滚原因")
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rollback_record"
        ordering = ["-created_at"]
        verbose_name = "回滚记录"
        verbose_name_plural = "回滚记录"