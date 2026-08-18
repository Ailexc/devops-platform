"""
初始化默认优化规则 —— 对应 V5 Demo 的规则集。

用法: python manage.py seed_rules
幂等：已存在的同名规则不会重复创建。
"""
from django.core.management.base import BaseCommand

from cost.models import OptimizationRule


DEFAULT_RULES = [
    {
        'name': '闲置主机检测',
        'rule_type': 'idle', 'severity': 'high', 'priority': 10,
        'description': '检测已停止的云主机，建议下架释放',
        'scope': {'cloud': '', 'account': '', 'region': 'cn-hangzhou', 'resource_type': 'instance'},
        'conditions': {'resource_type': 'instance', 'status': 'stopped'},
        'title_template': '闲置主机 {resource_name} 建议下架',
        'saving_config': {'type': 'spec_ratio', 'percent': 100},
    },
    {
        'name': '低利用率降配',
        'rule_type': 'downsize', 'severity': 'medium', 'priority': 8,
        'description': '运行中但 CPU 平均利用率 < 5% 的主机，建议降配',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
        'conditions': {'resource_type': 'instance', 'status': 'running',
                       'metrics': {'avg_cpu_7d': {'lt': 5}}},
        'title_template': '主机 {resource_name} CPU 利用率过低，建议降配',
        'saving_config': {'type': 'spec_ratio', 'percent': 40},
    },
    {
        'name': '未挂载云硬盘',
        'rule_type': 'unused', 'severity': 'low', 'priority': 6,
        'description': '状态为 available 的云硬盘，建议释放',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'disk'},
        'conditions': {'resource_type': 'disk', 'status': 'available'},
        'title_template': '云硬盘 {resource_name} 未挂载，建议释放',
        'saving_config': {'type': 'fixed', 'amount': 50},
    },
    {
        'name': '闲置实例检测',
        'rule_type': 'idle', 'severity': 'high', 'priority': 9,
        'description': '检测已停止的实例，建议下架释放',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
        'conditions': {'resource_type': 'instance', 'status': 'stopped'},
        'title_template': '闲置实例 {resource_name} 建议下架',
        'saving_config': {'type': 'spec_ratio', 'percent': 100},
    },
    {
        'name': '低利用率实例',
        'rule_type': 'downsize', 'severity': 'medium', 'priority': 7,
        'description': '实例 CPU 平均利用率 < 5%，建议降配',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
        'conditions': {'resource_type': 'instance', 'status': 'running',
                       'metrics': {'avg_cpu_7d': {'lt': 5}}},
        'title_template': '实例 {resource_name} 建议降配',
        'saving_config': {'type': 'spec_ratio', 'percent': 40},
    },
    {
        'name': '部门预算超支',
        'rule_type': 'budget', 'severity': 'high', 'priority': 5,
        'description': '部门月度预算使用超过 80% 时触发告警',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': ''},
        'conditions': {'budget_usage_percent': {'gte': 80}},
        'title_template': '{department_name} 部门预算已使用 {usage_percent}%',
        'saving_config': {'type': 'none'},
    },
    {
        'name': '费用环比异常',
        'rule_type': 'trend', 'severity': 'medium', 'priority': 4,
        'description': '检测月度费用环比增长超过 20% 的账号',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': ''},
        'conditions': {'threshold_percent': 20, 'direction': 'increase'},
        'title_template': '{account_name} 费用环比增长 {change_percent}%',
        'saving_config': {'type': 'none'},
    },
    {
        'name': '按量转包年优化',
        'rule_type': 'reserved', 'severity': 'medium', 'priority': 6,
        'description': '按量计费主机推荐转包年/预留，节省约 30%',
        'scope': {'cloud': '', 'account': '', 'region': '', 'resource_type': 'instance'},
        'conditions': {'billing_mode': 'pay_as_you_go'},
        'title_template': '主机 {resource_name} 建议转包年节省成本',
        'saving_config': {'type': 'spec_ratio', 'percent': 30},
    },
]


class Command(BaseCommand):
    help = '初始化默认优化规则（幂等）'

    def handle(self, *args, **options):
        created = 0
        for spec in DEFAULT_RULES:
            obj, was_created = OptimizationRule.objects.get_or_create(
                name=spec['name'],
                defaults={k: v for k, v in spec.items() if k != 'name'},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  + 创建规则: {spec["name"]}'))
            else:
                self.stdout.write(f'  = 已存在: {spec["name"]}')
        self.stdout.write(self.style.SUCCESS(f'完成：新增 {created} 条规则，共 {OptimizationRule.objects.count()} 条'))
