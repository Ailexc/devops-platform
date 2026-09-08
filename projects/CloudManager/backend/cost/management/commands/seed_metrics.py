"""
模拟采集器写入资源指标摘要 —— 供降配检测使用。

真实场景：采集平台从监控系统（CloudWatch/云监控/Prometheus）拉取指标，
统一拉平为 avg_cpu_7d / avg_mem_7d 写入 CMDB Resource.metadata。
本命令模拟该行为，为 Demo 提供降配检测的数据。

用法: python manage.py seed_metrics
幂等：仅对缺少指标摘要的资源写入。
"""
import random

from django.core.management.base import BaseCommand

from cmdb.models import Resource


class Command(BaseCommand):
    help = '模拟采集器向 Resource.metadata 写入指标摘要（avg_cpu_7d / avg_mem_7d）'

    def handle(self, *args, **options):
        written = 0
        qs = Resource.objects.filter(resource_type='instance', status='running', is_deleted=False)
        for res in qs:
            meta = dict(res.metadata or {})
            if 'avg_cpu_7d' in meta:
                continue  # 已有指标，跳过
            # 模拟：约 30% 为低利用率（触发降配），其余正常
            if random.random() < 0.3:
                avg_cpu = round(random.uniform(1.0, 4.8), 1)
            else:
                avg_cpu = round(random.uniform(8.0, 65.0), 1)
            avg_mem = round(random.uniform(10.0, 70.0), 1)
            meta['avg_cpu_7d'] = avg_cpu
            meta['avg_mem_7d'] = avg_mem
            res.metadata = meta
            res.save(update_fields=['metadata', 'updated_at'])
            written += 1
        self.stdout.write(self.style.SUCCESS(
            f'完成：为 {written} 个运行中实例写入指标摘要（模拟采集器）'
        ))
