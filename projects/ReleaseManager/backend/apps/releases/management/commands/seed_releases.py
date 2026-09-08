import datetime
import random
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.applications.models import Application, AppEnvConfig
from apps.infrastructures.models import Environment
from apps.releases.models import Release, ReleaseTask


class Command(BaseCommand):
    help = '生成发布记录种子数据'

    def handle(self, *args, **options):
        self._seed_releases()
        self.stdout.write(self.style.SUCCESS('发布记录种子数据生成完成!'))

    def _generate_release_no(self, date_offset=0):
        today = datetime.date.today() - datetime.timedelta(days=date_offset)
        suffix = f'{random.randint(0, 9999):04d}'
        return f'REL-{today.strftime("%Y%m%d")}-{suffix}'

    def _seed_releases(self):
        apps = Application.objects.all()
        users = list(User.objects.all())
        envs = list(Environment.objects.all())

        versions = ['v1.0.0', 'v1.1.0', 'v1.2.0', 'v2.0.0', 'v2.1.0', 'v2.2.0', 'v2.3.0', 'v3.0.0']
        commit_ids = ['a1b2c3d', 'e4f5g6h', 'i7j8k9l', 'm0n1o2p', 'q3r4s5t', 'u6v7w8x', 'y9z0a1b', 'c2d3e4f']
        commit_msgs = [
            'feat: add user auth module',
            'fix: resolve payment timeout issue',
            'refactor: optimize order query performance',
            'feat: add notification service',
            'fix: fix memory leak in worker',
            'chore: update dependencies',
            'feat: add rate limiting',
            'fix: correct typo in config',
        ]

        statuses = ['pending', 'approved', 'completed', 'completed', 'completed',
                     'failed', 'rolled_back', 'completed', 'completed', 'cancelled']
        release_modes = ['regular', 'regular', 'regular', 'incremental', 'compensation',
                         'quick', 'rollback', 'regular', 'regular', 'regular']
        deploy_strategies = ['rolling', 'rolling', 'rolling', 'rolling',
                             'blue_green', 'canary', 'rolling', 'rolling', 'rolling', 'rolling']

        created = 0
        for app in apps:
            # 每个应用在不同环境生成 3-8 条发布记录
            app_env_configs = AppEnvConfig.objects.filter(application=app)
            for env_config in app_env_configs:
                num_releases = random.randint(3, 8)
                for i in range(num_releases):
                    release_date_offset = (num_releases - i) * random.randint(1, 3)
                    status = random.choice(statuses)
                    mode = random.choice(release_modes)
                    strategy = random.choice(deploy_strategies)

                    # 回滚模式需要特殊处理
                    if mode == 'rollback':
                        status = 'completed'
                        strategy = 'rolling'

                    release = Release.objects.create(
                        release_no=self._generate_release_no(release_date_offset),
                        title=f'{app.name} {versions[i % len(versions)]} 发布',
                        description=f'发布 {app.name} 的 {versions[i % len(versions)]} 版本到 {env_config.environment.name}',
                        application=app,
                        env_config=env_config,
                        environment=env_config.environment,
                        version=versions[i % len(versions)],
                        commit_id=commit_ids[i % len(commit_ids)],
                        commit_message=commit_msgs[i % len(commit_msgs)],
                        image_tag=f'{app.code}:{versions[i % len(versions)]}',
                        status=status,
                        release_mode=mode,
                        deploy_strategy=strategy,
                        deploy_mode=app.deploy_mode or 'k8s',
                        canary_percent=random.choice([10, 20, 30]) if strategy == 'canary' else 10,
                        creator=random.choice(users),
                    )

                    # 创建 11 个阶段任务
                    tasks = []
                    for stage, _ in ReleaseTask.STAGES:
                        if status == 'completed':
                            task_status = 'success'
                        elif status == 'failed':
                            task_status = random.choice(['success', 'success', 'failed'])
                        elif status == 'running':
                            task_status = random.choice(['success', 'success', 'running', 'pending'])
                        elif status == 'pending' or status == 'approved':
                            task_status = 'pending'
                        elif status == 'cancelled':
                            task_status = random.choice(['success', 'skipped', 'skipped'])
                        elif status == 'rolled_back':
                            task_status = random.choice(['success', 'success', 'skipped'])
                        else:
                            task_status = 'pending'

                        tasks.append(ReleaseTask(
                            release=release,
                            stage=stage,
                            status=task_status,
                            operator=release.creator if task_status in ('success', 'failed') else None,
                            message=f'[Demo] 阶段 {stage} 执行{"成功" if task_status == "success" else "跳过"}' if task_status != 'pending' else '',
                        ))
                    ReleaseTask.objects.bulk_create(tasks)
                    created += 1

        self.stdout.write(f'  共创建了 {created} 条发布记录')