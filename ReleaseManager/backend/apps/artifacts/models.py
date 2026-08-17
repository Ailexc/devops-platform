from django.db import models
from apps.accounts.models import User
from apps.applications.models import Application
from apps.releases.models import Release
from apps.infrastructures.models import Environment


STATUS_CHOICES = [
    ('active', '启用'),
    ('inactive', '停用'),
]


class ArtifactRepository(models.Model):
    """制品仓库 - 存储制品的后端系统"""
    REPO_TYPES = [
        ('docker_registry', 'Docker Registry'),
        ('harbor', 'Harbor'),
        ('nexus', 'Nexus'),
        ('s3', 'S3 存储'),
        ('local', '本地存储'),
    ]

    name = models.CharField(max_length=64, verbose_name="仓库名称")
    repo_type = models.CharField(max_length=32, choices=REPO_TYPES, verbose_name="仓库类型")
    url = models.URLField(verbose_name="仓库地址")
    username = models.CharField(max_length=64, blank=True, verbose_name="用户名")
    password = models.CharField(max_length=128, blank=True, verbose_name="密码")
    is_default = models.BooleanField(default=False, verbose_name="是否默认仓库")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artifact_repository"
        verbose_name = "制品仓库"
        verbose_name_plural = "制品仓库"

    def __str__(self):
        return self.name


class Artifact(models.Model):
    """制品 - 构建产物的记录，连接 CI 和 CD 的桥梁"""
    ARTIFACT_TYPES = [
        ('docker_image', 'Docker 镜像'),
        ('jar', 'JAR 包'),
        ('war', 'WAR 包'),
        ('npm_package', 'NPM 包'),
        ('python_wheel', 'Python Wheel'),
        ('binary', '二进制文件'),
        ('static_files', '静态文件'),
        ('helm_chart', 'Helm Chart'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="artifacts",
                                    verbose_name="所属应用")
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="artifacts", verbose_name="关联发布单")
    version = models.CharField(max_length=64, verbose_name="版本号")
    artifact_type = models.CharField(max_length=32, choices=ARTIFACT_TYPES, verbose_name="制品类型")
    repository = models.ForeignKey(ArtifactRepository, on_delete=models.CASCADE, related_name="+",
                                   verbose_name="制品仓库")
    storage_path = models.CharField(max_length=512, verbose_name="存储路径",
                                    help_text="Docker 镜像的完整名称或文件的存储路径")
    image_tag = models.CharField(max_length=128, blank=True, verbose_name="镜像 Tag",
                                 help_text="Docker 镜像特有，如 v1.2.3")
    # 双镜像支持
    builder_image = models.CharField(max_length=128, blank=True, verbose_name="环境基础镜像",
                                     help_text="CI 编译阶段使用的镜像，如 golang:1.23-alpine")
    base_image = models.CharField(max_length=128, blank=True, verbose_name="应用基础镜像",
                                  help_text="预装运行环境的镜像，产物拷贝到该镜像中组装")
    base_image_id = models.CharField(max_length=128, blank=True, verbose_name="应用基础镜像 ID",
                                     help_text="Spug 中预绑定的应用基础镜像的 ECR 地址")
    file_name = models.CharField(max_length=256, blank=True, verbose_name="文件名",
                                 help_text="文件制品特有")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小(字节)")
    checksum = models.CharField(max_length=128, blank=True, verbose_name="校验值(SHA256)")
    build_job_url = models.URLField(blank=True, verbose_name="构建任务链接")
    build_duration = models.IntegerField(default=0, verbose_name="构建耗时(秒)")
    commit_id = models.CharField(max_length=64, blank=True, verbose_name="构建时的 Commit ID")
    branch = models.CharField(max_length=64, blank=True, verbose_name="构建分支")
    metadata = models.JSONField(default=dict, verbose_name="额外元数据",
                                help_text="构建参数、环境信息、依赖信息等")
    current_env = models.CharField(max_length=16, blank=True, verbose_name="当前所在环境",
                                   help_text="dev / test / staging / prod")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "artifact"
        ordering = ["-created_at"]
        verbose_name = "制品"
        verbose_name_plural = "制品"
        indexes = [
            models.Index(fields=["application", "-created_at"]),
            models.Index(fields=["version"]),
        ]

    def __str__(self):
        return f"{self.application.name} - {self.version}"


class ArtifactPromotion(models.Model):
    """制品晋级记录 - 制品从一个环境'晋级'到下一个环境"""
    PROMOTION_STATUS = [
        ('pending', '待晋级'),
        ('promoted', '已晋级'),
        ('rejected', '驳回'),
        ('rolled_back', '已回退'),
    ]

    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="promotions")
    from_env = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+",
                                 verbose_name="来源环境")
    to_env = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+",
                               verbose_name="目标环境")
    status = models.CharField(max_length=16, choices=PROMOTION_STATUS, default='pending')
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="+")
    promoted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    promoted_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artifact_promotion"
        ordering = ["-created_at"]
        verbose_name = "制品晋级记录"
        verbose_name_plural = "制品晋级记录"

    def __str__(self):
        return f"{self.artifact} -> {self.to_env.name}"