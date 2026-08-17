from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.organizations.models import BusinessLine, Group
from apps.authz.models import Role, RoleDataRule, SubjectMembership, EnvironmentApprovalConfig, ApprovalFlowTemplate, PermissionRequest
from apps.infrastructures.models import Environment, Cluster, K8sNamespace
from apps.applications.models import Application, AppEnvConfig, ImageRegistry
from apps.authz.models import ReleaseApprovalConfig, AppChangeApprovalConfig
from apps.artifacts.models import ArtifactRepository


class Command(BaseCommand):
    help = '初始化种子数据（v4 权限模型）'

    def handle(self, *args, **options):
        self._create_users()
        self._create_business_lines()
        self._create_groups()
        self._create_group_roles()
        self._create_user_roles()
        self._create_memberships()
        self._create_environments()
        self._create_clusters()
        self._create_apps()
        self._create_approval_flow_templates()
        self._create_approval_configs()
        self._create_release_approval_configs()
        self._create_app_change_approval_config()
        self._create_group_default_rules()
        self._ensure_demo_app_permissions()
        self._create_user_custom_rules()
        self._rebuild_all_caches()
        self._create_artifact_repos()
        self._create_demo_artifacts()
        self._create_image_registry()
        self._create_permission_requests()
        self.stdout.write(self.style.SUCCESS('种子数据初始化完成!'))

    # ─── 用户 ─────────────────────────────────────────────────

    def _create_users(self):
        users_data = [
            ('zhangsan', '张三', 'zhangsan@demo.com'),
            ('lisi', '李四', 'lisi@demo.com'),
            ('wangwu', '王五', 'wangwu@demo.com'),
            ('zhaoliu', '赵六', 'zhaoliu@demo.com'),
            ('qianqi', '钱七', 'qianqi@demo.com'),
            ('sunba', '孙八', 'sunba@demo.com'),
            ('zhoujiu', '周九', 'zhoujiu@demo.com'),
            ('xiaoliu', '小刘', 'xiaoliu@demo.com'),
            ('xiaochen', '小陈', 'xiaochen@demo.com'),
            ('dawei', '大伟', 'dawei@demo.com'),
            ('xiaomei', '小美', 'xiaomei@demo.com'),
            ('admin', '管理员', 'admin@demo.com'),
        ]
        for username, display_name, email in users_data:
            User.objects.get_or_create(
                username=username,
                defaults={'display_name': display_name, 'email': email}
            )
        self.stdout.write(f'  创建了 {len(users_data)} 个用户')

    # ─── 业务线 ───────────────────────────────────────────────

    def _create_business_lines(self):
        bls = [
            ('payment', '支付业务线', 1, 'zhangsan'),
            ('ecommerce', '电商业务线', 2, 'qianqi'),
            ('platform', '基础平台', 3, 'zhoujiu'),
        ]
        for code, name, sort, leader_username in bls:
            leader = User.objects.get(username=leader_username)
            BusinessLine.objects.update_or_create(
                code=code,
                defaults={'name': name, 'sort_order': sort, 'leader': leader}
            )
        self.stdout.write(f'  创建了 {len(bls)} 个业务线（含负责人）')

    # ─── 组 ───────────────────────────────────────────────────

    def _create_groups(self):
        groups_data = [
            ('payment-dev', '支付研发组', 'payment', 'zhangsan'),
            ('payment-test', '支付测试组', 'payment', 'lisi'),
            ('payment-arch', '支付架构组', 'payment', 'lisi'),
            ('ecommerce-dev', '电商研发组', 'ecommerce', 'qianqi'),
            ('ecommerce-test', '电商测试组', 'ecommerce', 'sunba'),
            ('platform-ops', '平台运维组', 'platform', 'zhoujiu'),
            ('platform-dev', '平台研发组', 'platform', 'zhoujiu'),
            ('frontend', '前端组', 'ecommerce', 'sunba'),
            ('data-platform', '数据平台组', 'platform', 'zhoujiu'),
        ]
        for code, name, bl_code, leader_username in groups_data:
            bl = BusinessLine.objects.get(code=bl_code)
            leader = User.objects.get(username=leader_username)
            Group.objects.update_or_create(
                code=code,
                defaults={'name': name, 'business_line': bl, 'leader': leader}
            )
        self.stdout.write(f'  创建了 {len(groups_data)} 个组（含负责人）')

    # ─── 组 Role ──────────────────────────────────────────────

    def _create_group_roles(self):
        """为每个组创建专属 Role"""
        groups = Group.objects.all()
        for group in groups:
            role, created = Role.objects.get_or_create(
                name=f'{group.code}_role',
                defaults={
                    'owner_type': 'group',
                    'is_system': True,
                }
            )
            if created or not group.role:
                group.role = role
                group.save()
        self.stdout.write(f'  为 {groups.count()} 个组创建了专属 Role')

    # ─── 用户 Role ────────────────────────────────────────────

    def _create_user_roles(self):
        """为每个用户创建空白专属 Role"""
        users = User.objects.all()
        for user in users:
            role, created = Role.objects.get_or_create(
                name=f'{user.username}_role',
                defaults={
                    'owner_type': 'user',
                    'is_system': True,
                }
            )
            if created or not user.role:
                user.role = role
                user.save()
        self.stdout.write(f'  为 {users.count()} 个用户创建了专属 Role')

    # ─── 成员关系 ─────────────────────────────────────────────

    def _create_memberships(self):
        memberships = [
            ('zhangsan', 'payment-dev', 'primary'),
            ('lisi', 'payment-dev', 'primary'),
            ('lisi', 'payment-test', 'primary'),
            ('lisi', 'payment-arch', 'primary'),
            ('zhaoliu', 'payment-test', 'primary'),
            ('zhaoliu', 'payment-arch', 'primary'),
            ('qianqi', 'ecommerce-dev', 'primary'),
            ('sunba', 'ecommerce-dev', 'primary'),
            ('sunba', 'ecommerce-test', 'primary'),
            ('dawei', 'ecommerce-test', 'primary'),
            ('zhoujiu', 'platform-ops', 'primary'),
            ('zhoujiu', 'platform-dev', 'primary'),
            ('xiaomei', 'platform-dev', 'primary'),
            ('wangwu', 'frontend', 'primary'),
            ('xiaoliu', 'frontend', 'primary'),
            ('xiaochen', 'frontend', 'primary'),
            ('wangwu', 'payment-dev', 'collaborator'),
            ('wangwu', 'ecommerce-dev', 'collaborator'),
            ('xiaomei', 'data-platform', 'primary'),
            ('dawei', 'frontend', 'collaborator'),
        ]
        for username, group_code, mtype in memberships:
            user = User.objects.get(username=username)
            group = Group.objects.get(code=group_code)
            SubjectMembership.objects.get_or_create(
                user=user, group=group,
                defaults={'membership_type': mtype}
            )
        self.stdout.write(f'  创建了 {len(memberships)} 条成员关系')

    # ─── 环境 ─────────────────────────────────────────────────

    def _create_environments(self):
        envs = [
            ('dev', '开发环境', 'dev', 1, False),
            ('dev2', '开发环境2', 'dev', 2, False),
            ('test1', '测试环境1', 'test', 3, False),
            ('test2', '测试环境2', 'test', 4, False),
            ('test3', '测试环境3', 'test', 5, False),
            ('test4', '测试环境4', 'test', 6, False),
            ('test5', '测试环境5', 'test', 7, False),
            ('pre1', '预发环境1', 'staging', 8, False),
            ('pre2', '预发环境2', 'staging', 9, False),
            ('prod1', '生产环境1', 'prod', 10, True),
            ('prod2', '生产环境2', 'prod', 11, True),
        ]
        # 部署类型：dev/test/pre → k8s, prod1 → ec2, prod2 → k8s
        deploy_type_map = {
            'dev': 'k8s', 'dev2': 'k8s',
            'test1': 'k8s', 'test2': 'k8s', 'test3': 'k8s', 'test4': 'k8s', 'test5': 'k8s',
            'pre1': 'k8s', 'pre2': 'k8s',
            'prod1': 'ec2', 'prod2': 'k8s',
        }
        env_meta = {
            'dev': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-1', 'network_type': 'internal', 'k8s_context': 'kind-dev', 'cost_center': 'R&D'},
            'dev2': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-2', 'network_type': 'internal', 'k8s_context': 'kind-dev2', 'cost_center': 'R&D'},
            'test1': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-1', 'network_type': 'internal', 'k8s_context': 'kind-test1', 'cost_center': 'QA'},
            'test2': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-1', 'network_type': 'internal', 'k8s_context': 'kind-test2', 'cost_center': 'QA'},
            'test3': {'cloud_provider': 'aliyun', 'account_id': '987654321098', 'region': 'cn-shanghai', 'zone': 'AZ-1', 'network_type': 'internal', 'k8s_context': 'kind-test3', 'cost_center': 'QA'},
            'test4': {'cloud_provider': 'aliyun', 'account_id': '987654321098', 'region': 'cn-shanghai', 'zone': 'AZ-2', 'network_type': 'internal', 'k8s_context': 'kind-test4', 'cost_center': 'QA'},
            'test5': {'cloud_provider': 'aliyun', 'account_id': '987654321098', 'region': 'cn-shanghai', 'zone': 'AZ-2', 'network_type': 'internal', 'k8s_context': 'kind-test5', 'cost_center': 'QA'},
            'pre1': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-1', 'network_type': 'dmz', 'k8s_context': 'kind-pre1', 'cost_center': 'Staging'},
            'pre2': {'cloud_provider': 'aliyun', 'account_id': '987654321098', 'region': 'cn-shanghai', 'zone': 'AZ-2', 'network_type': 'dmz', 'k8s_context': 'kind-pre2', 'cost_center': 'Staging'},
            'prod1': {'cloud_provider': 'aws', 'account_id': '123456789012', 'region': 'cn-beijing', 'zone': 'AZ-1', 'network_type': 'dmz', 'k8s_context': 'kind-prod1', 'cost_center': 'Production'},
            'prod2': {'cloud_provider': 'aliyun', 'account_id': '987654321098', 'region': 'cn-shanghai', 'zone': 'AZ-2', 'network_type': 'dmz', 'k8s_context': 'kind-prod2', 'cost_center': 'Production'},
        }
        owners = {
            'dev': 'zhangsan', 'dev2': 'zhangsan',
            'test1': 'lisi', 'test2': 'lisi', 'test3': 'lisi', 'test4': 'lisi', 'test5': 'lisi',
            'pre1': 'zhoujiu', 'pre2': 'zhoujiu',
            'prod1': 'zhoujiu', 'prod2': 'zhoujiu',
        }
        for code, name, env_type, sort, is_prod in envs:
            meta = env_meta.get(code, {})
            owner = User.objects.filter(username=owners.get(code)).first()
            Environment.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'env_type': env_type,
                    'deploy_type': deploy_type_map.get(code, 'k8s'),
                    'sort_order': sort,
                    'is_prod': is_prod,
                    'description': f'{name}，用于 {env_type} 阶段',
                    'cloud_provider': meta.get('cloud_provider', ''),
                    'account_id': meta.get('account_id', ''),
                    'region': meta.get('region', ''),
                    'zone': meta.get('zone', ''),
                    'network_type': meta.get('network_type', 'internal'),
                    'k8s_context': meta.get('k8s_context', ''),
                    'cost_center': meta.get('cost_center', ''),
                    'owner': owner,
                    'status': 'active',
                }
            )
        self.stdout.write(f'  创建了 {len(envs)} 个环境')

    # ─── 集群 ─────────────────────────────────────────────────

    def _create_clusters(self):
        for env in Environment.objects.all():
            env_code = env.code
            cluster, _ = Cluster.objects.get_or_create(
                code=f'kind-{env_code}',
                defaults={
                    'name': f'kind-{env_code}',
                    'api_server': 'https://127.0.0.1:6443',
                    'environment': env,
                }
            )
            K8sNamespace.objects.get_or_create(
                name=env_code,
                cluster=cluster,
                defaults={'environment': env}
            )

    # ─── 应用 ─────────────────────────────────────────────────

    def _create_apps(self):
        lang_images = {
            'go':     {'builder_image': 'golang:1.23-alpine',          'base_image': 'alpine:3.20'},
            'node':   {'builder_image': 'node:20-alpine',              'base_image': 'node:20-alpine'},
            'python': {'builder_image': 'python:3.11-slim',            'base_image': 'python:3.11-slim'},
            'java':   {'builder_image': 'maven:3.9-eclipse-temurin-21','base_image': 'eclipse-temurin:21-jre-alpine'},
        }
        # (code, name, lang, bl_code, owner_username, group_code, app_type, priority, is_core, tech_stack, tags)
        apps_data = [
            ('payment-api', '支付核心服务', 'go', 'payment', 'zhangsan', 'payment-dev', 'backend', 'p0', True, ['gin', 'grpc', 'redis'], ['core', 'financial']),
            ('payment-frontend', '支付收银台', 'node', 'payment', 'zhangsan', 'payment-dev', 'web', 'p1', False, ['react', 'typescript'], ['frontend', 'payment']),
            ('payment-job', '支付定时任务', 'java', 'payment', 'lisi', 'payment-arch', 'job', 'p1', False, ['spring-boot', 'quartz'], ['job', 'payment']),
            ('order-api', '订单服务', 'python', 'ecommerce', 'qianqi', 'ecommerce-dev', 'backend', 'p1', True, ['django', 'celery', 'postgresql'], ['core', 'order']),
            ('inventory-api', '库存服务', 'go', 'ecommerce', 'qianqi', 'ecommerce-dev', 'backend', 'p1', True, ['go-zero', 'etcd'], ['core', 'inventory']),
            ('ecommerce-frontend', '电商前台', 'node', 'ecommerce', 'wangwu', 'frontend', 'web', 'p2', False, ['nextjs', 'tailwind'], ['frontend', 'ecommerce']),
            ('ecommerce-admin', '电商运营后台', 'node', 'ecommerce', 'sunba', 'frontend', 'web', 'p2', False, ['react', 'antd'], ['admin', 'ecommerce']),
            ('user-service', '用户中心', 'go', 'platform', 'zhoujiu', 'platform-dev', 'backend', 'p1', True, ['go-kit', 'nats'], ['core', 'user']),
            ('notification-service', '通知服务', 'python', 'platform', 'zhoujiu', 'platform-dev', 'backend', 'p2', False, ['fastapi', 'rabbitmq'], ['message', 'platform']),
            ('infra-gateway', 'API 网关', 'go', 'platform', 'zhoujiu', 'platform-ops', 'middleware', 'p0', True, ['envoy', 'lua'], ['gateway', 'infra']),
            ('infra-monitor', '监控告警', 'python', 'platform', 'xiaomei', 'data-platform', 'data', 'p1', True, ['prometheus', 'grafana'], ['observability', 'platform']),
            ('recommend-service', '推荐服务', 'python', 'platform', 'xiaomei', 'data-platform', 'backend', 'p2', False, ['pytorch', 'flask'], ['ml', 'recommend']),
            # ── Demo 应用（对应 demo-apps/ 下的三个真实应用）──
            # 负责人为李四（payment-dev 组主成员）；可见性走 own_group 模型：
            # 归属 payment-dev 组 → 组内成员（张三/李四）都可发布。
            ('go-app', 'Go Demo App', 'go', 'payment', 'lisi', 'payment-dev', 'backend', 'p1', False, ['gin'], ['demo', 'go']),
            ('node-app', 'Node Demo App', 'node', 'payment', 'lisi', 'payment-dev', 'backend', 'p1', False, ['express'], ['demo', 'node']),
            ('python-app', 'Python Demo App', 'python', 'payment', 'lisi', 'payment-dev', 'backend', 'p1', False, ['fastapi'], ['demo', 'python']),
        ]
        for code, name, lang, bl_code, owner_username, group_code, app_type, priority, is_core, tech_stack, tags in apps_data:
            bl = BusinessLine.objects.get(code=bl_code)
            owner = User.objects.get(username=owner_username)
            owner_group = Group.objects.get(code=group_code)
            images = lang_images.get(lang, {})
            app, _ = Application.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'language': lang,
                    'app_type': app_type,
                    'business_line': bl,
                    'owner_group': owner_group,
                    'owner': owner,
                    'product_owner': owner,
                    'qa_owner': User.objects.filter(username='lisi' if bl_code == 'payment' else 'sunba' if bl_code == 'ecommerce' else 'zhoujiu').first(),
                    'ops_owner': User.objects.get(username='zhoujiu'),
                    'priority': priority,
                    'is_core': is_core,
                    'tech_stack': tech_stack,
                    'tags': tags,
                    'deploy_mode': 'k8s',
                    'artifact_type': 'docker',
                    'repo_branch': 'main',
                    'git_group': f'{bl_code}-team',
                    'domain': f'{code}.demo.com',
                    'builder_image': images.get('builder_image', ''),
                    'base_image': images.get('base_image', ''),
                    'security_level': 'confidential' if priority == 'p0' else 'internal',
                    'sla': '99.99' if priority == 'p0' else '99.9',
                }
            )
            # 同步更新字段
            app.name = name
            app.language = lang
            app.app_type = app_type
            app.business_line = bl
            app.owner_group = owner_group
            app.owner = owner
            if not app.product_owner_id:
                app.product_owner = owner
            if not app.qa_owner_id:
                app.qa_owner = User.objects.filter(username='lisi' if bl_code == 'payment' else 'sunba' if bl_code == 'ecommerce' else 'zhoujiu').first()
            if not app.ops_owner_id:
                app.ops_owner = User.objects.get(username='zhoujiu')
            if not app.builder_image:
                app.builder_image = images.get('builder_image', '')
            if not app.base_image:
                app.base_image = images.get('base_image', '')
            app.priority = priority
            app.is_core = is_core
            app.tech_stack = tech_stack
            app.tags = tags
            app.git_group = f'{bl_code}-team'
            app.domain = f'{code}.demo.com'
            app.security_level = 'confidential' if priority == 'p0' else 'internal'
            app.sla = '99.99' if priority == 'p0' else '99.9'
            app.save()

            # 为每个应用创建环境配置
            for env in Environment.objects.all():
                cluster = Cluster.objects.get(code=f'kind-{env.code}')
                namespace = K8sNamespace.objects.get(name=env.code)
                AppEnvConfig.objects.get_or_create(
                    application=app, environment=env,
                    defaults={
                        'cluster': cluster,
                        'namespace': namespace,
                        'image_repo': code,
                        'deploy_strategy': 'rolling' if env.env_type not in ['staging'] else 'blue_green',
                    }
                )
        self.stdout.write(f'  创建了 {len(apps_data)} 个应用')

    # ─── 审批流模板 ───────────────────────────────────────────

    def _create_approval_flow_templates(self):
        templates = [
            {
                'name': '基础审批流',
                'code': 'basic_approval',
                'description': '单步审批：应用负责人审批',
                'steps': [
                    {
                        'order': 1,
                        'name': '应用负责人审批',
                        'dimension': 'app_owner',
                        'approver_resolver': 'app_owner',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                ],
            },
            {
                'name': '标准审批流',
                'code': 'standard_approval',
                'description': '两步审批：应用负责人 + 业务线负责人',
                'steps': [
                    {
                        'order': 1,
                        'name': '应用负责人审批',
                        'dimension': 'app_owner',
                        'approver_resolver': 'app_owner',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                    {
                        'order': 2,
                        'name': '业务线负责人审批',
                        'dimension': 'business_line_leader',
                        'approver_resolver': 'business_line_leader',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 48,
                    },
                ],
            },
            {
                'name': '跨组标准审批流',
                'code': 'cross_group_standard',
                'description': '跨组协作两步审批：应用负责人 + 业务线负责人',
                'steps': [
                    {
                        'order': 1,
                        'name': '应用负责人审批',
                        'dimension': 'app_owner',
                        'approver_resolver': 'app_owner',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                    {
                        'order': 2,
                        'name': '业务线负责人审批',
                        'dimension': 'business_line_leader',
                        'approver_resolver': 'business_line_leader',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 48,
                    },
                ],
            },
            {
                'name': '跨组高级审批流',
                'code': 'cross_group_advanced',
                'description': '跨组协作三步审批：应用负责人 + 业务线负责人 + 安全审批',
                'steps': [
                    {
                        'order': 1,
                        'name': '应用负责人审批',
                        'dimension': 'app_owner',
                        'approver_resolver': 'app_owner',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                    {
                        'order': 2,
                        'name': '业务线负责人审批',
                        'dimension': 'business_line_leader',
                        'approver_resolver': 'business_line_leader',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 48,
                    },
                    {
                        'order': 3,
                        'name': '安全审批',
                        'dimension': 'security',
                        'approver_resolver': 'fixed_role',
                        'resolver_config': {'role': 'security_team'},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                ],
            },
            {
                'name': '生产审批流',
                'code': 'production_approval',
                'description': '四步审批：应用负责人 + 业务线负责人 + 安全审批 + 运维审批',
                'steps': [
                    {
                        'order': 1,
                        'name': '应用负责人审批',
                        'dimension': 'app_owner',
                        'approver_resolver': 'app_owner',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                    {
                        'order': 2,
                        'name': '业务线负责人审批',
                        'dimension': 'business_line_leader',
                        'approver_resolver': 'business_line_leader',
                        'resolver_config': {},
                        'required_count': 1,
                        'timeout_hours': 48,
                    },
                    {
                        'order': 3,
                        'name': '安全审批',
                        'dimension': 'security',
                        'approver_resolver': 'fixed_role',
                        'resolver_config': {'role': 'security_team'},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                    {
                        'order': 4,
                        'name': '运维审批',
                        'dimension': 'ops',
                        'approver_resolver': 'fixed_role',
                        'resolver_config': {'role': 'ops_team'},
                        'required_count': 1,
                        'timeout_hours': 24,
                    },
                ],
            },
        ]
        # 保存所有审批流模板
        for tpl in templates:
            ApprovalFlowTemplate.objects.update_or_create(
                code=tpl['code'],
                defaults={
                    'name': tpl['name'],
                    'description': tpl['description'],
                    'steps': tpl['steps'],
                },
            )
        # 新增应用变更审批模板
        ApprovalFlowTemplate.objects.update_or_create(
            code='app_change_approval',
            defaults={
                'name': '应用变更审批流',
                'category': 'app_change',
                'description': '两步审批：应用负责人 + 业务线负责人',
                'steps': [
                    {'order': 1, 'name': '应用负责人审批', 'dimension': 'app_owner',
                     'approver_resolver': 'app_owner', 'resolver_config': {}, 'required_count': 1, 'timeout_hours': 24},
                    {'order': 2, 'name': '业务线负责人审批', 'dimension': 'business_line_leader',
                     'approver_resolver': 'business_line_leader', 'resolver_config': {}, 'required_count': 1, 'timeout_hours': 48},
                ],
            }
        )
        self.stdout.write(f'  创建了 {len(templates) + 1} 个审批流模板')

    # ─── 审批配置 ─────────────────────────────────────────────

    def _create_approval_configs(self):
        """按环境类型 + 授权范围创建审批策略"""
        configs = [
            # 本组权限
            ('dev', 'own_group', False, None),
            ('test', 'own_group', True, 'basic_approval'),
            ('staging', 'own_group', True, 'standard_approval'),
            ('prod', 'own_group', True, 'production_approval'),
            # 跨组协作
            ('dev', 'cross_group', True, 'standard_approval'),
            ('test', 'cross_group', True, 'standard_approval'),
            ('staging', 'cross_group', True, 'cross_group_advanced'),
            ('prod', 'cross_group', True, 'production_approval'),
        ]
        for env_type, grant_scope, requires, template_code in configs:
            template = None
            if template_code:
                template = ApprovalFlowTemplate.objects.get(code=template_code)
            EnvironmentApprovalConfig.objects.update_or_create(
                env_type=env_type,
                grant_scope=grant_scope,
                defaults={
                    'requires_approval': requires,
                    'flow_template': template,
                }
            )
        self.stdout.write(f'  创建了 {len(configs)} 条审批策略')

    # ─── 发布策略 ─────────────────────────────────────────────

    def _create_release_approval_configs(self):
        """按环境类型创建发布审批策略"""
        configs = [
            ('dev', False, None),
            ('test', True, 'basic_approval'),
            ('staging', True, 'standard_approval'),
            ('prod', True, 'production_approval'),
        ]
        for env_type, requires, template_code in configs:
            template = None
            if template_code:
                template = ApprovalFlowTemplate.objects.get(code=template_code)
            ReleaseApprovalConfig.objects.update_or_create(
                env_type=env_type,
                defaults={
                    'requires_approval': requires,
                    'flow_template': template,
                }
            )
        self.stdout.write(f'  创建了 {len(configs)} 条发布策略')

    # ─── 应用变更审批配置 ─────────────────────────────────────

    def _create_app_change_approval_config(self):
        template = ApprovalFlowTemplate.objects.filter(category='app_change').first()
        AppChangeApprovalConfig.objects.update_or_create(
            id=1,
            defaults={
                'requires_approval': True,
                'flow_template': template,
                'is_active': True,
            }
        )
        self.stdout.write('  创建了应用变更审批配置')

    def _create_group_default_rules(self):
        """
        为每个组创建默认数据权限规则：
        - 组名下应用 → dev 环境全授权
        """
        # 应用默认 dev/test 全授权给承接组
        envs = Environment.objects.all()

        for app in Application.objects.filter(status='active'):
            group = app.owner_group
            if not group or not group.role:
                continue
            bl = app.business_line

            for env_type in ['dev', 'test']:
                env_ids = list(envs.filter(env_type=env_type).values_list('id', flat=True))
                if env_ids:
                    RoleDataRule.objects.get_or_create(
                        role=group.role,
                        app_id=app.id,
                        env_type=env_type,
                        defaults={
                            'business_line_id': bl.id,
                            'owner_group_id': group.id,
                            'is_all_envs': True,
                            'allow_env_ids': [],
                            'deny_env_ids': [],
                            'grant_scope': 'own_group',
                        }
                    )

        # 跨组协作示例：支付研发组把 payment-api test 环境分享给前端组
        payment_dev = Group.objects.get(code='payment-dev')
        frontend = Group.objects.get(code='frontend')
        payment_api = Application.objects.get(code='payment-api')
        test_env_ids = list(envs.filter(env_type='test').values_list('id', flat=True))
        if payment_dev.role and frontend.role and test_env_ids:
            RoleDataRule.objects.get_or_create(
                role=frontend.role,
                app_id=payment_api.id,
                env_type='test',
                defaults={
                    'business_line_id': payment_api.business_line_id,
                    'owner_group_id': payment_dev.id,
                    'is_all_envs': True,
                    'allow_env_ids': [],
                    'deny_env_ids': [],
                    'grant_scope': 'cross_group',
                }
            )

        self.stdout.write('  创建了组默认数据权限规则')

    # ─── Demo 应用权限兜底 ────────────────────────────────────

    def _ensure_demo_app_permissions(self):
        """
        兜底：确保 3 个 Demo 应用（go-app/node-app/python-app）对 payment-dev 组可见。

        历史问题：Demo 应用曾出现 owner_group 为空（或只有张三的个人规则），
        导致组内成员（如李四，即 Demo 应用负责人）看不到 Demo 应用，
        表现为"Demo 应用又没了"。本方法显式保证：
          - 强制 app.owner_group = payment-dev（防止漂移）；
          - 为 payment-dev 组角色补齐每个 Demo 应用的 dev/test 全环境授权规则；
          - 幂等：规则已存在则跳过。
        需在 _rebuild_all_caches() 之前调用，使新规则进入有效权限缓存。
        """
        dev_group = Group.objects.filter(code='payment-dev').first()
        if not dev_group or not dev_group.role:
            self.stdout.write('  [warn] payment-dev 组或组 Role 不存在，跳过 Demo 应用权限兜底')
            return

        envs = Environment.objects.all()
        demo_codes = ['go-app', 'node-app', 'python-app']
        fixed_count = 0
        for code in demo_codes:
            app = Application.objects.filter(code=code).first()
            if not app:
                continue
            # 强制归属 payment-dev，防止 owner_group 漂移
            if app.owner_group_id != dev_group.id:
                app.owner_group = dev_group
                app.save(update_fields=['owner_group'])
                fixed_count += 1
            for env_type in ['dev', 'test']:
                env_ids = list(envs.filter(env_type=env_type).values_list('id', flat=True))
                if not env_ids:
                    continue
                RoleDataRule.objects.get_or_create(
                    role=dev_group.role,
                    app_id=app.id,
                    env_type=env_type,
                    defaults={
                        'business_line_id': app.business_line_id,
                        'owner_group_id': dev_group.id,
                        'is_all_envs': True,
                        'allow_env_ids': [],
                        'deny_env_ids': [],
                        'grant_scope': 'own_group',
                    }
                )
        self.stdout.write(f'  已确保 {len(demo_codes)} 个 Demo 应用对 payment-dev 组可见（修正 owner_group {fixed_count} 处）')

    # ─── 用户个人权限规则 ──────────────────────────────────────

    def _create_user_custom_rules(self):
        """
        创建用户个人权限规则示例，包含混合权限和跨组协作场景
        """
        from django.utils import timezone
        from datetime import timedelta

        test1 = Environment.objects.get(code='test1')
        test2 = Environment.objects.get(code='test2')
        test3 = Environment.objects.get(code='test3')
        test4 = Environment.objects.get(code='test4')

        def _ensure_partial_group_rule(group, app):
            """为组创建只授权 test1-test2 的测试环境规则"""
            if not group.role:
                return None
            rule, _ = RoleDataRule.objects.get_or_create(
                role=group.role,
                app_id=app.id,
                env_type='test',
                defaults={
                    'business_line_id': app.business_line_id,
                    'owner_group_id': group.id,
                    'is_all_envs': False,
                    'allow_env_ids': [test1.id, test2.id],
                    'deny_env_ids': [],
                    'grant_scope': 'own_group',
                }
            )
            rule.is_all_envs = False
            rule.allow_env_ids = [test1.id, test2.id]
            rule.owner_group_id = group.id
            rule.grant_scope = 'own_group'
            rule.valid_to = None
            rule.save()
            return rule

        def _ensure_user_rule(user, app, owner_group, allow_env_ids):
            if not user.role:
                return
            RoleDataRule.objects.update_or_create(
                role=user.role,
                app_id=app.id,
                env_type='test',
                defaults={
                    'business_line_id': app.business_line_id,
                    'owner_group_id': owner_group.id,
                    'is_all_envs': False,
                    'allow_env_ids': allow_env_ids,
                    'deny_env_ids': [],
                    'grant_scope': 'own_group',
                }
            )

        # 场景1：赵六（支付测试组）payment-api 混合权限
        zhaoliu = User.objects.get(username='zhaoliu')
        payment_api = Application.objects.get(code='payment-api')
        payment_test = Group.objects.get(code='payment-test')
        _ensure_partial_group_rule(payment_test, payment_api)
        _ensure_user_rule(zhaoliu, payment_api, payment_test, [test3.id, test4.id])

        # 场景2：孙八（电商研发组）order-api 混合权限
        sunba = User.objects.get(username='sunba')
        order_api = Application.objects.get(code='order-api')
        ecommerce_dev = Group.objects.get(code='ecommerce-dev')
        _ensure_partial_group_rule(ecommerce_dev, order_api)
        _ensure_user_rule(sunba, order_api, ecommerce_dev, [test3.id, test4.id])

        # 场景3：小美（平台研发组）infra-monitor 混合权限
        xiaomei = User.objects.get(username='xiaomei')
        infra_monitor = Application.objects.get(code='infra-monitor')
        platform_dev = Group.objects.get(code='platform-dev')
        _ensure_partial_group_rule(platform_dev, infra_monitor)
        _ensure_user_rule(xiaomei, infra_monitor, platform_dev, [test3.id, test4.id])

        # 场景4：王五（前端组）跨组协作 payment-api 临时授权
        wangwu = User.objects.get(username='wangwu')
        payment_dev = Group.objects.get(code='payment-dev')
        if wangwu.role:
            RoleDataRule.objects.get_or_create(
                role=wangwu.role,
                app_id=payment_api.id,
                env_type='test',
                defaults={
                    'business_line_id': payment_api.business_line_id,
                    'owner_group_id': payment_dev.id,
                    'is_all_envs': False,
                    'allow_env_ids': [test1.id, test2.id],
                    'deny_env_ids': [],
                    'grant_scope': 'cross_group',
                    'valid_from': timezone.now(),
                    'valid_to': timezone.now() + timedelta(days=30),
                }
            )

        # 场景5：大伟（电商测试组）user-service 跨组协作权限
        dawei = User.objects.get(username='dawei')
        user_service = Application.objects.get(code='user-service')
        platform_dev = Group.objects.get(code='platform-dev')
        if dawei.role:
            RoleDataRule.objects.get_or_create(
                role=dawei.role,
                app_id=user_service.id,
                env_type='test',
                defaults={
                    'business_line_id': user_service.business_line_id,
                    'owner_group_id': platform_dev.id,
                    'is_all_envs': False,
                    'allow_env_ids': [test1.id, test2.id, test3.id],
                    'deny_env_ids': [],
                    'grant_scope': 'cross_group',
                }
            )

        self.stdout.write('  创建了用户个人权限规则示例')

    # ─── 缓存重算 ─────────────────────────────────────────────

    def _rebuild_all_caches(self):
        from apps.authz.utils import rebuild_user_cache

        users = User.objects.all()
        for user in users:
            rebuild_user_cache(user)
        self.stdout.write(f'  重算了 {users.count()} 个用户的有效权限缓存')

    # ─── 制品库 ───────────────────────────────────────────────

    def _create_artifact_repos(self):
        ArtifactRepository.objects.get_or_create(
            name='本地 Docker Registry',
            defaults={
                'repo_type': 'docker_registry',
                'url': 'localhost:5000',
                'is_default': True,
            }
        )

    def _create_demo_artifacts(self):
        """为 demo 应用创建制品记录"""
        from apps.artifacts.models import Artifact, ArtifactPromotion
        from apps.infrastructures.models import Environment

        repo = ArtifactRepository.objects.filter(is_default=True).first()
        if not repo:
            return

        zhangsan = User.objects.get(username='zhangsan')
        demo_apps = [
            ('go-app', 'go', [
                ('v1.0.0', 'dev', 'main', 'a1b2c3d4', 45),
                ('v1.0.0', 'test1', 'main', 'a1b2c3d4', 45),
                ('v1.1.0', 'dev', 'main', 'e5f6g7h8', 52),
            ]),
            ('node-app', 'node', [
                ('v1.0.0', 'dev', 'main', 'b2c3d4e5', 38),
                ('v1.0.0', 'test1', 'main', 'b2c3d4e5', 38),
            ]),
            ('python-app', 'python', [
                ('v1.0.0', 'dev', 'main', 'c3d4e5f6', 30),
                ('v1.0.0', 'test1', 'main', 'c3d4e5f6', 30),
                ('v1.0.0', 'pre1', 'main', 'c3d4e5f6', 30),
                ('v1.1.0', 'dev', 'main', 'f7g8h9i0', 35),
                ('v1.1.0', 'test1', 'main', 'f7g8h9i0', 35),
            ]),
        ]

        count = 0
        for app_code, lang, versions in demo_apps:
            try:
                app = Application.objects.get(code=app_code)
            except Application.DoesNotExist:
                continue
            for version, env, branch, commit, duration in versions:
                env_obj = Environment.objects.filter(code=env).first()
                artifact, created = Artifact.objects.get_or_create(
                    application=app,
                    version=version,
                    current_env=env,
                    defaults={
                        'artifact_type': 'docker_image',
                        'repository': repo,
                        'storage_path': f'registry.local/{app_code}:{version}',
                        'image_tag': f'{app_code}:{version}',
                        'branch': branch,
                        'commit_id': commit,
                        'build_duration': duration,
                        'file_size': 45 * 1024 * 1024,  # ~45MB
                        'created_by': zhangsan,
                    }
                )
                if created:
                    count += 1

        # 为 python-app v1.0.0 创建晋级记录（dev → test1 → pre1）
        try:
            py_app = Application.objects.get(code='python-app')
            py_artifact = Artifact.objects.filter(application=py_app, version='v1.0.0').order_by('id').first()
            if py_artifact:
                dev_env = Environment.objects.get(code='dev')
                test_env = Environment.objects.get(code='test1')
                pre_env = Environment.objects.get(code='pre1')
                ArtifactPromotion.objects.get_or_create(
                    artifact=py_artifact, from_env=dev_env, to_env=test_env,
                    defaults={'status': 'promoted', 'promoted_by': zhangsan}
                )
                ArtifactPromotion.objects.get_or_create(
                    artifact=py_artifact, from_env=test_env, to_env=pre_env,
                    defaults={'status': 'promoted', 'promoted_by': zhangsan}
                )
        except Exception:
            pass

        self.stdout.write(f'  创建了 {count} 条制品记录')

    # ─── 镜像注册表 ────────────────────────────────────────────

    def _create_image_registry(self):
        images_data = [
            ('python', 'python:3.11-slim', 'python:3.11-slim', 'Python 应用，CI/CD 使用同一镜像'),
            ('go', 'golang:1.23-alpine', 'alpine:3.20', 'Go 编译产物为静态二进制，运行时用精简镜像'),
            ('node', 'node:20-alpine', 'node:20-alpine', 'Node.js 应用，CI/CD 使用同一镜像'),
            ('java', 'maven:3.9-eclipse-temurin-21', 'eclipse-temurin:21-jre-alpine', 'Java 使用 Maven 编译，JRE 运行'),
            ('other', 'alpine:3.20', 'alpine:3.20', '其他语言使用通用 Alpine 镜像'),
        ]
        for lang, builder, base, desc in images_data:
            ImageRegistry.objects.update_or_create(
                language=lang,
                defaults={
                    'builder_image': builder,
                    'base_image': base,
                    'description': desc,
                }
            )
        self.stdout.write(f'  创建了 {len(images_data)} 条镜像注册表记录')

    # ─── 权限申请记录 ──────────────────────────────────────────

    def _create_permission_requests(self):
        """
        创建历史权限申请记录，用于支撑 申请记录 和 与我相关 页面展示。
        """
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()

        payment_api = Application.objects.get(code='payment-api')
        order_api = Application.objects.get(code='order-api')
        user_service = Application.objects.get(code='user-service')
        infra_monitor = Application.objects.get(code='infra-monitor')
        ecommerce_admin = Application.objects.get(code='ecommerce-admin')

        payment_dev = Group.objects.get(code='payment-dev')
        frontend = Group.objects.get(code='frontend')
        ecommerce_dev = Group.objects.get(code='ecommerce-dev')
        platform_dev = Group.objects.get(code='platform-dev')

        zhang_san = User.objects.get(username='zhangsan')
        wang_wu = User.objects.get(username='wangwu')
        da_wei = User.objects.get(username='dawei')
        xiao_chen = User.objects.get(username='xiaochen')
        xiao_mei = User.objects.get(username='xiaomei')

        # 1. 王五申请 payment-api 权限（待审批）
        if not PermissionRequest.objects.filter(
            user=wang_wu, app_id=payment_api.id, request_type='apply', status='pending'
        ).exists():
            PermissionRequest.objects.create(
                user=wang_wu,
                request_type='apply',
                app_id=payment_api.id,
                env_type='staging',
                is_all_envs=False,
                env_ids=[
                    Environment.objects.get(code='pre1').id,
                    Environment.objects.get(code='pre2').id,
                ],
                grant_scope='cross_group',
                reason='需要预发环境联调支付接口',
                status='pending',
                extra_data={
                    'owner_group_id': payment_dev.id,
                    'target_user_ids': [wang_wu.id],
                },
                beneficiary_user_ids=[wang_wu.id],
                beneficiary_group_ids=[],
                created_at=now - timedelta(hours=2),
            )

        # 2. 大伟申请 user-service 权限（已通过）
        if not PermissionRequest.objects.filter(
            user=da_wei, app_id=user_service.id, request_type='apply', status='approved'
        ).exists():
            PermissionRequest.objects.create(
                user=da_wei,
                request_type='apply',
                app_id=user_service.id,
                env_type='test',
                is_all_envs=False,
                env_ids=[
                    Environment.objects.get(code='test1').id,
                    Environment.objects.get(code='test2').id,
                    Environment.objects.get(code='test3').id,
                ],
                grant_scope='cross_group',
                reason='测试电商用户中心集成',
                status='approved',
                extra_data={
                    'owner_group_id': platform_dev.id,
                    'target_user_ids': [da_wei.id],
                },
                beneficiary_user_ids=[da_wei.id],
                beneficiary_group_ids=[],
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=2),
            )

        # 3. 小陈申请 order-api 权限（已拒绝）
        if not PermissionRequest.objects.filter(
            user=xiao_chen, app_id=order_api.id, request_type='apply', status='rejected'
        ).exists():
            PermissionRequest.objects.create(
                user=xiao_chen,
                request_type='apply',
                app_id=order_api.id,
                env_type='test',
                is_all_envs=True,
                env_ids=[],
                grant_scope='own_group',
                reason='需要订单服务测试环境联调',
                status='rejected',
                extra_data={
                    'owner_group_id': ecommerce_dev.id,
                    'target_group_id': frontend.id,
                },
                beneficiary_user_ids=[xiao_chen.id],
                beneficiary_group_ids=[frontend.id],
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=4),
            )

        # 4. 张三分享 payment-api 给前端组（已通过）
        if not PermissionRequest.objects.filter(
            user=zhang_san, app_id=payment_api.id, request_type='share', status='approved'
        ).exists():
            PermissionRequest.objects.create(
                user=zhang_san,
                request_type='share',
                app_id=payment_api.id,
                env_type='test',
                is_all_envs=True,
                env_ids=[],
                grant_scope='cross_group',
                reason='前端组需要支付接口测试环境',
                status='approved',
                extra_data={
                    'owner_group_id': payment_dev.id,
                    'target_group_id': frontend.id,
                },
                beneficiary_user_ids=[],
                beneficiary_group_ids=[frontend.id],
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=9),
            )

        # 5. 小美申请 infra-monitor staging 权限（待审批 - 与我相关）
        if not PermissionRequest.objects.filter(
            user=xiao_mei, app_id=infra_monitor.id, request_type='apply', status='pending'
        ).exists():
            PermissionRequest.objects.create(
                user=xiao_mei,
                request_type='apply',
                app_id=infra_monitor.id,
                env_type='staging',
                is_all_envs=False,
                env_ids=[
                    Environment.objects.get(code='pre1').id,
                ],
                grant_scope='own_group',
                reason='监控告警系统预发环境验证',
                status='pending',
                extra_data={
                    'owner_group_id': platform_dev.id,
                    'target_group_id': platform_dev.id,
                },
                beneficiary_user_ids=[xiao_mei.id],
                beneficiary_group_ids=[platform_dev.id],
                created_at=now - timedelta(hours=5),
            )

        # 6. 张三回收 payment-api 从前端组的协作权限（待审批 - 与我相关）
        if not PermissionRequest.objects.filter(
            user=zhang_san, app_id=payment_api.id, request_type='revoke', status='pending'
        ).exists():
            PermissionRequest.objects.create(
                user=zhang_san,
                request_type='revoke',
                app_id=payment_api.id,
                env_type='test',
                is_all_envs=False,
                env_ids=[
                    Environment.objects.get(code='test1').id,
                    Environment.objects.get(code='test2').id,
                ],
                grant_scope='cross_group',
                reason='前端组已完成支付接口对接，回收测试环境权限',
                status='pending',
                extra_data={
                    'owner_group_id': payment_dev.id,
                    'target_group_id': frontend.id,
                },
                beneficiary_user_ids=[],
                beneficiary_group_ids=[frontend.id],
                created_at=now - timedelta(hours=1),
            )

        self.stdout.write(f'  创建了 6 条权限申请记录')