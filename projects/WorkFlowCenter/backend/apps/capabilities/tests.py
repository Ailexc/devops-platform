from django.test import TestCase
from .models import Capability, TaskJob
from .services.executor import CapabilityExecutor, MockJobPlatformClient


class CapabilityModelTest(TestCase):
    """能力模型测试"""

    def test_create_capability(self):
        cap = Capability.objects.create(
            code='mail_send',
            name='发送邮件',
            execute_mode='async',
            input_schema={'type': 'object', 'properties': {'to': {'type': 'array'}}},
        )
        self.assertEqual(cap.code, 'mail_send')
        self.assertTrue(cap.is_active)


class MockExecutorTest(TestCase):
    """Mock 执行器测试"""

    def test_mail_send(self):
        executor = CapabilityExecutor(client=MockJobPlatformClient())
        result = executor.execute_capability(
            job_id='test-job-001',
            capability_code='mail_send',
            input_data={'to': ['test@example.com'], 'subject': 'Hello'},
        )
        self.assertEqual(result['status'], 'sent')
        self.assertIn('message_id', result)

    def test_cmdb_create_host(self):
        executor = CapabilityExecutor(client=MockJobPlatformClient())
        result = executor.execute_capability(
            job_id='test-job-002',
            capability_code='cmdb_create_host',
            input_data={'hostname': 'web-01'},
        )
        self.assertIn('host_id', result)
