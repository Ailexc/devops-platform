"""
补充多云模拟数据 —— 阿里云 / AWS 账号 + 资源 + 指标摘要，并更新规则云范围。

真实场景：采集平台从各云同步资源到 CMDB。本命令模拟该行为，为成本优化
Demo 提供多云数据，使大屏"覆盖云厂商 / 按云节省"、报告"云→账号→区域→类型"
层级树更加完整。

用法: python manage.py seed_multicloud
幂等：账号/资源按唯一标识 get_or_create，规则按名称 update scope。
"""
from django.core.management.base import BaseCommand

from cmdb.models import CloudAccount, Resource
from cost.models import OptimizationRule


def _get_account(account_name, provider_type):
    acc, _ = CloudAccount.objects.get_or_create(
        account_name=account_name, provider_type=provider_type,
        defaults={'status': 1, 'sync_status': 2, 'regions': ''},
    )
    return acc


def _upsert_resource(account, rtype, name, cid, region, status, spec, metadata):
    res, created = Resource.objects.get_or_create(
        account=account, cloud_resource_id=cid,
        defaults={
            'provider_type': account.provider_type,
            'resource_type': rtype,
            'resource_name': name,
            'region': region,
            'status': status,
            'spec': spec,
            'metadata': metadata,
            'source': 0,
        },
    )
    if not created:
        # 已有则更新状态/指标
        res.status = status
        res.spec = spec
        res.metadata = metadata
        res.save(update_fields=['status', 'spec', 'metadata', 'updated_at'])
    return res


ALIYUN_RESOURCES = [
    # (resource_type, name, cid, region, status, spec, metadata)
    ('instance', 'aliyun-web-001', 'i-aliyun-web001', 'cn-hangzhou', 'stopped', 'ecs.g6.xlarge',
     {'cpu': 4, 'memory_gb': 16, 'os': 'centos-7.9'}),
    ('instance', 'aliyun-api-002', 'i-aliyun-api002', 'cn-beijing', 'stopped', 'ecs.g6.large',
     {'cpu': 2, 'memory_gb': 8, 'os': 'ubuntu-22.04'}),
    ('instance', 'aliyun-worker-003', 'i-aliyun-wrk003', 'cn-hangzhou', 'running', 'ecs.g6.2xlarge',
     {'cpu': 8, 'memory_gb': 32, 'os': 'centos-7.9', 'avg_cpu_7d': 3.5, 'avg_mem_7d': 15.0}),
    ('instance', 'aliyun-cache-004', 'i-aliyun-cache04', 'cn-shanghai', 'running', 'ecs.c7.large',
     {'cpu': 2, 'memory_gb': 8, 'os': 'ubuntu-22.04', 'avg_cpu_7d': 25.0, 'avg_mem_7d': 40.0}),
    ('disk', 'aliyun-db-disk', 'd-aliyun-db001', 'cn-hangzhou', 'available', '500GB SSD', {}),
    ('disk', 'aliyun-data-disk', 'd-aliyun-data02', 'cn-beijing', 'available', '1TB HDD', {}),
]

AWS_RESOURCES = [
    ('instance', 'aws-web-001', 'i-aws-web001', 'us-east-1', 'stopped', 't3.xlarge',
     {'cpu': 4, 'memory_gb': 16, 'os': 'amzn2'}),
    ('instance', 'aws-api-002', 'i-aws-api002', 'us-east-1', 'running', 't3.large',
     {'cpu': 2, 'memory_gb': 8, 'os': 'amzn2', 'avg_cpu_7d': 4.2, 'avg_mem_7d': 20.0}),
    ('instance', 'aws-db-003', 'i-aws-db003', 'us-east-1', 'running', 't3.large',
     {'cpu': 2, 'memory_gb': 8, 'os': 'ubuntu-22.04', 'avg_cpu_7d': 42.0, 'avg_mem_7d': 55.0}),
    ('disk', 'aws-ebs-disk', 'd-aws-ebs001', 'us-east-1', 'available', '200GB SSD', {}),
]

# 按规则名更新云范围（让云分组生效）
RULE_CLOUD_SCOPE = {
    '闲置主机检测': '阿里云',
    '低利用率降配': '阿里云',
    '闲置实例检测': 'AWS',
    '低利用率实例': 'AWS',
}


class Command(BaseCommand):
    help = '补充阿里云/AWS 多云模拟数据 + 更新规则云范围'

    def handle(self, *args, **options):
        # 1. 账号
        aliyun = _get_account('阿里云主账号', 'aliyun')
        aws = _get_account('AWS主账号', 'aws')
        self.stdout.write(f'  账号就绪: {aliyun.account_name}(aliyun) / {aws.account_name}(aws)')

        # 2. 资源
        for spec in ALIYUN_RESOURCES:
            _upsert_resource(aliyun, *spec)
        for spec in AWS_RESOURCES:
            _upsert_resource(aws, *spec)
        self.stdout.write(self.style.SUCCESS(
            f'  资源就绪: 阿里云 {len(ALIYUN_RESOURCES)} 个 / AWS {len(AWS_RESOURCES)} 个'
        ))

        # 3. 更新规则云范围
        updated = 0
        for rule_name, cloud in RULE_CLOUD_SCOPE.items():
            for r in OptimizationRule.objects.filter(name=rule_name):
                scope = dict(r.scope or {})
                scope['cloud'] = cloud
                r.scope = scope
                r.save(update_fields=['scope', 'updated_at'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'  规则云范围更新: {updated} 条'))
