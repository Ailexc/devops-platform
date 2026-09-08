from django.db import models


class ExecutionRecord(models.Model):
    """任务执行历史记录 — 两级实体模型（父+子同表）。

    所有粒度的执行都写入同一张表：
    - parent=None  → 任务级记录（region/group/resource/relation 均可）
    - parent!=None → 进程级子记录（region/group 级任务展开的每个资源/关系进程）

    前端只看"有没有子记录"决定是否显示进程列表，不判断 scope。
    """

    # 任务粒度
    SCOPE_CHOICES = [
        ("region", "区域级"),
        ("group", "资源组级"),
        ("resource", "资源级"),
        ("relation", "关系级"),
        ("test", "测试"),
    ]
    scope = models.CharField("任务粒度", max_length=20, choices=SCOPE_CHOICES, default="region")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        verbose_name="父任务",
    )

    # 任务元信息
    task_name = models.CharField("任务名称", max_length=200)
    module = models.CharField("所属模块", max_length=50)           # AWS / 内部 / 巡检 / 测试
    target = models.CharField("执行目标", max_length=300, blank=True, default="")
    trigger = models.CharField("触发方式", max_length=50)          # Cron / 定时(15min) / 人工 / 测试

    # 执行状态
    STATUS_CHOICES = [
        ("success", "成功"),
        ("failed", "失败"),
        ("partial", "部分失败"),
        ("running", "运行中"),
        ("pending", "等待中"),
    ]
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")

    # 执行详情
    celery_task_id = models.CharField("Celery Task ID", max_length=200, blank=True, default="", db_index=True)
    error = models.TextField("错误信息", blank=True, default="")
    detail = models.TextField("执行详情", blank=True, default="")
    duration = models.CharField("耗时", max_length=30, blank=True, default="-")
    result = models.JSONField("执行结果", blank=True, null=True)   # 存放 Celery 返回的完整结果

    # 生命周期事件
    lifecycle_events = models.JSONField("生命周期事件", default=list, blank=True)
    # 格式: [{"ts": "14:00:01", "event": "created", "label": "任务创建", "detail": "...", "icon": "📥"}]

    # 派发参数（供一键重试复用）：{"account", "region", "scope", "target", "mode", "trigger", "resource_ids"}
    params = models.JSONField("派发参数", blank=True, default=dict, null=True)

    # 时间
    started_at = models.DateTimeField("开始时间", auto_now_add=True)
    finished_at = models.DateTimeField("结束时间", blank=True, null=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "执行记录"
        verbose_name_plural = "执行记录"

    def __str__(self):
        return f"[{self.status}] {self.task_name} ({self.started_at:%m-%d %H:%M})"


class DailyTaskStat(models.Model):
    """按天聚合统计（保留 30 天，供大盘趋势/可靠性观察）。

    任务完成时增量更新，与执行明细解耦，大盘查询不扫明细表。
    """

    stat_date = models.DateField("日期")
    module = models.CharField("模块", max_length=50, default="AWS")
    total = models.IntegerField("任务数", default=0)
    success = models.IntegerField("成功数", default=0)
    failed = models.IntegerField("失败数", default=0)
    total_duration = models.FloatField("总耗时(秒)", default=0)
    synced_count = models.IntegerField("同步资源量", default=0)

    class Meta:
        verbose_name = "日任务统计"
        verbose_name_plural = "日任务统计"
        unique_together = ("stat_date", "module")
        ordering = ["-stat_date"]

    def __str__(self):
        return f"{self.stat_date} {self.module}: {self.total} tasks"
