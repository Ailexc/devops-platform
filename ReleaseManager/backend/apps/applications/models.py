from django.db import models
from apps.accounts.models import User
from apps.organizations.models import BusinessLine
from apps.infrastructures.models import Environment, Cluster, K8sNamespace


LANGUAGES = [
    ('python', 'Python'),
    ('go', 'Go'),
    ('node', 'Node.js'),
    ('java', 'Java'),
    ('other', '其他'),
]

APP_TYPES = [
    ('web', 'Web 应用'),
    ('backend', '后端服务'),
    ('mobile', '移动应用'),
    ('middleware', '中间件'),
    ('job', '定时任务'),
    ('data', '数据服务'),
]

STATUS_CHOICES = [
    ('active', '启用'),
    ('inactive', '停用'),
]

STRATEGIES = [
    ('rolling', '滚动更新'),
    ('blue_green', '蓝绿部署'),
    ('canary', '灰度发布'),
]

DEPLOY_MODES = [
    ('k8s', 'K8s 镜像部署'),
    ('ec2', 'EC2 产物部署'),
]

PRIORITIES = [
    ('p0', 'P0 核心'),
    ('p1', 'P1 重要'),
    ('p2', 'P2 普通'),
    ('p3', 'P3 低优先级'),
]

SLA_LEVELS = [
    ('99.99', '99.99%'),
    ('99.9', '99.9%'),
    ('99.5', '99.5%'),
    ('99', '99%'),
]

ARTIFACT_TYPES = [
    ('docker', 'Docker 镜像'),
    ('jar', 'JAR 包'),
    ('static', '静态资源'),
    ('binary', '二进制包'),
]

SECURITY_LEVELS = [
    ('public', '公开'),
    ('internal', '内部'),
    ('confidential', '机密'),
    ('secret', '绝密'),
]


class Application(models.Model):
    """应用"""
    name = models.CharField(max_length=64, verbose_name="应用名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="应用编码")
    description = models.TextField(blank=True, verbose_name="描述")
    app_type = models.CharField(max_length=16, choices=APP_TYPES, default='backend',
                                verbose_name="应用类型")
    language = models.CharField(max_length=16, choices=LANGUAGES, verbose_name="开发语言")
    repo_url = models.URLField(blank=True, verbose_name="仓库地址")
    repo_branch = models.CharField(max_length=64, default='main', verbose_name="默认分支")
    git_group = models.CharField(max_length=64, blank=True, verbose_name="Git 所属组")
    domain = models.CharField(max_length=128, blank=True, verbose_name="域名/二级域名")
    deploy_mode = models.CharField(max_length=8, choices=DEPLOY_MODES, default='k8s',
                                   verbose_name="部署模式", null=True, blank=True)
    artifact_type = models.CharField(max_length=16, choices=ARTIFACT_TYPES, default='docker',
                                     verbose_name="产物类型")
    builder_image = models.CharField(max_length=128, blank=True, verbose_name="环境基础镜像",
                                     help_text="CI 编译用镜像，如 golang:1.23-alpine")
    base_image = models.CharField(max_length=128, blank=True, verbose_name="应用基础镜像",
                                  help_text="运行环境镜像，如 alpine:3.20，产物拷贝到此镜像中")
    business_line = models.ForeignKey(BusinessLine, on_delete=models.CASCADE, related_name="apps")
    owner_group = models.ForeignKey(
        'organizations.Group', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="owned_apps", verbose_name="承接组"
    )
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="owned_apps",
                              verbose_name="应用负责人")
    owner_ids = models.JSONField(default=list, blank=True, verbose_name="负责人 ID 列表",
                                 help_text="支持多个负责人的 ID 列表")
    product_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="product_owned_apps", verbose_name="产品负责人")
    qa_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="qa_owned_apps", verbose_name="测试负责人")
    ops_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="ops_owned_apps", verbose_name="运维负责人")
    priority = models.CharField(max_length=8, choices=PRIORITIES, default='p2',
                                verbose_name="应用等级")
    sla = models.CharField(max_length=8, choices=SLA_LEVELS, default='99.9',
                           verbose_name="SLA 等级")
    security_level = models.CharField(max_length=16, choices=SECURITY_LEVELS, default='internal',
                                      verbose_name="安全等级")
    is_core = models.BooleanField(default=False, verbose_name="是否核心应用")
    tech_stack = models.JSONField(default=list, blank=True, verbose_name="技术栈")
    tags = models.JSONField(default=list, blank=True, verbose_name="标签")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application"
        verbose_name = "应用"
        verbose_name_plural = "应用"

    def __str__(self):
        return f"{self.name}({self.code})"


class AppEnvConfig(models.Model):
    """应用在各环境下的部署配置"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="env_configs")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="+")
    namespace = models.ForeignKey(K8sNamespace, on_delete=models.CASCADE, related_name="+")
    deploy_strategy = models.CharField(max_length=16, choices=STRATEGIES, default='rolling')
    replicas = models.IntegerField(default=1, verbose_name="副本数")
    canary_percent = models.IntegerField(default=10, verbose_name="灰度比例(%)",
                                         help_text="仅灰度策略有效")
    image_repo = models.CharField(max_length=128, verbose_name="镜像仓库")
    container_port = models.IntegerField(default=8080, verbose_name="容器端口")
    health_check_path = models.CharField(max_length=64, default='/health', verbose_name="健康检查路径")
    cpu_limit = models.CharField(max_length=16, default='500m', verbose_name="CPU 限制")
    memory_limit = models.CharField(max_length=16, default='512Mi', verbose_name="内存限制")
    auto_rollback = models.BooleanField(default=True, verbose_name="失败自动回滚")
    health_check_timeout = models.IntegerField(default=300, verbose_name="健康检查超时(秒)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_env_config"
        unique_together = [("application", "environment")]
        verbose_name = "应用环境配置"
        verbose_name_plural = "应用环境配置"

    def __str__(self):
        return f"{self.application.name} - {self.environment.name}"


class ImageRegistry(models.Model):
    """镜像注册表 - 按开发语言管理默认的双镜像配置"""
    language = models.CharField(max_length=16, choices=LANGUAGES, unique=True,
                                verbose_name="开发语言")
    registry = models.CharField(max_length=256, default='docker.io', verbose_name="镜像仓库来源",
                                help_text="镜像仓库地址，如 docker.io、registry.cn-hangzhou.aliyuncs.com")
    builder_image = models.CharField(max_length=128, verbose_name="环境基础镜像",
                                     help_text="CI 编译阶段使用，含编译器/工具链，如 golang:1.23-alpine")
    base_image = models.CharField(max_length=128, verbose_name="应用基础镜像",
                                  help_text="CD 运行阶段使用，预装运行环境，如 alpine:3.20")
    description = models.TextField(blank=True, verbose_name="说明")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "image_registry"
        verbose_name = "镜像注册表"
        verbose_name_plural = "镜像注册表"

    def __str__(self):
        return f"{self.get_language_display()} → {self.builder_image} / {self.base_image}"