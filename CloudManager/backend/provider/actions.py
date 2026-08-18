"""
原子操作注册表：场景编排的可复用最小操作单元。
每个操作：参数校验 + 执行（云/Mock + CMDB 回写）+ 可选回滚。
"""
import logging
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ActionSpec:
    action_type: str
    name: str
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    need_approval: bool = True
    params_schema: Dict[str, Any] = field(default_factory=dict)
    rollback: Optional[Callable[[Dict[str, Any]], None]] = None


class ActionRegistry:
    """原子操作注册表（策略模式）"""
    _actions: Dict[str, ActionSpec] = {}

    @classmethod
    def register(cls, spec: ActionSpec):
        cls._actions[spec.action_type] = spec

    @classmethod
    def get(cls, action_type: str) -> ActionSpec:
        spec = cls._actions.get(action_type)
        if not spec:
            raise ValueError(f'未知原子操作: {action_type}')
        return spec

    @classmethod
    def list(cls):
        return [
            {'action_type': s.action_type, 'name': s.name, 'need_approval': s.need_approval}
            for s in cls._actions.values()
        ]


# ---------- 公共工具 ----------

def _mock_account():
    from cmdb.models import CloudAccount
    return CloudAccount.objects.filter(provider_type='mock').first()


def _write_change(resource, action, operator='scenario', before=None, after=None):
    from cmdb.models import ResourceChange
    ResourceChange.objects.create(
        resource=resource, action=action,
        before_data=before or {}, after_data=after or {},
        operator=operator, source='ticket',
    )


def _link(source_id, target_id, relation_type, strength='hard'):
    from cmdb.models import ResourceRelation
    ResourceRelation.objects.get_or_create(
        source_id=source_id, target_id=target_id, relation_type=relation_type,
        defaults={'strength': strength, 'relation_source': 'manual'},
    )


# ---------- 原子操作实现 ----------

def action_create_instance(params: Dict[str, Any]) -> Dict[str, Any]:
    """申请 N 台机器（Mock 云操作 + CMDB 回写）"""
    from cmdb.models import Resource
    from provider.core import get_provider

    account = _mock_account()
    provider = get_provider('mock')
    handle = provider.create_instance(params)
    data = handle.result.get('instance_data') or {}
    resource = Resource.objects.create(
        account=account,
        provider_type='mock',
        resource_type='instance',
        resource_name=data.get('resource_name') or params.get('name', 'scenario-instance'),
        cloud_resource_id=data.get('cloud_resource_id') or f'i-{uuid.uuid4().hex[:12]}',
        region=data.get('region') or params.get('region', 'cn-hangzhou'),
        zone=data.get('zone', ''),
        status='running',
        spec=data.get('spec') or params.get('spec', 't3.medium'),
        metadata=data.get('metadata', {}),
        source=1,
        source_system='manual',
        sync_mode='manual',
    )
    if params.get('application_id'):
        resource.application_id = params['application_id']
        resource.save(update_fields=['application', 'updated_at'])
    if params.get('security_group_id'):
        _link(resource.id, params['security_group_id'], 'attach_sg', 'hard')
    _write_change(resource, 'create', after=data)
    return {
        'resource_id': resource.id,
        'cloud_resource_id': resource.cloud_resource_id,
        'name': resource.resource_name,
        'message': f'实例 {resource.resource_name} 创建成功',
    }


def _rollback_resource_create(params: Dict[str, Any]):
    from cmdb.models import Resource
    Resource.objects.filter(id=params.get('resource_id')).update(is_deleted=True)


def action_create_subnet(params: Dict[str, Any]) -> Dict[str, Any]:
    """新建子网（依赖 VPC）"""
    from cmdb.models import Resource

    account = _mock_account()
    vpc_id = params.get('vpc_id')
    vpc = Resource.objects.filter(id=vpc_id, resource_type='vpc').first() if vpc_id else None
    if not vpc:
        vpc = Resource.objects.filter(resource_type='vpc').first()
    if not vpc:
        raise ValueError('未找到可用的 VPC')
    subnet = Resource.objects.create(
        account=account, provider_type='mock', resource_type='subnet',
        resource_name=params.get('name') or f'subnet-{uuid.uuid4().hex[:6]}',
        cloud_resource_id=f'subnet-{uuid.uuid4().hex[:12]}',
        region=params.get('region') or vpc.region, status='available',
        metadata={'cidr_block': params.get('cidr', '10.10.0.0/24')},
        source=1, source_system='manual', sync_mode='manual',
    )
    _link(subnet.id, vpc.id, 'belongs_to_vpc', 'hard')
    _write_change(subnet, 'create', after={'cidr': params.get('cidr', '10.10.0.0/24')})
    return {'resource_id': subnet.id, 'cloud_resource_id': subnet.cloud_resource_id,
            'name': subnet.resource_name, 'vpc': vpc.resource_name, 'message': '子网创建成功'}


