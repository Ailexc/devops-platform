from django.db import models
from apps.accounts.models import User
from apps.applications.models import Application
from apps.releases.models import Release
from apps.infrastructures.models import Environment


class ConfigTemplate(models.Model):
    """配置模板 - 定义配置的结构和变量占位符"""
    TEMPLATE_TYPES = [
        ('yaml', 'YAML 配置文件'),
        ('properties', 'Properties 文件'),
        ('env', '环境变量'),
        ('json', 'JSON 配置文件'),
        ('nginx', 'Nginx 配置'),
        ('custom', '自定义'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="config_templates",
                                    verbose_name="所属应用")
    name = models.CharField(max_length=64, verbose_name="模板名称")
    template_type = models.CharField(max_length=16, choices=TEMPLATE_TYPES, verbose_name="模板类型")
    template_content = models.TextField(verbose_name="模板内容")
    description = models.TextField(blank=True, verbose_name="描述")
    deploy_path = models.CharField(max_length=256, blank=True, verbose_name="部署路径",
                                   help_text="如 /etc/app/config.yaml")
    version = models.IntegerField(default=1, verbose_name="模板版本")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_template"
        unique_together = [("application", "name")]
        verbose_name = "配置模板"
        verbose_name_plural = "配置模板"

    def __str__(self):
        return f"{self.application.name} - {self.name}"


class ConfigVariable(models.Model):
    """配置变量 - 模板中使用的变量定义"""
    VALUE_TYPES = [
        ('string', '字符串'),
        ('number', '数字'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
        ('text', '多行文本'),
    ]

    template = models.ForeignKey(ConfigTemplate, on_delete=models.CASCADE, related_name="variables",
                                 verbose_name="所属模板")
    key = models.CharField(max_length=128, verbose_name="变量名",
                           help_text="如 DB_URL, LOG_LEVEL, APP_NAME")
    value_type = models.CharField(max_length=16, choices=VALUE_TYPES, default='string')
    default_value = models.TextField(blank=True, verbose_name="默认值")
    description = models.TextField(blank=True, verbose_name="变量说明")
    is_secret = models.BooleanField(default=False, verbose_name="是否为敏感变量",
                                    help_text="敏感变量在 UI 中加密显示，如密码、Token")
    is_required = models.BooleanField(default=True, verbose_name="是否必填")
    validation_rule = models.CharField(max_length=256, blank=True, verbose_name="校验规则",
                                       help_text="正则表达式或取值范围")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "config_variable"
        unique_together = [("template", "key")]
        ordering = ["template", "sort_order"]
        verbose_name = "配置变量"
        verbose_name_plural = "配置变量"

    def __str__(self):
        return f"{self.template.name} - {self.key}"


class ConfigVariableValue(models.Model):
    """配置变量值 - 每个变量在不同环境下的具体值"""
    variable = models.ForeignKey(ConfigVariable, on_delete=models.CASCADE, related_name="values")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    value = models.TextField(verbose_name="变量值")
    encrypted_value = models.TextField(blank=True, verbose_name="加密值")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_variable_value"
        unique_together = [("variable", "environment")]
        verbose_name = "变量值"
        verbose_name_plural = "变量值"

    def __str__(self):
        return f"{self.variable.key} @ {self.environment.name}"


class ConfigRelease(models.Model):
    """配置发布记录 - 记录某次发布时使用的配置版本"""
    template = models.ForeignKey(ConfigTemplate, on_delete=models.CASCADE, related_name="releases")
    version = models.IntegerField(verbose_name="配置版本号")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name="+")
    rendered_content = models.TextField(verbose_name="渲染后的配置内容")
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="config_releases")
    status = models.CharField(max_length=16, choices=[
        ('pending', '待应用'),
        ('applied', '已应用'),
        ('rolled_back', '已回滚'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        db_table = "config_release"
        ordering = ["-created_at"]
        verbose_name = "配置发布记录"
        verbose_name_plural = "配置发布记录"

    def __str__(self):
        return f"{self.template.name} v{self.version} @ {self.environment.name}"