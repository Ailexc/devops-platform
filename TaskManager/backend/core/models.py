"""
core models — 配置层数据模型（模拟 Apollo 配置中心）。

真实生产环境中账号/区域/endpoint 配置在 Apollo 配置中心，
demo 环境中用 DB 表承载（source 字段标识来源：apollo/db/seed）。
"""

from django.db import models


class AccountRegion(models.Model):
    """账号/区域配置 — 任务树「配置层」数据源。

    - account:   账号名（如 生产环境）
    - account_id: AWS 账号 ID
    - region:    区域代码（如 ap-northeast-1）
    - endpoint:  AWS endpoint / 数据源地址
    - cron:      区域级默认定时表达式
    - source:    配置来源（seed=演示播种, apollo=配置中心, db=手动维护）
    - enabled:   是否启用（下线字段，false 时不参与调度/任务树）
    """

    account = models.CharField("账号", max_length=100)
    account_id = models.CharField("账号ID", max_length=50, blank=True, default="")
    region = models.CharField("区域", max_length=50)
    endpoint = models.CharField("Endpoint", max_length=300, blank=True, default="")
    cron = models.CharField("默认Cron", max_length=50, blank=True, default="0 2 * * *")
    concurrency = models.IntegerField("并发数", default=50)
    source = models.CharField("配置来源", max_length=20, default="seed")
    enabled = models.BooleanField("启用", default=True)

    class Meta:
        verbose_name = "账号区域配置"
        verbose_name_plural = "账号区域配置"
        unique_together = ("account", "region")
        ordering = ["account", "region"]

    def __str__(self):
        return f"{self.account}/{self.region}"
