"""
种子数据初始化命令
用法: python manage.py seed_data
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.accounts.models import Department
from apps.capabilities.models import Capability
from apps.processes.models import ProcessDefinition
from apps.processes.models import InitiatorApp
from apps.processes.services.security import hash_api_key
from apps.tickets.models import TicketType

User = get_user_model()


class Command(BaseCommand):
    help = '初始化种子数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化种子数据...')

        # 1. 创建部门
        tech_dept = Department.objects.create(name='技术部')
        it_ops = Department.objects.create(name='IT运维组', parent=tech_dept)
        dev_dept = Department.objects.create(name='研发组', parent=tech_dept)
        finance_dept = Department.objects.create(name='财务部')

        self.stdout.write(self.style.SUCCESS('✓ 部门创建完成'))

        # 2. 创建角色
        admin_group, _ = Group.objects.get_or_create(name='admin')
        agent_group, _ = Group.objects.get_or_create(name='agent')
        user_group, _ = Group.objects.get_or_create(name='user')

        self.stdout.write(self.style.SUCCESS('✓ 角色创建完成'))

        # 3. 创建用户
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'first_name': '管理员', 'department': tech_dept, 'is_staff': True, 'is_superuser': True, 'group': admin_group},
            {'username': 'xiaoming', 'password': 'user123', 'first_name': '小明', 'department': dev_dept, 'group': user_group},
            {'username': 'xiaohong', 'password': 'user123', 'first_name': '小红', 'department': dev_dept, 'group': user_group},
            {'username': 'xiaohuang', 'password': 'user123', 'first_name': '小黄', 'department': dev_dept, 'group': user_group},
            {'username': 'xiaoli', 'password': 'user123', 'first_name': '小李', 'department': it_ops, 'group': user_group},
            {'username': 'xiaowang', 'password': 'user123', 'first_name': '小王', 'department': it_ops, 'group': user_group},
            {'username': 'xiaozhang', 'password': 'user123', 'first_name': '小张', 'department': finance_dept, 'group': user_group},
            {'username': 'xiaozhao', 'password': 'user123', 'first_name': '小赵', 'department': finance_dept, 'group': user_group},
        ]

        users = {}
        for ud in users_data:
            group = ud.pop('group')
            user, created = User.objects.get_or_create(
                username=ud['username'],
                defaults=ud,
            )
            if created:
                user.set_password(ud['password'])
                user.save()
            user.groups.add(group)
            users[ud['username']] = user

        # 设置部门主管
        it_ops.manager = users['xiaoli']
        it_ops.save()
        tech_dept.manager = users['admin']
        tech_dept.save()
        finance_dept.manager = users['xiaozhang']
        finance_dept.save()

        self.stdout.write(self.style.SUCCESS('✓ 用户创建完成'))

        # 4. 创建能力
        capabilities_data = [
            {
                'code': 'cmdb.create_host',
                'name': 'CMDB 创建主机',
                'description': '在 CMDB 系统中创建主机记录',
                'execute_mode': 'async',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'hostname': {'type': 'string', 'title': '主机名'},
                        'cpu': {'type': 'integer', 'title': 'CPU 核数'},
                        'memory': {'type': 'integer', 'title': '内存(GB)'},
                        'os': {'type': 'string', 'title': '操作系统'},
                    },
                    'required': ['hostname'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'host_id': {'type': 'string'},
                        'ip': {'type': 'string'},
                        'status': {'type': 'string'},
                    },
                },
            },
            {
                'code': 'cmdb.restart_host',
                'name': 'CMDB 重启主机',
                'description': '在 CMDB 系统中重启指定主机',
                'execute_mode': 'async',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'hostname': {'type': 'string', 'title': '主机名'},
                        'restart_type': {'type': 'string', 'title': '重启类型', 'enum': ['system', 'service', 'hard']},
                    },
                    'required': ['hostname'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'task_id': {'type': 'string'},
                        'status': {'type': 'string'},
                        'message': {'type': 'string'},
                    },
                },
            },
            {
                'code': 'dns.add_record',
                'name': 'DNS 添加记录',
                'description': '在 DNS 服务器中添加解析记录',
                'execute_mode': 'sync',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'domain': {'type': 'string', 'title': '域名'},
                        'record_type': {'type': 'string', 'title': '记录类型', 'enum': ['A', 'CNAME', 'MX']},
                        'record_value': {'type': 'string', 'title': '记录值'},
                        'ttl': {'type': 'integer', 'title': 'TTL'},
                    },
                    'required': ['domain', 'record_type', 'record_value'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'record_id': {'type': 'string'},
                        'status': {'type': 'string'},
                    },
                },
            },
            {
                'code': 'mail.send',
                'name': '邮件发送',
                'description': '发送邮件通知',
                'execute_mode': 'sync',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'to': {'type': 'array', 'items': {'type': 'string'}, 'title': '收件人'},
                        'subject': {'type': 'string', 'title': '主题'},
                        'body': {'type': 'string', 'title': '正文'},
                    },
                    'required': ['to', 'subject', 'body'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'message_id': {'type': 'string'},
                        'status': {'type': 'string'},
                    },
                },
            },
            {
                'code': 'external.approve',
                'name': '外部审批',
                'description': '调用外部审批系统',
                'execute_mode': 'async',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'title': '审批标题'},
                        'content': {'type': 'string', 'title': '审批内容'},
                        'approver': {'type': 'string', 'title': '审批人'},
                    },
                    'required': ['title'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'approval_id': {'type': 'string'},
                        'status': {'type': 'string'},
                    },
                },
            },
            {
                'code': 'permission.center.grant',
                'name': '权限中心授权',
                'description': '调用权限中心系统进行权限开通',
                'execute_mode': 'async',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'system': {'type': 'string', 'title': '目标系统'},
                        'account': {'type': 'string', 'title': '目标账号'},
                        'permission_level': {'type': 'string', 'title': '权限级别'},
                        'permission_scope': {'type': 'string', 'title': '权限范围'},
                        'duration_type': {'type': 'string', 'title': '有效期类型'},
                        'duration_days': {'type': 'integer', 'title': '有效天数'},
                    },
                    'required': ['system', 'account', 'permission_level'],
                },
                'output_schema': {
                    'type': 'object',
                    'properties': {
                        'grant_id': {'type': 'string'},
                        'status': {'type': 'string'},
                        'expire_at': {'type': 'string'},
                    },
                },
            },
        ]

        for cap_data in capabilities_data:
            Capability.objects.get_or_create(
                code=cap_data['code'],
                defaults=cap_data,
            )

        self.stdout.write(self.style.SUCCESS('✓ 能力创建完成'))

        # 5. 创建工单类型
        TicketType.objects.get_or_create(
            code='server_apply',
            defaults={
                'name': '服务器申请',
                'description': '申请新的服务器资源',
            },
        )
        TicketType.objects.get_or_create(
            code='permission_apply',
            defaults={
                'name': '权限开通',
                'description': '申请系统权限开通',
            },
        )
        TicketType.objects.get_or_create(
            code='new_service_apply',
            defaults={
                'name': '新增服务申请',
                'description': '申请新增服务部署',
            },
        )
        TicketType.objects.get_or_create(
            code='server_restart',
            defaults={
                'name': '服务器重启',
                'description': '申请重启服务器',
            },
        )

        self.stdout.write(self.style.SUCCESS('✓ 工单类型创建完成'))

        # 6. 创建演示发起程序
        apps_data = [
            {
                'code': 'cmdb_sync',
                'name': 'CMDB 资产同步',
                'api_key': 'demo_cmdb_sync_key_2026',
                'description': '资产系统自动发起服务器申请',
            },
            {
                'code': 'it_service',
                'name': 'IT 服务台',
                'api_key': 'demo_it_service_key_2026',
                'description': '服务台代为提单',
            },
            {
                'code': 'permission_center',
                'name': '权限中心',
                'api_key': 'demo_permission_center_key_2026',
                'description': '权限中心自动发起权限开通',
            },
            {
                'code': 'cloud_manager',
                'name': '云管平台',
                'api_key': 'demo_cloud_manager_key_2026',
                'description': '云管平台自动发起服务与重启',
            },
        ]
        initiator_apps = {}
        for ad in apps_data:
            app, created = InitiatorApp.objects.get_or_create(
                code=ad['code'],
                defaults={
                    'name': ad['name'],
                    'api_key_hash': hash_api_key(ad['api_key']),
                    'is_active': True,
                },
            )
            if created:
                self.stdout.write(f"  API Key（仅展示一次）: {ad['code']} = {ad['api_key']}")
            initiator_apps[ad['code']] = app

        self.stdout.write(self.style.SUCCESS('✓ 发起程序创建完成'))

        # 7. 获取用户和能力对象
        xiaoli = User.objects.get(username='xiaoli')
        xiaoming = User.objects.get(username='xiaoming')
        xiaohong = User.objects.get(username='xiaohong')
        xiaowang = User.objects.get(username='xiaowang')
        admin_user = User.objects.get(username='admin')
        cmdb_cap = Capability.objects.get(code='cmdb.create_host')
        restart_cap = Capability.objects.get(code='cmdb.restart_host')
        mail_cap = Capability.objects.get(code='mail.send')
        dns_cap = Capability.objects.get(code='dns.add_record')
        perm_cap = Capability.objects.get(code='permission.center.grant')
        external_approve_cap = Capability.objects.get(code='external.approve')
        # 办理节点默认办理人（Demo：Admin + 若干成员，≥2 组，保证「流程建模」检查可通过）
        auto_transactors = [
            {"rid": "t_admin", "transactorType": 4, "assignees": [admin_user.id]},
            {"rid": "t_ops", "transactorType": 4, "assignees": [xiaoming.id, xiaohong.id, xiaowang.id]},
        ]

        # ====================================================================
        # 表单定义
        # ====================================================================
        server_apply_form = {
            "rules": [
                {"type": "input", "field": "hostname", "title": "主机名", "validate": [{"required": True}], "props": {"placeholder": "如 web-prod-01"}},
                {"type": "select", "field": "os", "title": "操作系统", "validate": [{"required": True}], "options": [
                    {"label": "CentOS 7.9", "value": "CentOS 7.9"},
                    {"label": "Ubuntu 22.04 LTS", "value": "Ubuntu 22.04 LTS"},
                    {"label": "Debian 12", "value": "Debian 12"},
                    {"label": "Windows Server 2022", "value": "Windows Server 2022"}
                ]},
                {"type": "inputNumber", "field": "cpu", "title": "CPU 核数", "value": 4, "validate": [{"required": True}], "props": {"min": 1, "max": 128}},
                {"type": "inputNumber", "field": "memory", "title": "内存 (GB)", "value": 8, "validate": [{"required": True}], "props": {"min": 1, "max": 512}},
                {"type": "inputNumber", "field": "disk_size", "title": "系统盘 (GB)", "value": 50, "validate": [{"required": True}], "props": {"min": 20, "max": 2000}},
                {"type": "inputNumber", "field": "data_disk_size", "title": "数据盘 (GB)", "props": {"min": 0, "max": 10000}},
                {"type": "select", "field": "zone", "title": "可用区", "options": [
                    {"label": "华东1（杭州）", "value": "cn-hangzhou"},
                    {"label": "华北2（北京）", "value": "cn-beijing"},
                    {"label": "华南1（深圳）", "value": "cn-shenzhen"}
                ]},
                {"type": "inputNumber", "field": "quantity", "title": "申请数量", "value": 1, "props": {"min": 1, "max": 50}},
                {"type": "input", "field": "network_segment", "title": "网段要求", "props": {"placeholder": "如 10.0.1.0/24（可选）"}},
                {"type": "input", "field": "email", "title": "通知邮箱", "validate": [{"required": True}], "props": {"placeholder": "接收创建通知的邮箱"}},
                {"type": "textarea", "field": "reason", "title": "申请理由", "validate": [{"required": True}], "props": {"placeholder": "请描述申请服务器的用途和必要性"}},
            ],
            "options": {"labelWidth": 120}
        }

        permission_apply_form = {
            "rules": [
                {"type": "select", "field": "system", "title": "目标系统", "validate": [{"required": True}], "options": [
                    {"label": "CMDB 数据平台", "value": "cmdb_platform"},
                    {"label": "云管平台", "value": "cloud_manager"}
                ]},
                {"type": "input", "field": "account", "title": "目标账号", "validate": [{"required": True}], "props": {"placeholder": "请输入用户名或工号"}},
                {"type": "select", "field": "permission_level", "title": "权限级别", "validate": [{"required": True}], "options": [
                    {"label": "只读", "value": "readonly"},
                    {"label": "普通操作", "value": "normal"},
                    {"label": "管理员", "value": "admin"},
                    {"label": "超级管理员", "value": "superadmin"}
                ]},
                {"type": "textarea", "field": "permission_scope", "title": "权限范围", "validate": [{"required": True}], "props": {"placeholder": "请描述需要的具体模块和操作权限"}},
                {"type": "select", "field": "duration_type", "title": "有效期类型", "validate": [{"required": True}], "options": [
                    {"label": "长期有效", "value": "permanent"},
                    {"label": "临时", "value": "temporary"}
                ]},
                {"type": "inputNumber", "field": "duration_days", "title": "临时有效天数", "props": {"min": 1, "max": 365}, "display": "$.duration_type === 'temporary'"},
                {"type": "input", "field": "notify_email", "title": "通知邮箱", "validate": [{"required": True}], "props": {"placeholder": "接收开通通知的邮箱"}},
                {"type": "textarea", "field": "reason", "title": "申请理由", "validate": [{"required": True}], "props": {"placeholder": "请描述权限开通的业务原因"}},
            ],
            "options": {"labelWidth": 120}
        }

        new_service_apply_form = {
            "rules": [
                {"type": "input", "field": "service_name", "title": "服务名称", "validate": [{"required": True}], "props": {"placeholder": "如 user-api、order-service"}},
                {"type": "select", "field": "service_type", "title": "服务类型", "validate": [{"required": True}], "options": [
                    {"label": "Web 应用", "value": "web"},
                    {"label": "API 服务", "value": "api"},
                    {"label": "消息队列", "value": "mq"},
                    {"label": "数据库", "value": "database"},
                    {"label": "缓存服务", "value": "cache"},
                    {"label": "定时任务", "value": "cron"}
                ]},
                {"type": "select", "field": "environment", "title": "部署环境", "validate": [{"required": True}], "options": [
                    {"label": "测试环境", "value": "test"},
                    {"label": "预发环境", "value": "staging"},
                    {"label": "生产环境", "value": "production"}
                ]},
                {"type": "select", "field": "language_runtime", "title": "语言/运行时", "options": [
                    {"label": "Java 17", "value": "java17"},
                    {"label": "Go 1.22", "value": "go122"},
                    {"label": "Python 3.12", "value": "python312"},
                    {"label": "Node.js 20", "value": "node20"},
                    {"label": "其他", "value": "other"}
                ]},
                {"type": "textarea", "field": "resource_request", "title": "资源需求", "validate": [{"required": True}], "props": {"placeholder": "请描述 CPU/内存/磁盘预估需求"}},
                {"type": "textarea", "field": "dependency", "title": "服务依赖", "props": {"placeholder": "请列出依赖的其他服务（可选）"}},
                {"type": "input", "field": "domain_request", "title": "域名需求", "props": {"placeholder": "如 api.example.com（可选）"}},
                {"type": "switch", "field": "db_required", "title": "需要数据库"},
                {"type": "select", "field": "db_type", "title": "数据库类型", "display": "$.db_required", "options": [
                    {"label": "MySQL 8.0", "value": "mysql"},
                    {"label": "PostgreSQL 16", "value": "postgresql"},
                    {"label": "MongoDB 7", "value": "mongodb"},
                    {"label": "Redis 7", "value": "redis"}
                ]},
                {"type": "datePicker", "field": "expected_date", "title": "预期上线时间", "validate": [{"required": True}], "props": {"type": "date"}},
                {"type": "input", "field": "notify_email", "title": "通知邮箱", "validate": [{"required": True}], "props": {"placeholder": "接收部署通知的邮箱"}},
                {"type": "textarea", "field": "reason", "title": "申请理由", "validate": [{"required": True}], "props": {"placeholder": "请描述新增服务的业务背景和必要性"}},
            ],
            "options": {"labelWidth": 120}
        }

        server_restart_form = {
            "rules": [
                {"type": "input", "field": "hostname", "title": "主机名", "validate": [{"required": True}], "props": {"placeholder": "请输入需要重启的主机名"}},
                {"type": "select", "field": "restart_type", "title": "重启类型", "validate": [{"required": True}], "options": [
                    {"label": "系统重启", "value": "system"},
                    {"label": "服务重启", "value": "service"},
                    {"label": "硬重启（强制）", "value": "hard"}
                ]},
                {"type": "textarea", "field": "reason", "title": "重启原因", "validate": [{"required": True}], "props": {"placeholder": "请描述重启原因"}},
                {"type": "select", "field": "urgency", "title": "紧急程度", "validate": [{"required": True}], "options": [
                    {"label": "普通", "value": "normal"},
                    {"label": "紧急", "value": "urgent"}
                ]},
                {"type": "inputNumber", "field": "downtime_expected", "title": "预计停机时长(分钟)", "props": {"min": 0, "max": 1440}},
                {"type": "textarea", "field": "notify_list", "title": "通知人员", "props": {"placeholder": "请输入需要通知的邮箱，多个用逗号分隔"}},
            ],
            "options": {"labelWidth": 140}
        }

        # ====================================================================
        # 8. 流程定义 - 服务器申请（全员可提交 + 云管平台发起）
        # 流程：发起人 → 运维审批 → [高配?] → 部门主管审批 → 自动创建+通知 → 结束
        # Beeflow nodeConfig 树形格式（type: 0=开始 1=审批 5=办理 9=结束 4=网关 3=条件）
        # ====================================================================
        server_apply_definition = {
            "nodeConfig": {
                "key": "start",
                "name": "发起人",
                "type": 0,
                "childNode": {
                    "key": "ops_approve",
                    "name": "运维审批",
                    "type": 1,
                    "multiInstanceApprovalType": 0,
                    "assignees": [{"rid": "a1", "assigneeType": 4, "assignees": [xiaoli.id]}],
                    "childNode": {
                        "key": "config_gateway",
                        "name": "配置判断",
                        "type": 4,
                        "conditionNodes": [
                            {
                                "key": "high_config",
                                "name": "高配服务器",
                                "type": 3,
                                "priorityLevel": 1,
                                "conditionGroups": [
                                    {"conditions": [{"varName": "cpu", "operator": 2, "val": "8"}]}
                                ],
                                "childNode": {
                                    "key": "manager_approve",
                                    "name": "部门主管审批",
                                    "type": 1,
                                    "multiInstanceApprovalType": 0,
                                    "assignees": [{"rid": "a2", "assigneeType": 1, "layer": 0, "layerType": 0}],
                                    "childNode": {
                                        "key": "auto_create",
                                        "name": "自动创建主机",
                                        "type": 5,
                                        "transactors": auto_transactors,
                                        "taskConfig": {
                                            "mode": "auto",
                                            "executionMode": "sequential",
                                            "actions": [
                                                {
                                                    "key": "act_create_host",
                                                    "name": "创建主机",
                                                    "capabilityId": cmdb_cap.id,
                                                    "capabilityCode": "cmdb.create_host",
                                                    "fieldBindings": [
                                                        {"capabilityField": "hostname", "capabilityType": "string", "source": "form", "formField": "hostname"},
                                                        {"capabilityField": "cpu", "capabilityType": "integer", "source": "form", "formField": "cpu"},
                                                        {"capabilityField": "memory", "capabilityType": "integer", "source": "form", "formField": "memory"},
                                                        {"capabilityField": "os", "capabilityType": "string", "source": "form", "formField": "os"},
                                                    ],
                                                },
                                                {
                                                    "key": "act_send_notify",
                                                    "name": "发送创建通知",
                                                    "capabilityId": mail_cap.id,
                                                    "capabilityCode": "mail.send",
                                                    "fieldBindings": [
                                                        {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "email"},
                                                        {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "服务器创建完成通知"},
                                                        {"capabilityField": "body", "capabilityType": "string", "source": "constant", "constant": "您申请的服务器已创建完成，请查收。"},
                                                    ],
                                                },
                                            ],
                                        },
                                        "childNode": {"key": "end1", "name": "结束", "type": 9, "childNode": None}
                                    }
                                }
                            },
                            {
                                "key": "normal_config",
                                "name": "普通配置",
                                "type": 3,
                                "priorityLevel": 2,
                                "conditionGroups": [],
                                "childNode": {
                                    "key": "auto_create2",
                                    "name": "自动创建主机",
                                    "type": 5,
                                    "transactors": auto_transactors,
                                    "taskConfig": {
                                        "mode": "auto",
                                        "executionMode": "sequential",
                                        "actions": [
                                            {
                                                "key": "act_create_host2",
                                                "name": "创建主机",
                                                "capabilityId": cmdb_cap.id,
                                                "capabilityCode": "cmdb.create_host",
                                                "fieldBindings": [
                                                    {"capabilityField": "hostname", "capabilityType": "string", "source": "form", "formField": "hostname"},
                                                    {"capabilityField": "cpu", "capabilityType": "integer", "source": "form", "formField": "cpu"},
                                                    {"capabilityField": "memory", "capabilityType": "integer", "source": "form", "formField": "memory"},
                                                    {"capabilityField": "os", "capabilityType": "string", "source": "form", "formField": "os"},
                                                ],
                                            },
                                            {
                                                "key": "act_send_notify2",
                                                "name": "发送创建通知",
                                                "capabilityId": mail_cap.id,
                                                "capabilityCode": "mail.send",
                                                "fieldBindings": [
                                                    {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "email"},
                                                    {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "服务器创建完成通知"},
                                                    {"capabilityField": "body", "capabilityType": "string", "source": "constant", "constant": "您申请的服务器已创建完成，请查收。"},
                                                ],
                                            },
                                        ],
                                    },
                                    "childNode": {"key": "end2", "name": "结束", "type": 9, "childNode": None}
                                }
                            }
                        ],
                        "childNode": None
                    }
                }
            },
            "workFlowDef": {"id": "wf_server_apply", "icon": "server", "name": "申请服务器", "cancelable": 1},
            "flowPermission": {"type": 0, "flowInitiators": []},
        }

        ProcessDefinition.objects.get_or_create(
            key='server_apply',
            defaults={
                'name': '申请服务器',
                'version': 1,
                'status': 'published',
                'category': 'it',
                'submit_scope': 'all',
                'allow_program_initiate': True,
                'initiator_app_ids': [initiator_apps['cloud_manager'].id],
                'definition_json': server_apply_definition,
                'form_schema': server_apply_form,
                'created_by': admin_user,
            },
        )

        # ====================================================================
        # 9. 流程定义 - 权限开通（仅程序发起，不允许人员提交）
        # 流程：发起人 → 自动授权(权限中心+通知) → 结束
        # ====================================================================
        permission_apply_definition = {
            "nodeConfig": {
                "key": "start",
                "name": "发起人",
                "type": 0,
                "childNode": {
                    "key": "auto_grant",
                    "name": "自动授权",
                    "type": 5,
                    "transactors": auto_transactors,
                    "taskConfig": {
                        "mode": "auto",
                        "executionMode": "sequential",
                        "actions": [
                            {
                                "key": "act_grant_permission",
                                "name": "权限中心授权",
                                "capabilityId": perm_cap.id,
                                "capabilityCode": "permission.center.grant",
                                "fieldBindings": [
                                    {"capabilityField": "system", "capabilityType": "string", "source": "form", "formField": "system"},
                                    {"capabilityField": "account", "capabilityType": "string", "source": "form", "formField": "account"},
                                    {"capabilityField": "permission_level", "capabilityType": "string", "source": "form", "formField": "permission_level"},
                                    {"capabilityField": "permission_scope", "capabilityType": "string", "source": "form", "formField": "permission_scope"},
                                    {"capabilityField": "duration_type", "capabilityType": "string", "source": "form", "formField": "duration_type"},
                                    {"capabilityField": "duration_days", "capabilityType": "integer", "source": "form", "formField": "duration_days"},
                                ],
                            },
                            {
                                "key": "act_send_notify",
                                "name": "发送开通通知",
                                "capabilityId": mail_cap.id,
                                "capabilityCode": "mail.send",
                                "fieldBindings": [
                                    {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "notify_email"},
                                    {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "权限开通完成通知"},
                                    {"capabilityField": "body", "capabilityType": "string", "source": "constant", "constant": "您申请的系统权限已开通完成。"},
                                ],
                            },
                        ],
                    },
                    "childNode": {"key": "end1", "name": "结束", "type": 9, "childNode": None}
                }
            },
            "workFlowDef": {"id": "wf_permission_apply", "icon": "key", "name": "权限开通", "cancelable": 0},
            "flowPermission": {"type": 0, "flowInitiators": []},
        }

        ProcessDefinition.objects.get_or_create(
            key='permission_apply',
            defaults={
                'name': '权限开通',
                'version': 1,
                'status': 'published',
                'category': 'it',
                'submit_scope': 'none',
                'allow_program_initiate': True,
                'initiator_app_ids': [initiator_apps['permission_center'].id],
                'definition_json': permission_apply_definition,
                'form_schema': permission_apply_form,
                'created_by': admin_user,
            },
        )

        # ====================================================================
        # 10. 流程定义 - 申请新增服务（全员可提交 + 云管平台发起）
        # 流程：发起人 → 主管审批 → 运维评估 → [生产?] → 技术负责人审批 →
        #       环境准备(同步) → 应用部署(异步) → 健康检查(异步) → 发布通知(同步) → 结束
        # ====================================================================
        new_service_apply_definition = {
            "nodeConfig": {
                "key": "start",
                "name": "发起人",
                "type": 0,
                "childNode": {
                    "key": "manager_approve",
                    "name": "部门主管审批",
                    "type": 1,
                    "multiInstanceApprovalType": 0,
                    "assignees": [{"rid": "a1", "assigneeType": 1, "layer": 0, "layerType": 0}],
                    "childNode": {
                        "key": "ops_evaluate",
                        "name": "运维评估",
                        "type": 1,
                        "multiInstanceApprovalType": 0,
                        "assignees": [{"rid": "a2", "assigneeType": 4, "assignees": [xiaoli.id]}],
                        "childNode": {
                            "key": "prod_gateway",
                            "name": "环境判断",
                            "type": 4,
                            "conditionNodes": [
                                {
                                    "key": "prod_env",
                                    "name": "生产环境",
                                    "type": 3,
                                    "priorityLevel": 1,
                                    "conditionGroups": [
                                        {"conditions": [{"varName": "environment", "operator": 0, "val": "production"}]}
                                    ],
                                    "childNode": {
                                        "key": "tech_approve",
                                        "name": "技术负责人审批",
                                        "type": 1,
                                        "multiInstanceApprovalType": 0,
                                        "assignees": [{"rid": "a3", "assigneeType": 1, "layer": 1, "layerType": 0}],
                                        "childNode": {
                                            "key": "env_prepare",
                                            "name": "环境准备",
                                            "type": 5,
                                            "transactors": auto_transactors,
                                            "taskConfig": {
                                                "mode": "auto",
                                                "executionMode": "sequential",
                                                "actions": [
                                                    {
                                                        "key": "act_prepare_dns",
                                                        "name": "预分配域名解析",
                                                        "capabilityId": dns_cap.id,
                                                        "capabilityCode": "dns.add_record",
                                                        "fieldBindings": [
                                                            {"capabilityField": "domain", "capabilityType": "string", "source": "form", "formField": "domain_request"},
                                                            {"capabilityField": "record_type", "capabilityType": "string", "source": "constant", "constant": "CNAME"},
                                                            {"capabilityField": "record_value", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                        ],
                                                    },
                                                ],
                                            },
                                            "childNode": {
                                                "key": "app_deploy",
                                                "name": "应用部署",
                                                "type": 5,
                                                "transactors": auto_transactors,
                                                "taskConfig": {
                                                    "mode": "auto",
                                                    "executionMode": "sequential",
                                                    "actions": [
                                                        {
                                                            "key": "act_deploy_host",
                                                            "name": "创建应用主机并部署",
                                                            "capabilityId": cmdb_cap.id,
                                                            "capabilityCode": "cmdb.create_host",
                                                            "fieldBindings": [
                                                                {"capabilityField": "hostname", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                                {"capabilityField": "cpu", "capabilityType": "integer", "source": "constant", "constant": 4},
                                                                {"capabilityField": "memory", "capabilityType": "integer", "source": "constant", "constant": 8},
                                                                {"capabilityField": "os", "capabilityType": "string", "source": "constant", "constant": "Ubuntu 22.04"},
                                                            ],
                                                        },
                                                    ],
                                                },
                                                "childNode": {
                                                    "key": "health_check",
                                                    "name": "健康检查",
                                                    "type": 5,
                                                    "transactors": auto_transactors,
                                                    "taskConfig": {
                                                        "mode": "auto",
                                                        "executionMode": "sequential",
                                                        "actions": [
                                                            {
                                                                "key": "act_health_check",
                                                                "name": "外部健康检查确认",
                                                                "capabilityId": external_approve_cap.id,
                                                                "capabilityCode": "external.approve",
                                                                "fieldBindings": [
                                                                    {"capabilityField": "title", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                                    {"capabilityField": "content", "capabilityType": "string", "source": "form", "formField": "resource_request"},
                                                                    {"capabilityField": "approver", "capabilityType": "string", "source": "constant", "constant": "技术负责人"},
                                                                ],
                                                            },
                                                        ],
                                                    },
                                                    "childNode": {
                                                        "key": "release_notify",
                                                        "name": "发布通知",
                                                        "type": 5,
                                                        "transactors": auto_transactors,
                                                        "taskConfig": {
                                                            "mode": "auto",
                                                            "executionMode": "sequential",
                                                            "actions": [
                                                                {
                                                                    "key": "act_release_notify",
                                                                    "name": "发送发布结果通知",
                                                                    "capabilityId": mail_cap.id,
                                                                    "capabilityCode": "mail.send",
                                                                    "fieldBindings": [
                                                                        {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "notify_email"},
                                                                        {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "服务发布完成通知"},
                                                                        {"capabilityField": "body", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                                    ],
                                                                },
                                                            ],
                                                        },
                                                        "childNode": {"key": "end1", "name": "结束", "type": 9, "childNode": None}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "key": "non_prod_env",
                                    "name": "非生产环境",
                                    "type": 3,
                                    "priorityLevel": 2,
                                    "conditionGroups": [],
                                    "childNode": {
                                        "key": "env_prepare",
                                        "name": "环境准备",
                                        "type": 5,
                                        "transactors": auto_transactors,
                                        "taskConfig": {
                                            "mode": "auto",
                                            "executionMode": "sequential",
                                            "actions": [
                                                {
                                                    "key": "act_prepare_dns2",
                                                    "name": "预分配域名解析",
                                                    "capabilityId": dns_cap.id,
                                                    "capabilityCode": "dns.add_record",
                                                    "fieldBindings": [
                                                        {"capabilityField": "domain", "capabilityType": "string", "source": "form", "formField": "domain_request"},
                                                        {"capabilityField": "record_type", "capabilityType": "string", "source": "constant", "constant": "CNAME"},
                                                        {"capabilityField": "record_value", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                    ],
                                                },
                                            ],
                                        },
                                        "childNode": {
                                            "key": "app_deploy",
                                            "name": "应用部署",
                                            "type": 5,
                                            "transactors": auto_transactors,
                                            "taskConfig": {
                                                "mode": "auto",
                                                "executionMode": "sequential",
                                                "actions": [
                                                    {
                                                        "key": "act_deploy_host2",
                                                        "name": "创建应用主机并部署",
                                                        "capabilityId": cmdb_cap.id,
                                                        "capabilityCode": "cmdb.create_host",
                                                        "fieldBindings": [
                                                            {"capabilityField": "hostname", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                            {"capabilityField": "cpu", "capabilityType": "integer", "source": "constant", "constant": 4},
                                                            {"capabilityField": "memory", "capabilityType": "integer", "source": "constant", "constant": 8},
                                                            {"capabilityField": "os", "capabilityType": "string", "source": "constant", "constant": "Ubuntu 22.04"},
                                                        ],
                                                    },
                                                ],
                                            },
                                            "childNode": {
                                                "key": "release_notify",
                                                "name": "发布通知",
                                                "type": 5,
                                                "transactors": auto_transactors,
                                                "taskConfig": {
                                                    "mode": "auto",
                                                    "executionMode": "sequential",
                                                    "actions": [
                                                        {
                                                            "key": "act_release_notify2",
                                                            "name": "发送发布结果通知",
                                                            "capabilityId": mail_cap.id,
                                                            "capabilityCode": "mail.send",
                                                            "fieldBindings": [
                                                                {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "notify_email"},
                                                                {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "服务发布完成通知"},
                                                                {"capabilityField": "body", "capabilityType": "string", "source": "form", "formField": "service_name"},
                                                            ],
                                                        },
                                                    ],
                                                },
                                                "childNode": {"key": "end2", "name": "结束", "type": 9, "childNode": None}
                                            }
                                        }
                                    }
                                }
                            ],
                            "childNode": None
                        }
                    }
                }
            },
            "workFlowDef": {"id": "wf_new_service_apply", "icon": "cloud", "name": "申请新增服务", "cancelable": 1},
            "flowPermission": {"type": 0, "flowInitiators": []},
        }

        ProcessDefinition.objects.get_or_create(
            key='new_service_apply',
            defaults={
                'name': '申请新增服务',
                'version': 1,
                'status': 'published',
                'category': 'it',
                'submit_scope': 'all',
                'allow_program_initiate': True,
                'initiator_app_ids': [initiator_apps['cloud_manager'].id],
                'definition_json': new_service_apply_definition,
                'form_schema': new_service_apply_form,
                'created_by': admin_user,
            },
        )

        # ====================================================================
        # 11. 流程定义 - 服务器重启（运维组可提交 + 云管平台发起）
        # 流程：发起人 → 自动重启(重启主机+通知) → 结束
        # ====================================================================
        server_restart_definition = {
            "nodeConfig": {
                "key": "start",
                "name": "发起人",
                "type": 0,
                "childNode": {
                    "key": "auto_restart",
                    "name": "自动重启",
                    "type": 5,
                    "transactors": auto_transactors,
                    "taskConfig": {
                        "mode": "auto",
                        "executionMode": "sequential",
                        "actions": [
                            {
                                "key": "act_restart_host",
                                "name": "重启主机",
                                "capabilityId": restart_cap.id,
                                "capabilityCode": "cmdb.restart_host",
                                "fieldBindings": [
                                    {"capabilityField": "hostname", "capabilityType": "string", "source": "form", "formField": "hostname"},
                                    {"capabilityField": "restart_type", "capabilityType": "string", "source": "form", "formField": "restart_type"},
                                ],
                            },
                            {
                                "key": "act_send_notify",
                                "name": "发送重启结果通知",
                                "capabilityId": mail_cap.id,
                                "capabilityCode": "mail.send",
                                "fieldBindings": [
                                    {"capabilityField": "to", "capabilityType": "array", "source": "form", "formField": "notify_list"},
                                    {"capabilityField": "subject", "capabilityType": "string", "source": "constant", "constant": "服务器重启完成通知"},
                                    {"capabilityField": "body", "capabilityType": "string", "source": "constant", "constant": "服务器重启操作已完成，请确认服务状态。"},
                                ],
                            },
                        ],
                    },
                    "childNode": {"key": "end1", "name": "结束", "type": 9, "childNode": None}
                }
            },
            "workFlowDef": {"id": "wf_server_restart", "icon": "restart", "name": "服务器重启", "cancelable": 0},
            "flowPermission": {"type": 0, "flowInitiators": []},
        }

        ProcessDefinition.objects.get_or_create(
            key='server_restart',
            defaults={
                'name': '服务器重启',
                'version': 1,
                'status': 'published',
                'category': 'it',
                'submit_scope': 'specific_dept',
                'submit_scope_ids': [it_ops.id],
                'allow_program_initiate': True,
                'initiator_app_ids': [initiator_apps['cloud_manager'].id],
                'definition_json': server_restart_definition,
                'form_schema': server_restart_form,
                'created_by': admin_user,
            },
        )

        self.stdout.write(self.style.SUCCESS('✓ 流程定义创建完成'))

        # ====================================================================
        # 12. 创建预置流程实例
        # ====================================================================
        from apps.processes.models import ProcessInstance, NodeTask
        from django.utils import timezone
        from datetime import timedelta

        # 获取流程定义
        server_apply_def = ProcessDefinition.objects.get(key='server_apply')

        # 实例1：服务器申请 - 运行中（小明发起，待运维审批）
        instance1, created = ProcessInstance.objects.get_or_create(
            instance_no='SRV-2026-001',
            defaults={
                'definition': server_apply_def,
                'status': 'running',
                'current_node_key': 'ops_approve',
                'started_by': xiaoming,
                'business_key': 'SRV-2026-001',
                'variables': {
                    'hostname': 'web-prod-01',
                    'os': 'CentOS 7.9',
                    'cpu': 8,
                    'memory': 16,
                    'disk_size': 100,
                    'data_disk_size': 500,
                    'zone': 'cn-hangzhou',
                    'quantity': 1,
                    'email': 'xiaoming@company.com',
                    'reason': '线上业务扩容，需要更多服务器资源',
                },
            }
        )
        if created:
            NodeTask.objects.create(
                instance=instance1,
                node_key='ops_approve',
                node_name='运维审批',
                node_type='approve',
                approval_type='single',
                assignee=xiaoli,
                candidate_users=[xiaoli.id],
                status='pending',
            )

        # 实例2：服务器申请 - 已完成
        instance2, created = ProcessInstance.objects.get_or_create(
            instance_no='SRV-2026-002',
            defaults={
                'definition': server_apply_def,
                'status': 'completed',
                'current_node_key': 'end',
                'started_by': xiaohong,
                'ended_at': timezone.now() - timedelta(days=1),
                'business_key': 'SRV-2026-002',
                'variables': {
                    'hostname': 'web-prod-02',
                    'os': 'Ubuntu 22.04 LTS',
                    'cpu': 4,
                    'memory': 8,
                    'disk_size': 50,
                    'zone': 'cn-hangzhou',
                    'quantity': 1,
                    'email': 'xiaohong@company.com',
                    'reason': '新业务上线需要服务器',
                },
            }
        )
        if created:
            NodeTask.objects.create(
                instance=instance2,
                node_key='ops_approve',
                node_name='运维审批',
                node_type='approve',
                approval_type='single',
                assignee=xiaoli,
                candidate_users=[xiaoli.id],
                status='completed',
                result='approved',
                opinion='同意，资源充足',
            )

        # 实例3：服务器重启 - 运行中（运维组小王发起，自动重启中）
        server_restart_def = ProcessDefinition.objects.get(key='server_restart')
        instance3, created = ProcessInstance.objects.get_or_create(
            instance_no='SRV-2026-003',
            defaults={
                'definition': server_restart_def,
                'status': 'running',
                'current_node_key': 'auto_restart',
                'started_by': xiaowang,
                'business_key': 'SRV-2026-003',
                'variables': {
                    'hostname': 'db-master-01',
                    'restart_type': 'system',
                    'reason': '系统内核安全更新后需要重启',
                    'urgency': 'urgent',
                    'downtime_expected': 10,
                    'notify_list': 'ops@company.com,dba@company.com',
                },
            }
        )
        if created:
            NodeTask.objects.create(
                instance=instance3,
                node_key='auto_restart',
                node_name='自动重启',
                node_type='handle',
                assignee=xiaowang,
                candidate_users=[xiaowang.id],
                status='running',
            )

        self.stdout.write(self.style.SUCCESS('✓ 预置流程实例创建完成'))
        self.stdout.write(self.style.SUCCESS('🎉 种子数据初始化完成！'))
        self.stdout.write('')
        self.stdout.write('默认用户：')
        self.stdout.write('  admin / admin123 （管理员）')
        self.stdout.write('  xiaoming / user123 （小明 - 研发组）')
        self.stdout.write('  xiaohong / user123 （小红 - 研发组）')
        self.stdout.write('  xiaohuang / user123 （小黄 - 研发组）')
        self.stdout.write('  xiaoli / user123 （小李 - IT运维组，部门主管）')
        self.stdout.write('  xiaowang / user123 （小王 - IT运维组）')
        self.stdout.write('  xiaozhang / user123 （小张 - 财务部，部门主管）')
        self.stdout.write('  xiaozhao / user123 （小赵 - 财务部）')
        self.stdout.write('')
        self.stdout.write('发起程序 API Key（仅展示一次）：')
        for ad in apps_data:
            self.stdout.write(f"  {ad['code']} = {ad['api_key']}")
