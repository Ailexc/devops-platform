"""
云适配层核心接口定义
各 Provider（AWS / 阿里云 / Mock）实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid
import time
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskHandle:
    """异步任务句柄"""
    task_id: str
    status: str = 'pending'  # pending / running / success / failed
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ''


@dataclass
class ResourceVO:
    """统一资源视图对象"""
    resource_type: str
    resource_name: str
    cloud_resource_id: str
    region: str
    status: str
    spec: str = ''
    zone: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


class CloudProvider(ABC):
    """云适配器抽象基类"""

    @abstractmethod
    def get_provider_type(self) -> str:
        """返回云类型标识: aws / aliyun / mock"""
        pass

    @abstractmethod
    def list_instances(self, region: str) -> List[ResourceVO]:
        """查询主机列表"""
        pass

    @abstractmethod
    def list_vpcs(self, region: str) -> List[ResourceVO]:
        """查询 VPC 列表"""
        pass

    @abstractmethod
    def list_security_groups(self, region: str) -> List[ResourceVO]:
        """查询安全组列表"""
        pass

    @abstractmethod
    def start_instance(self, instance_id: str) -> TaskHandle:
        """启动主机（异步）"""
        pass

    @abstractmethod
    def stop_instance(self, instance_id: str) -> TaskHandle:
        """停止主机（异步）"""
        pass

    @abstractmethod
    def resize_instance(self, instance_id: str, new_spec: str) -> TaskHandle:
        """变更规格（异步）"""
        pass

    @abstractmethod
    def create_instance(self, request: Dict[str, Any]) -> TaskHandle:
        """创建主机（异步）"""
        pass

    @abstractmethod
    def release_instance(self, instance_id: str) -> TaskHandle:
        """释放主机（异步）"""
        pass

    @abstractmethod
    def query_task(self, task_id: str) -> TaskHandle:
        """查询任务状态"""
        pass


class MockProvider(CloudProvider):
    """
    Mock 云 Provider
    - 内置模拟资源数据
    - 模拟异步任务（延迟 + 状态推进）
    - 支持失败注入
    """

    # 模拟地域
    REGIONS = ['cn-hangzhou', 'cn-shanghai', 'cn-beijing', 'us-east-1']
    # 模拟规格
    SPECS = ['t3.medium', 't3.large', 't3.xlarge', 'ecs.g6.large', 'ecs.g6.xlarge', 'ecs.g6.2xlarge']
    # 模拟可用区
    ZONES = ['a', 'b', 'c']

    def __init__(self, fail_rate: float = 0.0):
        """
        初始化 Mock Provider
        :param fail_rate: 失败注入概率 (0.0 ~ 1.0)
        """
        self.fail_rate = fail_rate
        # 内置模拟资源数据
        self._mock_instances: List[Dict[str, Any]] = []
        self._mock_vpcs: List[Dict[str, Any]] = []
        self._mock_sgs: List[Dict[str, Any]] = []
        self._mock_subnets: List[Dict[str, Any]] = []
        self._mock_disks: List[Dict[str, Any]] = []
        self._mock_lbs: List[Dict[str, Any]] = []
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._init_mock_data()

    def _init_mock_data(self):
        """生成初始模拟数据"""
        prefixes = ['web', 'api', 'db', 'cache', 'worker', 'gateway']
        statuses = ['running', 'stopped', 'running', 'running', 'stopped']

        # 生成主机
        for i in range(20):
            prefix = random.choice(prefixes)
            region = random.choice(self.REGIONS)
            self._mock_instances.append({
                'resource_type': 'instance',
                'resource_name': f'{prefix}-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'i-{uuid.uuid4().hex[:12]}',
                'region': region,
                'zone': f'{region}{random.choice(self.ZONES)}',
                'status': random.choice(statuses),
                'spec': random.choice(self.SPECS),
                'metadata': {
                    'cpu': random.choice([2, 4, 8, 16]),
                    'memory_gb': random.choice([4, 8, 16, 32]),
                    'os': random.choice(['ubuntu-22.04', 'centos-7.9', 'windows-2022']),
                    'private_ip': f'10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}',
                    'public_ip': f'47.{random.randint(100,255)}.{random.randint(0,255)}.{random.randint(1,254)}',
                }
            })

        # 生成 VPC
        for i in range(5):
            region = random.choice(self.REGIONS)
            self._mock_vpcs.append({
                'resource_type': 'vpc',
                'resource_name': f'vpc-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'vpc-{uuid.uuid4().hex[:12]}',
                'region': region,
                'status': 'available',
                'metadata': {
                    'cidr_block': f'10.{i}.0.0/16',
                    'is_default': i == 0,
                }
            })

        # 生成安全组
        for i in range(8):
            region = random.choice(self.REGIONS)
            self._mock_sgs.append({
                'resource_type': 'security_group',
                'resource_name': f'sg-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'sg-{uuid.uuid4().hex[:12]}',
                'region': region,
                'status': 'available',
                'metadata': {
                    'description': f'Mock security group {i+1}',
                    'inbound_rules': random.randint(3, 10),
                    'outbound_rules': random.randint(1, 5),
                }
            })

        # 生成子网
        for i in range(8):
            region = random.choice(self.REGIONS)
            self._mock_subnets.append({
                'resource_type': 'subnet',
                'resource_name': f'subnet-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'subnet-{uuid.uuid4().hex[:12]}',
                'region': region,
                'zone': f'{region}{random.choice(self.ZONES)}',
                'status': 'available',
                'metadata': {
                    'cidr_block': f'10.{random.randint(0,10)}.{i}.0/24',
                    'available_ips': random.randint(50, 200),
                }
            })

        # 生成云硬盘
        disk_prefixes = ['data', 'log', 'backup', 'temp']
        disk_statuses = ['in-use', 'available', 'available', 'in-use']
        for i in range(12):
            region = random.choice(self.REGIONS)
            prefix = random.choice(disk_prefixes)
            status = random.choice(disk_statuses)
            self._mock_disks.append({
                'resource_type': 'disk',
                'resource_name': f'{prefix}-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'disk-{uuid.uuid4().hex[:12]}',
                'region': region,
                'status': status,
                'spec': f'{random.choice([20, 50, 100, 200, 500])}GB',
                'metadata': {
                    'disk_type': random.choice(['cloud_ssd', 'cloud_efficiency']),
                    'size_gb': random.choice([20, 50, 100, 200, 500]),
                    'iops': random.randint(1000, 10000),
                }
            })

        # 生成负载均衡
        lb_statuses = ['active', 'active', 'inactive']
        for i in range(6):
            region = random.choice(self.REGIONS)
            self._mock_lbs.append({
                'resource_type': 'load_balancer',
                'resource_name': f'lb-{region[:2]}-{i+1:03d}',
                'cloud_resource_id': f'lb-{uuid.uuid4().hex[:12]}',
                'region': region,
                'status': random.choice(lb_statuses),
                'spec': random.choice(['slb.s1.small', 'slb.s2.medium', 'slb.c1.large']),
                'metadata': {
                    'type': random.choice(['internet', 'internal']),
                    'listeners': random.randint(2, 8),
                    'backend_servers': random.randint(2, 10),
                    'bandwidth': random.choice([10, 50, 100, 200]),
                    'vip': f'47.{random.randint(100,255)}.{random.randint(0,255)}.{random.randint(1,254)}',
                }
            })

    def get_provider_type(self) -> str:
        return 'mock'

    def list_instances(self, region: str) -> List[ResourceVO]:
        items = [i for i in self._mock_instances if i['region'] == region]
        return [ResourceVO(**item) for item in items]

    def list_vpcs(self, region: str) -> List[ResourceVO]:
        items = [v for v in self._mock_vpcs if v['region'] == region]
        return [ResourceVO(**item) for item in items]

    def list_security_groups(self, region: str) -> List[ResourceVO]:
        items = [s for s in self._mock_sgs if s['region'] == region]
        return [ResourceVO(**item) for item in items]

    def list_subnets(self, region: str) -> List[ResourceVO]:
        items = [s for s in self._mock_subnets if s['region'] == region]
        return [ResourceVO(**item) for item in items]

    def list_disks(self, region: str) -> List[ResourceVO]:
        items = [d for d in self._mock_disks if d['region'] == region]
        return [ResourceVO(**item) for item in items]

    def list_load_balancers(self, region: str) -> List[ResourceVO]:
        items = [lb for lb in self._mock_lbs if lb['region'] == region]
        return [ResourceVO(**item) for item in items]

    def _should_fail(self) -> bool:
        return random.random() < self.fail_rate

    def _create_task(self, task_type: str, extra: Dict = None) -> TaskHandle:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            'task_id': task_id,
            'status': 'running',
            'task_type': task_type,
            'created_at': time.time(),
            'extra': extra or {},
        }
        return TaskHandle(task_id=task_id, status='running')

    def start_instance(self, instance_id: str) -> TaskHandle:
        handle = self._create_task('start_instance', {'instance_id': instance_id})
        # 更新模拟数据中的状态
        for inst in self._mock_instances:
            if inst['cloud_resource_id'] == instance_id:
                inst['status'] = 'running'
                break
        return handle

    def stop_instance(self, instance_id: str) -> TaskHandle:
        handle = self._create_task('stop_instance', {'instance_id': instance_id})
        for inst in self._mock_instances:
            if inst['cloud_resource_id'] == instance_id:
                inst['status'] = 'stopped'
                break
        return handle

    def resize_instance(self, instance_id: str, new_spec: str) -> TaskHandle:
        handle = self._create_task('resize_instance', {
            'instance_id': instance_id, 'new_spec': new_spec
        })
        for inst in self._mock_instances:
            if inst['cloud_resource_id'] == instance_id:
                inst['spec'] = new_spec
                break
        return handle

    def create_instance(self, request: Dict[str, Any]) -> TaskHandle:
        new_id = f'i-{uuid.uuid4().hex[:12]}'
        region = request.get('region', random.choice(self.REGIONS))
        spec = request.get('spec', random.choice(self.SPECS))
        name = request.get('name', f'mock-{uuid.uuid4().hex[:6]}')

        instance_data = {
            'resource_type': 'instance',
            'resource_name': name,
            'cloud_resource_id': new_id,
            'region': region,
            'zone': f'{region}{random.choice(self.ZONES)}',
            'status': 'pending',
            'spec': spec,
            'metadata': {
                'cpu': request.get('cpu', 4),
                'memory_gb': request.get('memory_gb', 8),
                'os': request.get('os', 'ubuntu-22.04'),
                'private_ip': f'10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}',
                'public_ip': f'47.{random.randint(100,255)}.{random.randint(0,255)}.{random.randint(1,254)}',
            }
        }
        self._mock_instances.append(instance_data)

        handle = self._create_task('create_instance', {
            'instance_id': new_id,
            'instance_data': instance_data,
        })
        handle.result = {'instance_id': new_id, 'instance_data': instance_data}
        return handle

    def release_instance(self, instance_id: str) -> TaskHandle:
        handle = self._create_task('release_instance', {'instance_id': instance_id})
        self._mock_instances = [
            i for i in self._mock_instances if i['cloud_resource_id'] != instance_id
        ]
        return handle

    def query_task(self, task_id: str) -> TaskHandle:
        task = self._tasks.get(task_id)
        if not task:
            return TaskHandle(task_id=task_id, status='failed', error='Task not found')

        elapsed = time.time() - task['created_at']
        # 模拟 2-5 秒后完成
        if elapsed > random.uniform(2, 5):
            if self._should_fail():
                task['status'] = 'failed'
            else:
                task['status'] = 'success'

        return TaskHandle(
            task_id=task_id,
            status=task['status'],
            result=task.get('extra', {}),
            error='Mock failure injection' if task['status'] == 'failed' else ''
        )


# Provider 注册表
PROVIDERS = {
    'mock': MockProvider,
}


def get_provider(provider_type: str, **kwargs) -> CloudProvider:
    """获取 Provider 实例"""
    provider_cls = PROVIDERS.get(provider_type)
    if not provider_cls:
        raise ValueError(f'Unknown provider type: {provider_type}')
    return provider_cls(**kwargs)
