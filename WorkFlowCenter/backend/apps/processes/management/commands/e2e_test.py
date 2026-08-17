"""
流程端到端测试管理命令

用法:
  python manage.py e2e_test --key server_apply        # 跑单个流程
  python manage.py e2e_test --all                     # 跑全部已发布流程
"""
from django.core.management.base import BaseCommand

from apps.processes.models import ProcessDefinition
from apps.processes.services.e2e import run_e2e


class Command(BaseCommand):
    help = '流程端到端测试：一键跑通完整生命周期并打印每步'

    def add_arguments(self, parser):
        parser.add_argument('--key', type=str, default='', help='流程定义 key')
        parser.add_argument('--all', action='store_true', help='跑全部已发布流程')

    def handle(self, *args, **options):
        keys = []
        if options['all']:
            keys = list(ProcessDefinition.objects.filter(
                status=ProcessDefinition.Status.PUBLISHED,
            ).values_list('key', flat=True))
        elif options['key']:
            keys = [options['key']]
        else:
            self.stderr.write('请指定 --key <key> 或 --all')
            return

        for key in keys:
            self.stdout.write('\n' + '=' * 72)
            self.stdout.write(f'  E2E 测试：{key}')
            self.stdout.write('=' * 72)
            result = run_e2e(definition_key=key)
            if result.get('error'):
                self.stderr.write(f'  错误：{result["error"]}')
                continue
            for s in result['steps']:
                mark = '✓' if s['ok'] else '✕'
                self.stdout.write(
                    f'  [{mark}] step{s["step"]:>2} {s["action"]}'
                    f'  ({s["user"]})\n'
                    f'        {s["api"]}\n'
                    f'        req={s["request"]}\n'
                    f'        resp={s["response"]}'
                    + (f'  [note] {s["note"]}' if s.get('note') else '')
                )
            inst = result['instance']
            self.stdout.write(
                f'  → 实例 {inst["instance_no"]} [{inst["status_display"]}] '
                f'steps={result["summary"]["steps_count"]} '
                f'ok={result["summary"]["ok_count"]} fail={result["summary"]["fail_count"]}'
            )
