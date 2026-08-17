from django.db import models
from django.conf import settings


ENV_TYPES = [
    ('dev', '开发'),
    ('test', '测试'),
    ('staging', '预发'),
    ('prod', '生产'),
]

NETWORK_TYPES = [
    ('internal', '内网'),
    ('public', '公网'),
    ('dmz', 'DMZ'),
]

CLOUD_PROVIDERS = [
    ('aws', 'AWS'),
    ('aliyun', '阿里云'),
    ('tencent', '腾讯云'),
    ('huawei', '华为云'),
    ('azure', 'Azure'),
    ('gcp', 'GCP'),
]

STATUS_CHOICES = [
    ('active', '启用'),
    ('inactive', '停用'),
]

DEPLOY_TYPES = [
    ('k8s', 'Kubernetes'),
    ('ec2', 'EC2 / 虚拟机'),
]


class Environment(models.Model):
    """部署环境"""
    name = models.CharField(max_length=32, verbose_name="环境名称")
    code = models.CharField(max_length=16, unique=True, verbose_name="环境编码")
    env_type = models.CharField(max_length=16, choices=ENV_TYPES, default='dev', verbose_name="环境类型")
    description = models.TextField(blank=True, verbose_name="环境说明")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_prod = models.BooleanField(default=False, verbose_name="是否生产环境")
    cloud_provider = models.CharField(max_length=16, choices=CLOUD_PROVIDERS, blank=True,
                                      verbose_name="云厂商")
    account_id = models.CharField(max_length=32, blank=True, verbose_name="所属账号")
    region = models.CharField(max_length=32, blank=True, verbose_name="地域")
    zone = models.CharField(max_length=32, blank=True, verbose_name="可用区")
    network_type = models.CharField(max_length=16, choices=NETWORK_TYPES, default='internal',
                                    verbose_name="网络类型")
    k8s_context = models.CharField(max_length=64, blank=True, verbose_name="K8s Context")
    cost_center = models.CharField(max_length=32, blank=True, verbose_name="成本中心")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="owned_environments", verbose_name="环境负责人"
    )
    deploy_type = models.CharField(max_length=8, choices=DEPLOY_TYPES, default='k8s',
                                   verbose_name="部署类型")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "environment"
        ordering = ["sort_order"]
        verbose_name = "环境"
        verbose_name_plural = "环境"

    def __str__(self):
        return self.name


class Cluster(models.Model):
    """K8s 集群"""
    name = models.CharField(max_length=64, verbose_name="集群名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="集群编码")
    api_server = models.URLField(verbose_name="API Server 地址")
    kubeconfig = models.TextField(blank=True, verbose_name="Kubeconfig 内容")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="clusters")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cluster"
        verbose_name = "集群"
        verbose_name_plural = "集群"

    def __str__(self):
        return self.name


class K8sNamespace(models.Model):
    """K8s 命名空间"""
    name = models.CharField(max_length=64, verbose_name="命名空间名称")
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="namespaces")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "k8s_namespace"
        unique_together = [("name", "cluster")]
        verbose_name = "K8s 命名空间"
        verbose_name_plural = "K8s 命名空间"

    def __str__(self):
        return f"{self.cluster.name}/{self.name}"