"""
种子数据脚本
创建演示账号、角色、权限、部门、云账号、Mock 资源
用法: python3 manage.py shell < backend/seed_data.py
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import User, Role, Permission, Department, UserRole, RolePermission
from cmdb.models import CloudAccount, Resource, Application
from provider.core import MockProvider


def create_departments():
    """创建部门"""
    departments = [
        {'name': '技术部', 'sort_order': 1},
        {'name': '运维组', 'sort_order': 2},
        {'name': '研发组', 'sort_order': 3},
        {'name': '产品部', 'sort_order': 4},
        {'name': '财务部', 'sort_order': 5},
    ]
    dept_objs = {}
    for d in departments:
        obj, _ = Department.objects.get_or_create(name=d['name'], defaults=d)
        dept_objs[d['name']] = obj
    print(f'✅ 创建了 {len(dept_objs)} 个部门')
    return dept_objs


def create_roles():
    """创建角色"""
    roles_data = [
        {'name': '超级管理员', 'code': 'super_admin', 'description': '系统最高权限'},
        {'name': '云管理员', 'code': 'cloud_admin', 'description': '管理所有云资源'},
        {'name': '运维工程师', 'code': 'ops', 'description': '运维操作权限'},
        {'name': '只读用户', 'code': 'readonly', 'description': '仅查看权限'},
    ]
    role_objs = {}
    for r in roles_data:
        obj, _ = Role.objects.get_or_create(code=r['code'], defaults=r)
        role_objs[r['code']] = obj
    print(f'✅ 创建了 {len(role_objs)} 个角色')
    return role_objs


def create_permissions():
    """创建权限点"""
    permissions_data = [
        # CMDB 权限
        {'name': '查看资源', 'code': 'cmdb:resource:view', 'module': 'cmdb'},
        {'name': '创建资源', 'code': 'cmdb:resource:create', 'module': 'cmdb'},
        {'name': '编辑资源', 'code': 'cmdb:resource:edit', 'module': 'cmdb'},
        {'name': '删除资源', 'code': 'cmdb:resource:delete', 'module': 'cmdb'},
        {'name': '启动主机', 'code': 'cmdb:instance:start', 'module': 'cmdb'},
        {'name': '停止主机', 'code': 'cmdb:instance:stop', 'module': 'cmdb'},
        {'name': '变更规格', 'code': 'cmdb:instance:resize', 'module': 'cmdb'},
        {'name': '下线主机', 'code': 'cmdb:instance:release', 'module': 'cmdb'},
        {'name': '编辑依赖关系', 'code': 'cmdb:relation:edit', 'module': 'cmdb'},
        # 工单权限
        {'name': '查看工单', 'code': 'ticket:order:view', 'module': 'ticket'},
        {'name': '创建工单', 'code': 'ticket:order:create', 'module': 'ticket'},
        {'name': '审批工单', 'code': 'ticket:approve', 'module': 'ticket'},
        {'name': '取消工单', 'code': 'ticket:order:cancel', 'module': 'ticket'},
        # 账号权限
        {'name': '管理云账号', 'code': 'account:manage', 'module': 'account'},
        {'name': '同步云账号', 'code': 'account:sync', 'module': 'account'},
        # 系统权限
        {'name': '用户管理', 'code': 'system:user:manage', 'module': 'system'},
        {'name': '角色管理', 'code': 'system:role:manage', 'module': 'system'},
    ]
    perm_objs = {}
    for p in permissions_data:
        obj, _ = Permission.objects.get_or_create(code=p['code'], defaults=p)
        perm_objs[p['code']] = obj
    print(f'✅ 创建了 {len(perm_objs)} 个权限点')
    return perm_objs


def assign_role_permissions(role_objs, perm_objs):
    """分配角色权限"""
    # 超级管理员：全部权限
    for perm in perm_objs.values():
        RolePermission.objects.get_or_create(role=role_objs['super_admin'], permission=perm)

    # 云管理员：CMDB + 工单 + 账号权限
    cloud_admin_codes = [c for c in perm_objs if c.startswith(('cmdb:', 'ticket:', 'account:'))]
    for code in cloud_admin_codes:
        RolePermission.objects.get_or_create(role=role_objs['cloud_admin'], permission=perm_objs[code])

    # 运维：CMDB 查看/操作 + 工单创建/查看
    ops_codes = [
        'cmdb:resource:view', 'cmdb:instance:start', 'cmdb:instance:stop',
        'cmdb:instance:resize', 'cmdb:instance:release',
        'cmdb:relation:edit',
        'ticket:order:view', 'ticket:order:create',
    ]
    for code in ops_codes:
        if code in perm_objs:
            RolePermission.objects.get_or_create(role=role_objs['ops'], permission=perm_objs[code])

    # 只读：查看权限
    readonly_codes = ['cmdb:resource:view', 'ticket:order:view']
    for code in readonly_codes:
        if code in perm_objs:
            RolePermission.objects.get_or_create(role=role_objs['readonly'], permission=perm_objs[code])

    print('✅ 角色权限分配完成')


def create_users(dept_objs, role_objs):
    """创建演示用户"""
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'display_name': '系统管理员',
            'email': 'admin@cloud-manager.com',
            'department': dept_objs.get('技术部'),
            'roles': ['super_admin'],
        },
        {
            'username': 'cloud_admin',
            'password': 'admin123',
            'display_name': '云管理员',
            'email': 'cloud@cloud-manager.com',
            'department': dept_objs.get('运维组'),
            'roles': ['cloud_admin'],
        },
        {
            'username': 'ops_user',
            'password': 'admin123',
            'display_name': '运维工程师',
            'email': 'ops@cloud-manager.com',
            'department': dept_objs.get('运维组'),
            'roles': ['ops'],
        },
        {
            'username': 'readonly',
            'password': 'admin123',
            'display_name': '只读用户',
            'email': 'readonly@cloud-manager.com',
            'department': dept_objs.get('研发组'),
            'roles': ['readonly'],
        },
    ]

    for u in users_data:
        roles = u.pop('roles')
        user, created = User.objects.get_or_create(
            username=u['username'],
            defaults={**u, 'is_staff': True, 'is_superuser': u['username'] == 'admin'}
        )
        if created:
            user.set_password(u['password'])
            user.save()
            for role_code in roles:
                if role_code in role_objs:
                    UserRole.objects.get_or_create(user=user, role=role_objs[role_code])

    print(f'✅ 创建了 {len(users_data)} 个演示用户')


def create_cloud_accounts():
    """创建云账号"""
    accounts_data = [
        {
            'account_name': 'Mock 账号',
            'provider_type': 'mock',
            'regions': 'cn-hangzhou,cn-shanghai,cn-beijing,us-east-1',
            'status': 1,
        },
    ]
    for a in accounts_data:
        CloudAccount.objects.get_or_create(
            account_name=a['account_name'],
            defaults=a
        )
    print(f'✅ 创建了 {len(accounts_data)} 个云账号')


def create_mock_resources():
    """创建 Mock 资源"""
    account = CloudAccount.objects.filter(provider_type='mock').first()
    if not account:
        print('⚠️ 未找到 Mock 云账号，跳过资源创建')
        return

    provider = MockProvider()
    regions = MockProvider.REGIONS

    count = 0
    for region in regions:
        for vo in provider.list_instances(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'zone': vo.zone,
                    'status': vo.status,
                    'spec': vo.spec,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

        for vo in provider.list_vpcs(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'status': vo.status,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

        for vo in provider.list_security_groups(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'status': vo.status,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

        for vo in provider.list_subnets(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'zone': vo.zone,
                    'status': vo.status,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

        for vo in provider.list_disks(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'status': vo.status,
                    'spec': vo.spec,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

        for vo in provider.list_load_balancers(region):
            Resource.objects.get_or_create(
                cloud_resource_id=vo.cloud_resource_id,
                defaults={
                    'account': account,
                    'provider_type': 'mock',
                    'resource_type': vo.resource_type,
                    'resource_name': vo.resource_name,
                    'cloud_resource_id': vo.cloud_resource_id,
                    'region': vo.region,
                    'status': vo.status,
                    'spec': vo.spec,
                    'metadata': vo.metadata,
                    'source': 0,
                }
            )
            count += 1

    print(f'✅ 创建了 {count} 个 Mock 资源')


def create_resource_relations():
    """创建资源关系（实例→VPC、实例→安全组）"""
    from cmdb.models import Resource, ResourceRelation

    instances = Resource.objects.filter(resource_type='instance', is_deleted=False)
    vpcs = Resource.objects.filter(resource_type='vpc', is_deleted=False)
    sgs = Resource.objects.filter(resource_type='security_group', is_deleted=False)

    count = 0
    for inst in instances:
        # 每个实例关联一个 VPC（按地域匹配）
        vpc = vpcs.filter(region=inst.region).first()
        if vpc:
            _, created = ResourceRelation.objects.get_or_create(
                source=inst, target=vpc, relation_type='belongs_to_vpc'
            )
            if created:
                count += 1

        # 每个实例关联 1-2 个安全组
        region_sgs = sgs.filter(region=inst.region)
        for sg in region_sgs[:2]:
            _, created = ResourceRelation.objects.get_or_create(
                source=inst, target=sg, relation_type='attach_sg'
            )
            if created:
                count += 1

    print(f'✅ 创建了 {count} 条资源关系')


def create_service_catalog():
    """创建服务目录"""
    from catalog.models import ServiceCategory, ServiceItem, Quota
    from accounts.models import Department

    # 分类
    compute_cat, _ = ServiceCategory.objects.get_or_create(name='计算', defaults={'icon': '🖥️', 'sort_order': 1})
    network_cat, _ = ServiceCategory.objects.get_or_create(name='网络', defaults={'icon': '🌐', 'sort_order': 2})
    storage_cat, _ = ServiceCategory.objects.get_or_create(name='存储', defaults={'icon': '💾', 'sort_order': 3})

    # 服务项
    items_data = [
        {'name': '云主机', 'category': compute_cat, 'icon': '🖥️',
         'spec_options': [
             {'label': '2核4G (入门)', 'value': 't3.medium', 'cpu': 2, 'memory': 4, 'price': 99},
             {'label': '4核8G (标准)', 'value': 't3.large', 'cpu': 4, 'memory': 8, 'price': 199},
             {'label': '8核16G (增强)', 'value': 't3.xlarge', 'cpu': 8, 'memory': 16, 'price': 399},
             {'label': '16核32G (旗舰)', 'value': 'ecs.g6.2xlarge', 'cpu': 16, 'memory': 32, 'price': 799},
         ],
         'region_options': ['cn-hangzhou', 'cn-shanghai', 'cn-beijing', 'us-east-1']},
        {'name': '负载均衡', 'category': network_cat, 'icon': '⚖️',
         'spec_options': [
             {'label': '标准型', 'value': 'slb.s1.small', 'price': 59},
             {'label': '高性能型', 'value': 'slb.s2.medium', 'price': 199},
         ]},
        {'name': '云数据库', 'category': storage_cat, 'icon': '🗄️',
         'spec_options': [
             {'label': '1核2G', 'value': 'rds.mysql.s1.small', 'cpu': 1, 'memory': 2, 'price': 149},
             {'label': '2核4G', 'value': 'rds.mysql.s2.medium', 'cpu': 2, 'memory': 4, 'price': 299},
         ]},
    ]
    for item_data in items_data:
        ServiceItem.objects.get_or_create(
            name=item_data['name'],
            defaults={**item_data}
        )

    # 配额（每个部门）
    departments = Department.objects.all()
    for dept in departments:
        for item in ServiceItem.objects.all():
            Quota.objects.get_or_create(
                department=dept, service_item=item,
                defaults={'quota_limit': 10, 'used': 0}
            )

    print(f'✅ 创建了服务目录 ({ServiceCategory.objects.count()} 分类, {ServiceItem.objects.count()} 服务项)')


def create_cost_data():
    """创建模拟成本数据"""
    import random
    from decimal import Decimal
    from datetime import date
    from cost.models import CostBill, CostItem, Budget
    from cmdb.models import CloudAccount, Resource, Application
    from accounts.models import Department

    accounts = CloudAccount.objects.all()
    dept_pool = list(Department.objects.all())
    app_pool = list(Application.objects.all())

    # 生成最近6个月的账单
    for months_ago in range(5, -1, -1):
        d = date.today().replace(day=1)
        for _ in range(months_ago):
            if d.month == 1:
                d = d.replace(year=d.year - 1, month=12)
            else:
                d = d.replace(month=d.month - 1)
        month_str = d.strftime('%Y-%m')

        for account in accounts:
            bill, created = CostBill.objects.get_or_create(
                account=account, bill_month=month_str,
                defaults={'total_cost': 0}
            )
            if not created:
                continue

            resources = Resource.objects.filter(account=account, is_deleted=False)
            total = Decimal('0')
            for r in resources:
                base_price = random.uniform(30, 600)
                cost = round(base_price * random.uniform(0.7, 1.3), 2)
                day = random.randint(1, 28)
                # 账单分摊标签（模拟云账单 Cost Allocation Tag 解析）：
                # 部门从全部部门随机；应用约 70% 有归属、30% 未归属
                dept = random.choice(dept_pool) if dept_pool else None
                app = random.choice(app_pool) if app_pool and random.random() < 0.7 else None
                CostItem.objects.create(
                    bill=bill, resource=r, service_type=r.resource_type,
                    cost=cost, cost_date=f'{month_str}-{day:02d}',
                    department=dept,
                    application=app,
                )
                total += Decimal(str(cost))
            bill.total_cost = total
            bill.save()

    # 创建部门预算
    for dept in dept_pool:
        Budget.objects.get_or_create(
            department=dept, month=date.today().strftime('%Y-%m'),
            defaults={
                'budget_amount': random.choice([5000, 10000, 20000, 50000]),
                'used_amount': 0, 'alert_threshold': 80
            }
        )
    # 更新已用金额
    for budget in Budget.objects.all():
        items = CostItem.objects.filter(
            department=budget.department, bill__bill_month=budget.month
        )
        from django.db.models import Sum
        total = items.aggregate(Sum('cost'))['cost__sum'] or 0
        budget.used_amount = total
        budget.save()

    print(f'✅ 创建了 {CostBill.objects.count()} 条账单, {CostItem.objects.count()} 条费用明细, {Budget.objects.count()} 条预算')


def create_applications():
    """创建应用（业务层）"""
    from accounts.models import Department
    from cmdb.models import Application

    depts = {d.name: d for d in Department.objects.all()}
    apps_data = [
        {
            'name': '订单中心',
            'department': depts.get('研发组'), 'owner': '张伟',
            'description': '订单与交易核心服务，包含前端/后端/数据库/缓存',
            'app_code': 'order-center', 'app_name_en': 'order-center-service',
            'cmdb_ci_id': 'ci_app_1001', 'business_line': '交易中台',
            'app_category': 'core_business',
            'dev_owner': '李明', 'ops_owner': '赵磊', 'alert_group': 'order-center-alert',
            'creator': 'admin',
            'language': 'Java', 'framework': 'Spring Boot 3.2', 'app_type': 'microservice',
            'git_repo': 'git@git.xxx.com/order-center.git', 'default_branch': 'main',
            'artifact_repo': 'harbor.xxx.com/order-center',
            'ci_pipeline': 'https://ci.xxx.com/pipelines/order-center',
            'deploy_type': 'k8s', 'default_cluster': 'k8s-prod-01',
            'importance_level': 'P0', 'sla': '99.95%', 'dr_level': '同城双活',
            'change_policy': 'multi', 'domain': 'order.xxx.com',
            'tags': ['交易', '核心', '微服务'], 'doc_url': 'https://wiki.xxx.com/order-center',
        },
        {
            'name': '支付中心',
            'department': depts.get('研发组'), 'owner': '李娜',
            'description': '支付网关与账务服务',
            'app_code': 'pay-center', 'app_name_en': 'pay-center-service',
            'cmdb_ci_id': 'ci_app_1002', 'business_line': '资金中台',
            'app_category': 'core_business',
            'dev_owner': '陈晨', 'ops_owner': '赵磊', 'alert_group': 'pay-center-alert',
            'creator': 'admin',
            'language': 'Go', 'framework': 'Gin 1.9', 'app_type': 'microservice',
            'git_repo': 'git@git.xxx.com/pay-center.git', 'default_branch': 'main',
            'artifact_repo': 'harbor.xxx.com/pay-center',
            'ci_pipeline': 'https://ci.xxx.com/pipelines/pay-center',
            'deploy_type': 'k8s', 'default_cluster': 'k8s-prod-02',
            'importance_level': 'P0', 'sla': '99.99%', 'dr_level': '异地多活',
            'change_policy': 'multi', 'domain': 'pay.xxx.com',
            'tags': ['支付', '合规', '金融'], 'doc_url': 'https://wiki.xxx.com/pay-center',
        },
        {
            'name': '用户中心',
            'department': depts.get('技术部'), 'owner': '王强',
            'description': '用户账号与统一认证服务',
            'app_code': 'user-center', 'app_name_en': 'user-center-service',
            'cmdb_ci_id': 'ci_app_1003', 'business_line': '基础平台',
            'app_category': 'foundation',
            'dev_owner': '刘洋', 'ops_owner': '孙浩', 'alert_group': 'user-center-alert',
            'creator': 'admin',
            'language': 'Python', 'framework': 'Django 4.2', 'app_type': 'microservice',
            'git_repo': 'git@git.xxx.com/user-center.git', 'default_branch': 'main',
            'artifact_repo': 'harbor.xxx.com/user-center',
            'ci_pipeline': 'https://ci.xxx.com/pipelines/user-center',
            'deploy_type': 'k8s', 'default_cluster': 'k8s-prod-03',
            'importance_level': 'P1', 'sla': '99.9%', 'dr_level': '同城双活',
            'change_policy': 'single', 'domain': 'sso.xxx.com',
            'tags': ['认证', '基础支撑'], 'doc_url': 'https://wiki.xxx.com/user-center',
        },
    ]
    count = 0
    for a in apps_data:
        _, created = Application.objects.update_or_create(name=a['name'], defaults=a)
        count += created
    print(f'✅ 创建了 {count} 个新应用（共 {Application.objects.count()} 个）')


def create_environments():
    """为每个应用创建环境（dev/prod，不同云账号与地域，体现"环境=位置切片"）"""
    from cmdb.models import Application, CloudAccount, Environment

    account = CloudAccount.objects.filter(provider_type='mock').first()
    env_configs = {
        '订单中心': [
            ('dev', 'dev', 'cn-hangzhou', '开发环境：Mock 数据库，依赖精简'),
            ('prod', 'prod', 'us-east-1', '生产环境：RDS/缓存/消息队列全量依赖'),
        ],
        '支付中心': [
            ('dev', 'dev', 'cn-shanghai', '开发环境'),
            ('prod', 'prod', 'us-east-1', '生产环境：强监管依赖'),
        ],
        '用户中心': [
            ('dev', 'dev', 'cn-hangzhou', '开发环境'),
            ('prod', 'prod', 'cn-beijing', '生产环境'),
        ],
    }
    count = 0
    for app in Application.objects.all():
        for name, etype, region, desc in env_configs.get(app.name, []):
            _, created = Environment.objects.get_or_create(
                application=app, name=name,
                defaults={
                    'env_type': etype,
                    'account': account,
                    'region': region,
                    'description': desc,
                    'enabled': True,
                },
            )
            count += created
    print(f'✅ 创建了 {count} 个新环境（共 {Environment.objects.count()} 个）')


TOPOLOGY = {
    '订单中心': {
        'dev': {
            'services': [
                {'name': '前端', 'stype': 'frontend', 'dtype': 'ec2', 'domain': '', 'port': 8080, 'is_public': False, 'instances': 1},
                {'name': '后端', 'stype': 'backend', 'dtype': 'ec2', 'domain': '', 'port': 8080, 'is_public': False, 'instances': 1},
            ],
            'deps': ['gateway', 'database', 'cache'],
            'links': [
                ('gateway', 'communicates_with', '前端', 'hard'),
                ('前端', 'communicates_with', '后端', 'hard'),
                ('后端', 'depends_on', 'database', 'hard'),
                ('后端', 'depends_on', 'cache', 'soft'),
            ],
        },
        'prod': {
            'services': [
                {'name': '前端', 'stype': 'frontend', 'dtype': 'ec2', 'domain': 'order.xxx.com', 'port': 443, 'is_public': True, 'instances': 2},
                {'name': '后端', 'stype': 'backend', 'dtype': 'ec2', 'domain': '', 'port': 8080, 'is_public': False, 'instances': 3},
                {'name': 'Worker', 'stype': 'worker', 'dtype': 'eks', 'domain': '', 'port': 0, 'is_public': False, 'instances': 0},
            ],
            'deps': ['gateway', 'database', 'cache', 'message_queue', 'object_storage', 'cluster'],
            'links': [
                ('gateway', 'communicates_with', '前端', 'hard'),
                ('前端', 'communicates_with', '后端', 'hard'),
                ('后端', 'depends_on', 'database', 'hard'),
                ('后端', 'depends_on', 'cache', 'soft'),
                ('后端', 'depends_on', 'message_queue', 'hard'),
                ('后端', 'depends_on', 'object_storage', 'soft'),
                ('Worker', 'depends_on', 'message_queue', 'hard'),
            ],
        },
    },
    '支付中心': {
        'dev': {
            'services': [
                {'name': '支付网关', 'stype': 'backend', 'dtype': 'ec2', 'domain': '', 'port': 8080, 'is_public': False, 'instances': 1},
            ],
            'deps': ['gateway', 'database'],
            'links': [('支付网关', 'depends_on', 'database', 'hard')],
        },
        'prod': {
            'services': [
                {'name': '支付网关', 'stype': 'backend', 'dtype': 'ec2', 'domain': 'pay.xxx.com', 'port': 443, 'is_public': True, 'instances': 2},
                {'name': '账务处理', 'stype': 'worker', 'dtype': 'ec2', 'domain': '', 'port': 0, 'is_public': False, 'instances': 1},
            ],
            'deps': ['gateway', 'database', 'message_queue', 'object_storage'],
            'links': [
                ('gateway', 'communicates_with', '支付网关', 'hard'),
                ('支付网关', 'depends_on', 'database', 'hard'),
                ('支付网关', 'depends_on', 'message_queue', 'hard'),
                ('账务处理', 'depends_on', 'message_queue', 'hard'),
            ],
        },
    },
    '用户中心': {
        'dev': {
            'services': [
                {'name': '认证服务', 'stype': 'backend', 'dtype': 'ec2', 'domain': '', 'port': 8080, 'is_public': False, 'instances': 1},
            ],
            'deps': ['gateway', 'database'],
            'links': [('认证服务', 'depends_on', 'database', 'hard')],
        },
        'prod': {
            'services': [
                {'name': '认证服务', 'stype': 'backend', 'dtype': 'ec2', 'domain': 'sso.xxx.com', 'port': 443, 'is_public': True, 'instances': 2},
            ],
            'deps': ['gateway', 'database', 'cache'],
            'links': [
                ('gateway', 'communicates_with', '认证服务', 'hard'),
                ('认证服务', 'depends_on', 'database', 'hard'),
                ('认证服务', 'depends_on', 'cache', 'soft'),
            ],
        },
    },
}

DEP_SPECS = {
    'gateway': {'rtype': 'gateway', 'suffix': 'API网关', 'port': '80/443', 'spec': 'ALB', 'managed_by': 'cloud'},
    'database': {'rtype': 'database', 'suffix': '数据库', 'port': '3306', 'spec': 'db.r5.large', 'managed_by': 'cloud'},
    'cache': {'rtype': 'cache', 'suffix': '缓存', 'port': '6379', 'spec': 'redis.m6.large', 'managed_by': 'cloud'},
    'message_queue': {'rtype': 'message_queue', 'suffix': '消息总线', 'port': '9092', 'spec': 'kafka.m7.xlarge', 'managed_by': 'cloud'},
    'object_storage': {'rtype': 'object_storage', 'suffix': '对象存储', 'port': '443', 'spec': 's3-standard', 'managed_by': 'cloud'},
    'cluster': {'rtype': 'cluster', 'suffix': 'K8s集群', 'port': '6443', 'spec': 'eks-cluster', 'managed_by': 'cloud'},
}


def _reset_env_topology(app, env):
    """重置环境下的种子拓扑数据（服务/依赖资源/关系），保证 seed 幂等"""
    from cmdb.models import Resource, ResourceRelation, ServiceEndpoint, ServiceInstance

    svc_ids = list(ServiceInstance.objects.filter(application=app, environment=env).values_list('id', flat=True))
    ServiceEndpoint.objects.filter(service_id__in=svc_ids).delete()
    ServiceInstance.objects.filter(id__in=svc_ids).delete()
    seed_ids = list(Resource.objects.filter(environment=env, source__in=(1, 2)).values_list('id', flat=True))
    ResourceRelation.objects.filter(source_id__in=seed_ids).delete()
    ResourceRelation.objects.filter(target_id__in=seed_ids).delete()
    Resource.objects.filter(id__in=seed_ids).delete()
    Resource.objects.filter(environment=env, application=app, source=0).update(environment=None, application=None)


def create_app_topology():
    """按环境重建应用拓扑：服务(多实例) / 资源(网关·数据库·缓存·消息·存储·集群) / 依赖关系"""
    from cmdb.models import Application, CloudAccount, Resource, ResourceRelation, ServiceEndpoint, ServiceInstance

    account = CloudAccount.objects.filter(provider_type='mock').first()
    instance_pool = list(Resource.objects.filter(
        resource_type='instance', is_deleted=False, environment__isnull=True
    ).order_by('id'))
    pool_idx = 0

    def take_instance():
        nonlocal pool_idx
        if pool_idx >= len(instance_pool):
            pool_idx = 0
        inst = instance_pool[pool_idx]
        pool_idx += 1
        return inst

    def link(src_res, tgt_res, rtype, strength):
        if not src_res or not tgt_res or src_res.id == tgt_res.id:
            return
        ResourceRelation.objects.get_or_create(
            source=src_res, target=tgt_res, relation_type=rtype,
            defaults={'strength': strength, 'relation_source': 'manual'},
        )

    count = 0
    for app in Application.objects.all():
        for env in app.environments.all():
            config = TOPOLOGY.get(app.name, {}).get(env.name)
            if not config:
                continue
            _reset_env_topology(app, env)

            # 创建依赖资源（网关/数据库/缓存/消息/存储/集群）
            deps = {}
            for dep_key in config['deps']:
                spec = DEP_SPECS[dep_key]
                cloud_id = f'dep-{dep_key}-{app.id}-{env.id}'
                res, _ = Resource.objects.get_or_create(
                    cloud_resource_id=cloud_id,
                    defaults={
                        'account': account,
                        'provider_type': 'mock',
                        'resource_type': spec['rtype'],
                        'resource_name': f'{app.name}-{env.name}-{spec["suffix"]}',
                        'region': env.region,
                        'status': 'available',
                        'spec': spec['spec'],
                        'metadata': {'dep_key': dep_key, 'port': spec['port'], 'service': dep_key},
                        'source': 2,
                        'source_system': 'manual',
                        'sync_mode': 'manual',
                    },
                )
                res.environment = env
                res.application = app
                # 演示"自建资源"：dev 环境数据库为自建 MySQL
                res.managed_by = 'self' if (env.name == 'dev' and dep_key == 'database') else spec['managed_by']
                res.save(update_fields=['environment', 'application', 'managed_by', 'updated_at'])
                deps[dep_key] = res

            cluster = deps.get('cluster')
            svc_by_name = {}
            for s in config['services']:
                insts = []
                if s['instances']:
                    for _ in range(s['instances']):
                        inst = take_instance()
                        inst.application = app
                        inst.environment = env
                        inst.region = env.region
                        inst.save(update_fields=['application', 'environment', 'region', 'updated_at'])
                        insts.append(inst)
                elif s['dtype'] == 'eks' and cluster:
                    insts = [cluster]

                svc, _ = ServiceInstance.objects.get_or_create(
                    application=app, environment=env, name=s['name'],
                    defaults={
                        'resource': insts[0] if insts else None,
                        'service_type': s['stype'],
                        'deploy_type': s['dtype'],
                        'region': env.region,
                        'status': 'running',
                        'owner': app.owner,
                        'description': f'{app.name} - {env.name} - {s["name"]}',
                    },
                )
                svc.resource = insts[0] if insts else None
                svc.save()
                svc.resources.set(insts)
                svc_by_name[s['name']] = svc
                if s['domain']:
                    ServiceEndpoint.objects.get_or_create(
                        service=svc, protocol='https' if s['is_public'] else 'http',
                        defaults={'port': s['port'], 'domain': s['domain'],
                                  'is_public': s['is_public'],
                                  'certificate': '*.xxx.com' if s['is_public'] else ''},
                    )
                count += 1

            # 依赖关系（资源级：实例/网关 → 数据资源）
            for src_name, rtype, tgt_name, strength in config['links']:
                src_res = None
                if src_name == 'gateway':
                    src_res = deps.get('gateway')
                elif src_name in svc_by_name:
                    src_res = svc_by_name[src_name].resource
                tgt_res = None
                if tgt_name in deps:
                    tgt_res = deps[tgt_name]
                elif tgt_name in svc_by_name:
                    tgt_res = svc_by_name[tgt_name].resource
                link(src_res, tgt_res, rtype, strength)

    print(f'✅ 重建应用拓扑：{ServiceInstance.objects.count()} 个服务，'
          f'{ServiceEndpoint.objects.count()} 个端点，'
          f'{ResourceRelation.objects.count()} 条资源关系')


def create_security_rules():
    """为安全组生成规则（支撑网络连通性推导）"""
    from cmdb.models import Resource, SecurityRule

    sgs = Resource.objects.filter(resource_type='security_group', is_deleted=False)
    count = 0
    for sg in sgs[:12]:
        defaults_list = [
            {'direction': 'inbound', 'protocol': 'tcp', 'port_range': '80',
             'source': '0.0.0.0/0', 'priority': 100},
            {'direction': 'inbound', 'protocol': 'tcp', 'port_range': '443',
             'source': '0.0.0.0/0', 'priority': 100},
            {'direction': 'inbound', 'protocol': 'tcp', 'port_range': '8080',
             'source': '10.0.0.0/8', 'priority': 110},
        ]
        for d in defaults_list:
            _, created = SecurityRule.objects.get_or_create(
                security_group=sg, direction=d['direction'], protocol=d['protocol'],
                port_range=d['port_range'], source=d['source'],
                defaults={'priority': d['priority'], 'action': 'allow', 'enabled': True},
            )
            count += created
    print(f'✅ 创建了 {count} 条安全组规则（共 {SecurityRule.objects.count()} 条）')


def create_scenarios():
    """创建场景定义（服务扩容 / 安全组变更）"""
    from scenario.models import Scenario, ScenarioStep

    scale_out, _ = Scenario.objects.get_or_create(
        code='service_scale_out',
        defaults={
            'name': '服务扩容',
            'description': '为服务新增机器并完成网络打通、环境初始化、数据落库与发布推送',
            'icon': '🚀',
            'need_approval': True,
            'version': 'v1',
        },
    )
    scale_steps = [
        (1, '申请机器', 'create_instance', {'name': '扩容实例', 'region': 'cn-hangzhou',
                                           'spec': 't3.large'}, []),
        (2, '新建子网', 'create_subnet', {'cidr': '10.20.0.0/24'}, [1]),
        (3, '新建安全组', 'create_security_group', {'name': '扩容安全组'}, [2]),
        (4, '绑定安全组', 'attach_security_group', {}, [3]),
        (5, '网络打通', 'allow_network', {'port_range': '80,443'}, [4]),
        (6, '环境初始化', 'init_env', {'init_steps': ['安装依赖', '写入配置', '启动服务']}, [5]),
        (7, '数据落库', 'write_cmdb', {}, [6]),
        (8, '推送发布平台', 'publish_platform', {}, [7]),
    ]
    for step_no, name, action_type, template, depends in scale_steps:
        ScenarioStep.objects.update_or_create(
            scenario=scale_out, step_no=step_no,
            defaults={
                'name': name, 'action_type': action_type,
                'action_params_template': template,
                'depends_on': depends, 'retry_max': 3, 'enabled': True,
                'skip_if_missing': [],
            },
        )

    sg_change, _ = Scenario.objects.get_or_create(
        code='sg_quick_change',
        defaults={
            'name': '安全组变更',
            'description': '快速新建安全组并完成绑定与网络放行',
            'icon': '🛡️',
            'need_approval': True,
            'version': 'v1',
        },
    )
    sg_steps = [
        (1, '新建安全组', 'create_security_group', {'name': '变更安全组'}, []),
        (2, '绑定安全组', 'attach_security_group', {}, [1], ['instance_id']),
        (3, '网络打通', 'allow_network', {'port_range': '443'}, [2], []),
    ]
    for step in sg_steps:
        step_no, name, action_type, template, depends = step[:5]
        skip_if_missing = step[5] if len(step) > 5 else []
        ScenarioStep.objects.update_or_create(
            scenario=sg_change, step_no=step_no,
            defaults={
                'name': name, 'action_type': action_type,
                'action_params_template': template,
                'depends_on': depends, 'retry_max': 3, 'enabled': True,
                'skip_if_missing': skip_if_missing,
            },
        )
    print(f'✅ 创建了 {Scenario.objects.count()} 个场景，'
          f'{ScenarioStep.objects.count()} 个场景步骤')


def create_ticket_samples():
    """创建工单样本数据（5-10条，覆盖各状态和类型）"""
    from ticket.models import TicketOrder, TicketApproval, TicketTask
    from cmdb.models import Resource
    from django.utils import timezone
    from datetime import timedelta
    import uuid

    instances = Resource.objects.filter(resource_type='instance', is_deleted=False)[:5]
    if not instances.exists():
        print('⚠️ 无实例资源，跳过工单种子数据')
        return

    now = timezone.now()
    users = [
        {'name': '系统管理员', 'id': 1},
        {'name': '云管理员', 'id': 2},
        {'name': '运维工程师', 'id': 3},
    ]

    tickets_data = [
        {
            'ticket_type': 'start', 'title': '启动 web-cn-001 主机',
            'status': 'success', 'resource_idx': 0,
            'request_content': {},
            'result_content': {'task_id': f't-{uuid.uuid4().hex[:8]}', 'retry_count': 0},
            'days_ago': 5,
        },
        {
            'ticket_type': 'stop', 'title': '停止 api-cn-002 主机',
            'status': 'success', 'resource_idx': 1,
            'request_content': {},
            'result_content': {'task_id': f't-{uuid.uuid4().hex[:8]}', 'retry_count': 0},
            'days_ago': 4,
        },
        {
            'ticket_type': 'create_instance', 'title': '申请新主机 - 业务扩容',
            'status': 'success', 'resource_idx': 0,
            'request_content': {'name': 'expand-001', 'region': 'cn-hangzhou', 'spec': 't3.large', 'cpu': 4, 'memory_gb': 8},
            'result_content': {'task_id': f't-{uuid.uuid4().hex[:8]}', 'retry_count': 0},
            'days_ago': 3,
        },
        {
            'ticket_type': 'resize', 'title': '变更规格 db-cn-003 → ecs.g6.xlarge',
            'status': 'success', 'resource_idx': 2,
            'request_content': {'spec': 'ecs.g6.xlarge'},
            'result_content': {'task_id': f't-{uuid.uuid4().hex[:8]}', 'retry_count': 0},
            'days_ago': 2,
        },
        {
            'ticket_type': 'release', 'title': '下线测试主机 worker-cn-004',
            'status': 'success', 'resource_idx': 3,
            'request_content': {},
            'result_content': {'task_id': f't-{uuid.uuid4().hex[:8]}', 'retry_count': 0},
            'days_ago': 1,
        },
        {
            'ticket_type': 'start', 'title': '启动 cache-cn-005（失败重试）',
            'status': 'failed', 'resource_idx': 4,
            'request_content': {},
            'result_content': {},
            'fail_reason': '重试3次后仍失败: 连接超时',
            'days_ago': 1,
        },
        {
            'ticket_type': 'stop', 'title': '停止 gateway-us-001',
            'status': 'pending', 'resource_idx': 0,
            'request_content': {},
            'result_content': {},
            'days_ago': 0,
        },
        {
            'ticket_type': 'start', 'title': '启动 api-us-002',
            'status': 'rejected', 'resource_idx': 1,
            'request_content': {},
            'result_content': {},
            'fail_reason': '生产环境不允许随意操作',
            'days_ago': 3,
        },
    ]

    instances_list = list(instances)
    count = 0
    for i, t_data in enumerate(tickets_data):
        inst = instances_list[t_data['resource_idx'] % len(instances_list)]
        user = users[i % len(users)]
        created_at = now - timedelta(days=t_data['days_ago'])

        # 生成工单号
        day = created_at.strftime('%Y%m%d')
        prefix = f'WO{day}'
        existing = TicketOrder.objects.filter(ticket_no__startswith=prefix).count()
        seq = existing + 1
        ticket_no = f'{prefix}{seq:04d}'

        ticket, created = TicketOrder.objects.get_or_create(
            ticket_no=ticket_no,
            defaults={
                'ticket_type': t_data['ticket_type'],
                'title': t_data['title'],
                'status': t_data['status'],
                'applicant': user['name'],
                'applicant_id': user['id'],
                'resource_id': inst.cloud_resource_id,
                'resource_name': inst.resource_name,
                'provider_type': 'mock',
                'request_content': t_data['request_content'],
                'result_content': t_data['result_content'],
                'fail_reason': t_data.get('fail_reason', ''),
                'created_at': created_at,
                'updated_at': created_at,
                'finished_at': created_at if t_data['status'] in ('success', 'failed', 'rejected') else None,
            }
        )
        if not created:
            continue
        count += 1

        # 创建审批记录（非 pending 状态的工单）
        if t_data['status'] not in ('pending',):
            action = 1 if t_data['status'] != 'rejected' else 2
            approver = users[(i + 1) % len(users)]
            TicketApproval.objects.create(
                ticket=ticket,
                approver=approver['name'],
                approver_id=approver['id'],
                action=action,
                comment='同意' if action == 1 else t_data.get('fail_reason', '驳回'),
                approved_at=created_at - timedelta(hours=1),
            )

        # 创建执行任务（success/failed 状态的工单）
        if t_data['status'] in ('success', 'failed', 'running'):
            task_status = 'success' if t_data['status'] == 'success' else 'failed'
            TicketTask.objects.create(
                ticket=ticket,
                task_type=t_data['ticket_type'],
                provider_type='mock',
                status=task_status,
                retry_count=3 if t_data['status'] == 'failed' else 0,
                max_retry=3,
                request_id=str(uuid.uuid4()),
                exec_log=f'[{t_data["status"]}] Mock Provider 执行{"成功" if task_status == "success" else "失败"}',
                started_at=created_at - timedelta(minutes=30),
                finished_at=created_at - timedelta(minutes=29) if task_status == 'success' else created_at,
            )

    print(f'✅ 创建了 {count} 条工单样本（共 {TicketOrder.objects.count()} 条）')


def main():
    print('=' * 50)
    print('🌱 开始创建种子数据...')
    print('=' * 50)

    dept_objs = create_departments()
    role_objs = create_roles()
    perm_objs = create_permissions()
    assign_role_permissions(role_objs, perm_objs)
    create_users(dept_objs, role_objs)
    create_cloud_accounts()
    create_mock_resources()
    create_resource_relations()
    create_applications()
    create_environments()
    create_app_topology()
    create_security_rules()
    create_service_catalog()
    create_cost_data()
    create_scenarios()
    create_ticket_samples()

    print('=' * 50)
    print('🎉 种子数据创建完成！')
    print()
    print('📋 演示账号：')
    print('  admin / admin123 (超级管理员)')
    print('  cloud_admin / admin123 (云管理员)')
    print('  ops_user / admin123 (运维工程师)')
    print('  readonly / admin123 (只读用户)')
    print('=' * 50)


if __name__ == '__main__':
    main()
