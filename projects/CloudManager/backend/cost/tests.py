"""
成本模块测试 —— 规则引擎 + API 冒烟测试。

覆盖：
- 规则引擎：idle / downsize 匹配、节省估算、执行日志
- 全量检测：报告生成 + 汇总 + 层级树
- API：规则 CRUD、单规则执行、报告导出、总览
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.test import APIClient

from cmdb.models import CloudAccount, Resource
from cost.models import (
    OptimizationRule, OptimizationSuggestion, OptimizationReport, RuleExecutionLog,
)


def create_test_data():
    """创建最小测试数据：1 账号 + 3 资源"""
    account = CloudAccount.objects.create(
        account_name='测试账号', provider_type='mock', status=1, sync_status=2,
    )
    stopped = Resource.objects.create(
        account=account, provider_type='mock', resource_type='instance',
        resource_name='web-stopped-01', cloud_resource_id='i-stop01',
        region='cn-hangzhou', status='stopped', spec='ecs.g6.xlarge',
        metadata={'cpu': 4, 'memory_gb': 8},
    )
    running_low = Resource.objects.create(
        account=account, provider_type='mock', resource_type='instance',
        resource_name='web-idle-01', cloud_resource_id='i-idle01',
        region='cn-hangzhou', status='running', spec='ecs.g6.2xlarge',
        metadata={'cpu': 8, 'memory_gb': 16, 'avg_cpu_7d': 3.2, 'avg_mem_7d': 12.0},
    )
    running_busy = Resource.objects.create(
        account=account, provider_type='mock', resource_type='instance',
        resource_name='web-busy-01', cloud_resource_id='i-busy01',
        region='cn-hangzhou', status='running', spec='ecs.g6.xlarge',
        metadata={'cpu': 8, 'memory_gb': 16, 'avg_cpu_7d': 55.0, 'avg_mem_7d': 60.0},
    )
    return account, stopped, running_low, running_busy


class RuleEngineTests(APITestCase):
    def setUp(self):
        self.account, self.stopped, self.low, self.busy = create_test_data()

    def _make_rule(self, **kwargs):
        defaults = {
            'name': '测试规则', 'rule_type': 'idle', 'severity': 'high',
            'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
            'conditions': {'resource_type': 'instance', 'status': 'stopped'},
            'title_template': '闲置主机 {resource_name} 建议下架',
            'saving_config': {'type': 'spec_ratio', 'percent': 100},
        }
        defaults.update(kwargs)
        return OptimizationRule.objects.create(**defaults)

    def test_idle_rule_matches_stopped(self):
        from cost.engine import execute_rule
        rule = self._make_rule(name='闲置检测')
        result = execute_rule(rule, operator='tester')
        # 只匹配 stopped 的那台
        self.assertEqual(result['matched'], 1)
        self.assertEqual(result['created'], 1)
        sug = OptimizationSuggestion.objects.get(rule=rule)
        self.assertEqual(sug.resource, self.stopped)
        self.assertEqual(sug.region, 'cn-hangzhou')
        self.assertEqual(sug.provider_type, 'mock')
        # 执行日志
        log = RuleExecutionLog.objects.get(rule=rule)
        self.assertEqual(log.matched_count, 1)
        self.assertEqual(log.created_count, 1)

    def test_downsize_rule_reads_metadata(self):
        from cost.engine import execute_rule
        rule = self._make_rule(
            name='降配检测', rule_type='downsize', severity='medium',
            conditions={'resource_type': 'instance', 'status': 'running',
                        'metrics': {'avg_cpu_7d': {'lt': 5}}},
            saving_config={'type': 'spec_ratio', 'percent': 40},
        )
        result = execute_rule(rule, operator='tester')
        # 只匹配低利用率那台（avg_cpu_7d=3.2），不匹配 busy(55)
        self.assertEqual(result['matched'], 1)
        sug = OptimizationSuggestion.objects.get(rule=rule)
        self.assertEqual(sug.resource, self.low)
        self.assertGreater(float(sug.estimated_saving), 0)

    def test_run_all_generates_report(self):
        from cost.engine import run_all
        rule = self._make_rule(name='闲置检测')
        report = run_all(rules=[rule], trigger='manual', operator='tester')
        self.assertEqual(report.summary['total_rules'], 1)
        self.assertEqual(report.summary['total_matched'], 1)
        self.assertIn('mock', report.tree_snapshot)  # tree_snapshot 为云级树
        self.assertEqual(len(report.items_snapshot), 1)
        # 建议关联到报告
        sug = OptimizationSuggestion.objects.get(rule=rule)
        self.assertEqual(sug.report, report)


class CostApiTests(APITestCase):
    def setUp(self):
        self.account, *_ = create_test_data()
        self.user, _ = get_user_model().objects.get_or_create(username='api_tester')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_rules_crud_and_run(self):
        # 创建规则
        resp = self.client.post('/api/cost/rules/', {
            'name': 'API闲置检测', 'rule_type': 'idle', 'severity': 'high',
            'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
            'conditions': {'resource_type': 'instance', 'status': 'stopped'},
            'title_template': '闲置 {resource_name}', 'saving_config': {'type': 'fixed', 'amount': 100},
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        rule_id = resp.json()['id']

        # 单规则执行
        resp = self.client.post(f'/api/cost/rules/{rule_id}/run/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()['matched'], 1)

        # 启停
        resp = self.client.patch(f'/api/cost/rules/{rule_id}/', {'is_enabled': False}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['is_enabled'])

    def test_run_all_and_reports(self):
        OptimizationRule.objects.create(
            name='闲置检测', rule_type='idle', severity='high',
            scope={'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
            conditions={'resource_type': 'instance', 'status': 'stopped'},
            title_template='闲置 {resource_name}',
        )
        resp = self.client.post('/api/cost/rules/run_all/')
        self.assertEqual(resp.status_code, 200)
        report_id = resp.json()['report']['id']

        # 报告详情
        resp = self.client.get(f'/api/cost/reports/{report_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['id'], report_id)

        # 导出 CSV
        resp = self.client.get(f'/api/cost/reports/{report_id}/export/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])
        self.assertTrue(resp.content.startswith(b'\xef\xbb\xbf'))  # BOM

        # 总览
        resp = self.client.get('/api/cost/overview/summary/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('stats', resp.json())
        self.assertGreaterEqual(resp.json()['stats']['total'], 1)
