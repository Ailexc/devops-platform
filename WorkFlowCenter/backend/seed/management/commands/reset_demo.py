"""
一键重置数据库到 Demo 最佳状态（删除重建）。

用法:
  python manage.py reset_demo
  # Docker 环境:
  docker compose exec api python manage.py reset_demo

行为（无论当前数据库处于什么状态，执行后都会还原到 Demo 最佳状态）:
  1. migrate       -- 确保表结构就绪（幂等，新库/已迁移库均安全）
  2. flush         -- 清空所有数据表并重置自增序列（删除重建）
  3. loaddata      -- 恢复完整 Demo 数据快照 (seed/fixtures/demo_full.json)
  4. seed_demo_data -- 补齐演示数据（待办/已办/抄送，幂等）

说明:
  - demo_full.json 由 `python manage.py dumpdata --natural-primary --natural-foreign
    -e admin.logentry -e sessions.session` 在"Demo 最佳状态"下生成，
    包含: 部门/用户/角色/权限/能力/工单类型/发起程序/流程定义/预置流程实例/
    节点任务/审批记录/任务作业/FSM 状态日志 等全部业务数据。
  - 数据文件更新方式: 调整好数据库后重新执行上面的 dumpdata 命令覆盖该文件。
  - seed_demo_data 负责补齐「待办/已办/抄送」演示数据（以 admin 为主的
    管理员自己提交、自己审批场景），保证演示时各列表都有内容。
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '一键重置数据库到 Demo 最佳状态（删除重建，还原 dumpdata 快照）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-migrate',
            action='store_true',
            help='跳过 migrate（默认会先执行幂等的 migrate 确保表结构就绪）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('⚠️  即将删除并重建数据库为 Demo 最佳状态'))

        # 1. 确保表结构就绪（幂等，全新库/已迁移库均安全）
        if not options['no_migrate']:
            self.stdout.write('[1/3] migrate 确保表结构...')
            call_command('migrate', interactive=False, verbosity=0)

        # 2. 清空所有数据表并重置自增序列（删除重建核心）
        self.stdout.write('[2/3] flush 清空所有数据...')
        call_command('flush', interactive=False, verbosity=0)

        # 3. 恢复完整 Demo 快照
        self.stdout.write('[3/4] loaddata 恢复 Demo 快照 (seed/fixtures/demo_full.json)...')
        call_command('loaddata', 'demo_full', verbosity=0)

        # 4. 补齐演示数据（待办/已办/抄送，幂等）
        self.stdout.write('[4/4] seed_demo_data 补齐待办/已办/抄送演示数据...')
        call_command('seed_demo_data', verbosity=0)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ 数据库已还原到 Demo 最佳状态！'))
        self.stdout.write('  默认用户: admin/admin123 (管理员)')
        self.stdout.write('           xiaoming/xiaohong/xiaohuang/xiaoli/'
                          'xiaowang/xiaozhang/xiaozhao (均 user123)')
        self.stdout.write('  流程实例: SRV-2026-001/002/003 (预置) + WI-2026* (演示运行记录)')
        self.stdout.write('  演示数据: 待办/已办/抄送均已补齐（admin 视角可直接演示）')
