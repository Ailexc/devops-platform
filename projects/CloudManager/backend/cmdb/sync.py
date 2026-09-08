"""
元数据同步服务（模拟采集系统向云管推送数据）。

真实架构：两个独立采集系统分别做"定时同步"和"事件同步"维持 CMDB 准确性；
云管只接收数据写入本地整合视图，并标记来源系统与同步方式。
"""
import logging

from django.utils import timezone

from .models import Resource, ResourceChange, SyncJob

logger = logging.getLogger(__name__)


def _upsert_resource(account, vo, source_system='cmdb', sync_mode='schedule'):
    """按 cloud_resource_id 增量 upsert 一个资源，返回 (created, changed)"""
    before = None
    obj, created = Resource.objects.get_or_create(
        cloud_resource_id=vo.cloud_resource_id,
        defaults={
            'account': account,
            'provider_type': account.provider_type,
            'resource_type': vo.resource_type,
            'resource_name': vo.resource_name,
            'region': vo.region,
            'zone': vo.zone,
            'status': vo.status,
            'spec': vo.spec,
            'metadata': vo.metadata,
            'source': 0,
            'source_system': source_system,
            'sync_mode': sync_mode,
            'external_id': vo.cloud_resource_id,
        },
    )
    if created:
        ResourceChange.objects.create(
            resource=obj, action='sync', after_data={'source_system': source_system},
            operator='system:collection', source='sync',
        )
        return True, False

    changed = False
    before = {
        'status': obj.status,
        'resource_name': obj.resource_name,
        'spec': obj.spec,
        'region': obj.region,
    }
    if obj.status != vo.status or obj.resource_name != vo.resource_name or obj.spec != vo.spec:
        obj.status = vo.status
        obj.resource_name = vo.resource_name
        obj.spec = vo.spec
        obj.metadata = vo.metadata
        obj.source_system = source_system
        obj.sync_mode = sync_mode
        obj.external_id = vo.cloud_resource_id
        obj.updated_at = timezone.now()
        obj.save(update_fields=[
            'status', 'resource_name', 'spec', 'metadata',
            'source_system', 'sync_mode', 'external_id', 'updated_at',
        ])
        ResourceChange.objects.create(
            resource=obj, action='sync', before_data=before,
            after_data={'status': obj.status, 'spec': obj.spec},
            operator='system:collection', source='sync',
        )
        changed = True
    return False, changed


def run_schedule_sync(job_type='schedule', source_system='cmdb'):
    """定时同步：模拟采集系统A 从 CMDB 拉取全量/增量数据写入整合视图"""
    from cmdb.models import CloudAccount
    from provider.core import get_provider

    job = SyncJob.objects.create(job_type=job_type, status='running',
                                 source_system=source_system)
    try:
        account = CloudAccount.objects.filter(provider_type='mock').first()
        if not account:
            job.status = 'failed'
            job.message = '未找到 Mock 云账号'
            job.finished_at = timezone.now()
            job.save()
            return job

        provider = get_provider('mock')
        created = changed = 0
        for region in provider.REGIONS:
            for vo in (provider.list_instances(region) + provider.list_vpcs(region)
                       + provider.list_subnets(region) + provider.list_security_groups(region)
                       + provider.list_disks(region) + provider.list_load_balancers(region)):
                c, u = _upsert_resource(account, vo, source_system, 'schedule')
                created += c
                changed += u

        job.status = 'success'
        job.total_count = created + changed
        job.message = f'新增 {created} 条，更新 {changed} 条'
    except Exception as e:  # noqa: BLE001
        logger.exception('同步失败')
        job.status = 'failed'
        job.message = str(e)[:200]
    job.finished_at = timezone.now()
    job.save()
    return job


def handle_event(payload):
    """事件同步：模拟采集系统B 推送资源变更事件"""
    from cmdb.models import CloudAccount
    from provider.core import get_provider

    event_type = payload.get('event_type', 'resource.updated')
    data = payload.get('resource', {})
    job = SyncJob.objects.create(job_type='event', status='running',
                                 source_system=payload.get('source_system', 'collection-b'))
    try:
        account = CloudAccount.objects.filter(provider_type='mock').first()
        if not account:
            raise ValueError('未找到 Mock 云账号')

        if event_type == 'resource.deleted':
            deleted = Resource.objects.filter(cloud_resource_id=data.get('cloud_resource_id')).first()
            count = 0
            if deleted:
                ResourceChange.objects.create(
                    resource=deleted, action='event_delete', before_data={'status': deleted.status},
                    operator='system:collection-b', source='sync',
                )
                deleted.is_deleted = True
                deleted.save(update_fields=['is_deleted', 'updated_at'])
                count = 1
            job.status = 'success'
            job.total_count = count
            job.message = f'事件 {event_type} 处理 {count} 条'
        else:
            vo = _build_vo_from_event(data)
            created, changed = _upsert_resource(account, vo, 'cmdb', 'event')
            job.status = 'success'
            job.total_count = created + changed
            job.message = f'事件 {event_type}：新增 {int(created)}，更新 {int(changed)}'
    except Exception as e:  # noqa: BLE001
        job.status = 'failed'
        job.message = str(e)[:200]
    job.finished_at = timezone.now()
    job.save()
    return job


def _build_vo_from_event(data):
    """事件数据 -> 统一 ResourceVO"""
    from provider.core import ResourceVO

    return ResourceVO(
        resource_type=data.get('resource_type', 'instance'),
        resource_name=data.get('resource_name', 'event-resource'),
        cloud_resource_id=data.get('cloud_resource_id', ''),
        region=data.get('region', 'cn-hangzhou'),
        status=data.get('status', 'running'),
        spec=data.get('spec', ''),
        zone=data.get('zone', ''),
        metadata=data.get('metadata', {}),
    )