def action_create_security_group(params: Dict[str, Any]) -> Dict[str, Any]:
    """新建安全组"""
    from cmdb.models import Resource

    account = _mock_account()
    sg = Resource.objects.create(
        account=account, provider_type='mock', resource_type='security_group',
        resource_name=params.get('name') or f'sg-{uuid.uuid4().hex[:6]}',
        cloud_resource_id=f'sg-{uuid.uuid4().hex[:12]}',
        region=params.get('region', 'cn-hangzhou'), status='available',
        metadata={'description': params.get('description', '')},
        source=1, source_system='manual', sync_mode='manual',
    )
    _write_change(sg, 'create', after={'description': params.get('description', '')})
    return {'resource_id': sg.id, 'cloud_resource_id': sg.cloud_resource_id,
            'name': sg.resource_name, 'message': '安全组创建成功'}


def action_attach_security_group(params: Dict[str, Any]) -> Dict[str, Any]:
    """实例绑定安全组"""
    instance_id = params.get('instance_id')
    sg_id = params.get('security_group_id')
    if not instance_id or not sg_id:
        raise ValueError('缺少 instance_id / security_group_id')
    _link(instance_id, sg_id, 'attach_sg', 'hard')
    return {'message': '安全组绑定成功', 'instance_id': instance_id, 'security_group_id': sg_id}


def action_allow_network(params: Dict[str, Any]) -> Dict[str, Any]:
    """网络打通：为目标安全组生成放行规则"""
    from cmdb.models import SecurityRule

    sg_id = params.get('security_group_id')
    if not sg_id:
        raise ValueError('缺少 security_group_id')
    rule = SecurityRule.objects.create(
        security_group_id=sg_id,
        direction=params.get('direction', 'inbound'),
        protocol=params.get('protocol', 'tcp'),
        port_range=params.get('port_range', '80'),
        source=params.get('source', '0.0.0.0/0'),
        target=params.get('target', '0.0.0.0/0'),
        priority=params.get('priority', 100),
        action='allow',
        enabled=True,
    )
    return {'rule_id': rule.id, 'message': f'放行规则 {rule.protocol}:{rule.port_range} 已创建'}


def action_init_env(params: Dict[str, Any]) -> Dict[str, Any]:
    """环境初始化（Mock：模拟脚本执行日志）"""
    steps = params.get('init_steps', ['安装依赖', '写入配置', '启动服务'])
    log = '\n'.join(f'[init] {s} ... 完成' for s in steps)
    return {'message': '环境初始化完成', 'log': log}


def action_write_cmdb(params: Dict[str, Any]) -> Dict[str, Any]:
    """数据落库：更新资源归属/元数据（模拟 CMDB 变更）"""
    from cmdb.models import Resource

    resource = Resource.objects.filter(id=params.get('resource_id')).first()
    if not resource:
        raise ValueError('资源不存在')
    before = {'application': resource.application_id}
    if params.get('application_id'):
        resource.application_id = params['application_id']
        resource.save(update_fields=['application', 'updated_at'])
    updates = params.get('updates') or {}
    if updates:
        for k, v in updates.items():
            if hasattr(resource, k):
                setattr(resource, k, v)
        resource.save(update_fields=list(updates.keys()) + ['updated_at'])
    _write_change(resource, 'cmdb_update', before=before,
                  after={'application': resource.application_id})
    return {'resource_id': resource.id, 'message': 'CMDB 数据已更新'}


def action_publish_platform(params: Dict[str, Any]) -> Dict[str, Any]:
    """推送发布平台（Mock：HTTP 回调占位）"""
    target = params.get('publish_target', 'https://deploy.internal/publish')
    return {
        'message': '发布请求已推送',
        'target': target,
        'publish_id': f'pub-{uuid.uuid4().hex[:12]}',
        'status': 'accepted',
    }


# ---------- 注册 ----------

ActionRegistry.register(ActionSpec(
    'create_instance', '申请机器', action_create_instance,
    params_schema={'name': str, 'region': str, 'spec': str},
    rollback=_rollback_resource_create,
))
ActionRegistry.register(ActionSpec('create_subnet', '新建子网', action_create_subnet,
                                   params_schema={'name': str, 'cidr': str}))
ActionRegistry.register(ActionSpec('create_security_group', '新建安全组',
                                   action_create_security_group,
                                   params_schema={'name': str, 'description': str}))
ActionRegistry.register(ActionSpec('attach_security_group', '绑定安全组',
                                   action_attach_security_group,
                                   params_schema={'instance_id': int, 'security_group_id': int}))
ActionRegistry.register(ActionSpec('allow_network', '网络打通', action_allow_network,
                                   params_schema={'security_group_id': int, 'port_range': str}))
ActionRegistry.register(ActionSpec('init_env', '环境初始化', action_init_env,
                                   need_approval=False))
ActionRegistry.register(ActionSpec('write_cmdb', '数据落库', action_write_cmdb,
                                   params_schema={'resource_id': int, 'application_id': int}))
ActionRegistry.register(ActionSpec('publish_platform', '推送发布平台', action_publish_platform,
                                   need_approval=False))
