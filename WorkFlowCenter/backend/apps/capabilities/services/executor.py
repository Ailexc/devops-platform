"""
能力执行器

提供同步和异步两种执行模式，以及 Mock 客户端用于开发测试。
"""
import logging
from abc import ABC, abstractmethod
from typing import Any

from django.utils import timezone

from apps.capabilities.models import Capability, TaskJob

logger = logging.getLogger(__name__)


def _append_job_log(job, level, message):
    logs = list(job.logs or [])
    logs.append({
        'ts': timezone.now().isoformat(timespec='seconds'),
        'level': level,
        'message': message,
    })
    job.logs = logs
    job.save(update_fields=['logs', 'updated_at'])


class BaseJobPlatformClient(ABC):
    """Job 平台客户端基类"""

    @abstractmethod
    def execute(self, endpoint: str, input_data: dict) -> dict:
        """执行能力，返回输出数据"""
        ...


class HttpJobPlatformClient(BaseJobPlatformClient):
    """真实 HTTP 客户端：通过 HTTP 调用外部能力"""

    def execute(self, endpoint: str, input_data: dict) -> dict:
        import requests
        try:
            response = requests.post(endpoint, json=input_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'HTTP 调用失败: endpoint={endpoint}, error={e}')
            raise


class MockJobPlatformClient(BaseJobPlatformClient):
    """
    Mock 客户端：模拟各种内置能力的执行结果。
    用于开发和测试环境。
    """

    _MOCK_IMPLEMENTATIONS = {
        'cmdb_create_host': lambda data: {
            'host_id': 'mock-host-001',
            'hostname': data.get('hostname', 'mock-host'),
            'ip': '10.0.0.100',
            'status': 'active',
        },
        'dns_add_record': lambda data: {
            'record_id': 'mock-dns-001',
            'domain': data.get('domain', 'example.com'),
            'record_type': data.get('record_type', 'A'),
            'record_value': data.get('record_value', '10.0.0.1'),
            'status': 'created',
        },
        'mail_send': lambda data: {
            'message_id': 'mock-mail-001',
            'to': data.get('to', []),
            'subject': data.get('subject', ''),
            'status': 'sent',
        },
        'external_approve': lambda data: {
            'approval_id': 'mock-approval-001',
            'status': 'approved',
            'approver': 'mock-system',
            'opinion': '已自动审批',
        },
    }

    def execute(self, endpoint: str, input_data: dict) -> dict:
        """执行 Mock 能力"""
        capability_code = input_data.pop('_capability_code', '')
        # 兼容点号与下划线两种编码风格（cmdb.create_host / cmdb_create_host）
        handler = self._MOCK_IMPLEMENTATIONS.get(capability_code)
        if handler is None:
            handler = self._MOCK_IMPLEMENTATIONS.get(capability_code.replace('.', '_'))
        if handler:
            result = handler(input_data)
            logger.info(f'Mock 执行成功: capability={capability_code}, result={result}')
            return result
        logger.warning(f'Mock 执行: 未知能力 {capability_code}，返回空结果')
        return {'status': 'mock_executed', 'capability': capability_code}


class CapabilityExecutor:
    """
    能力执行器：协调 TaskJob 生命周期，调用合适的客户端执行能力。
    """

    def __init__(self, client=None):
        self.client = client or MockJobPlatformClient()

    def execute_capability(self, job_id: str, capability_code: str = '', input_data: dict = None) -> dict:
        """
        执行指定能力。

        1. 根据 job_id 查询 TaskJob
        2. 更新状态为 running
        3. 调用客户端执行
        4. 更新状态为 succeeded/failed
        5. 返回输出数据
        """
        try:
            job = TaskJob.objects.select_related('capability', 'instance', 'task').get(job_id=job_id)
        except TaskJob.DoesNotExist:
            logger.error(f'TaskJob 不存在: {job_id}')
            return {'error': f'Job {job_id} not found'}

        capability = job.capability

        # 标记开始执行
        job.status = TaskJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at', 'updated_at'])
        _append_job_log(job, 'info', f'执行器已接管，调用能力「{capability.code}」')

        try:
            # 将 capability_code 注入 input_data 供 Mock 使用
            exec_input = {**job.input_data, '_capability_code': capability.code}
            endpoint = capability.endpoint or ''

            _append_job_log(job, 'debug', f'请求参数：{exec_input}')
            output = self.client.execute(endpoint, exec_input)
            # 移除内部字段
            exec_input.pop('_capability_code', None)

            # 标记成功
            job.status = TaskJob.Status.SUCCEEDED
            job.output_data = output
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'output_data', 'completed_at', 'updated_at'])
            _append_job_log(job, 'info', f'能力执行成功，返回：{output}')

            logger.info(f'能力执行成功: job={job_id}, capability={capability.code}')
            return output

        except Exception as e:
            # 标记失败
            job.status = TaskJob.Status.FAILED
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
            _append_job_log(job, 'error', f'能力执行失败：{e}')

            logger.error(f'能力执行失败: job={job_id}, capability={capability.code}, error={e}')
            return {'error': str(e)}


# 默认使用 Mock 客户端
default_executor = CapabilityExecutor()
