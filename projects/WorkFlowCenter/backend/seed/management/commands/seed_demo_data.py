"""
Demo 演示数据增强（待办 / 已办 / 抄送补齐）

背景：reset_demo 恢复的 demo_full.json 是"历史真实运行"快照，其中流程多为
E2E 自动跑完（全部完成、审批人多为小李/系统），导致以 admin 等账号登录时：
  - 待办：0（没有进行中且审批人是当前账号的任务）
  - 抄送：0（没有 action=cc 的抄送记录）
对面试/演示不友好。

本命令用 ORM 幂等构造一批自洽的演示数据（以管理员 admin 为主，
体现"管理员自己提交、自己审批"的完整闭环）：
  - 进行中实例 + pending 审批任务 → 「待办」有数据（admin / xiaoli）
  - 已完成实例 + completed 审批任务 + approve 记录 → 「已办」有数据（admin）
  - 抄送节点 + cc 审批记录 → 「抄送我的」有数据（admin / 其他用户）

用法：
  python manage.py seed_demo_data        # 幂等，可重复执行
集成：reset_demo 在 loaddata 之后会自动调用本命令。
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.capabilities.models import Capability, TaskJob
from apps.events.models import WebhookSubscription, WebhookDelivery
from apps.processes.models import (
    ProcessDefinition,
    ProcessInstance,
    NodeTask,
    ApprovalRecord,
    InitiatorApp,
    ApiCallLog,
)
from apps.processes.services.security import hash_api_key

User = get_user_model()

# ---------------------------------------------------------------------------
# 实例编号前缀：DM-Demo，避免与 seed(SRV-)/运行(WI-) 冲突
# ---------------------------------------------------------------------------

# 进行中（产生待办）
PENDING_INSTANCES = [
    {
        'instance_no': 'DM-2026-001',
        'definition_key': 'server_apply',
        'started_by': 'xiaoming',
        'current_node_key': 'ops_approve',
        'variables': {
            'hostname': 'demo-web-01', 'os': 'CentOS 7.9',
            'cpu': 8, 'memory': 16, 'disk_size': 100, 'data_disk_size': 200,
            'zone': 'cn-hangzhou', 'quantity': 1, 'network_segment': '10.20.1.0/24',
            'email': 'xiaoming@company.com',
            'reason': '业务系统扩容，申请一台 Web 服务器承载新增业务',
        },
        'task': {
            'node_key': 'ops_approve', 'node_name': '运维审批',
            'assignee': 'admin',
        },
    },
    {
        'instance_no': 'DM-2026-002',
        'definition_key': 'new_service_apply',
        'started_by': 'xiaohong',
        'current_node_key': 'manager_approve',
        'variables': {
            'service_name': 'demo-user-api', 'service_type': 'api',
            'environment': 'test', 'language_runtime': 'python312',
            'resource_request': '2C4G，20G 磁盘', 'dependency': '',
            'domain_request': 'api.demo.com', 'db_required': True,
            'db_type': 'mysql', 'expected_date': '2026-09-15',
            'notify_email': 'xiaohong@company.com',
            'reason': '新增用户服务 API，供业务方与前端调用',
        },
        'task': {
            'node_key': 'manager_approve', 'node_name': '部门主管审批',
            'assignee': 'admin',
        },
    },
    {
        'instance_no': 'DM-2026-003',
        'definition_key': 'server_apply',
        'started_by': 'admin',
        'current_node_key': 'ops_approve',
        'variables': {
            'hostname': 'demo-db-01', 'os': 'Ubuntu 22.04',
            'cpu': 16, 'memory': 64, 'disk_size': 200, 'data_disk_size': 1000,
            'zone': 'cn-beijing', 'quantity': 1, 'network_segment': '10.20.2.0/24',
            'email': 'admin@company.com',
            'reason': '数据库集群扩容，申请一台高性能数据库服务器',
        },
        'task': {
            'node_key': 'ops_approve', 'node_name': '运维审批',
            'assignee': 'xiaoli',
        },
    },
]

# 已完成（产生已办 + 抄送）
DONE_INSTANCES = [
    {
        'instance_no': 'DM-2026-011',
        'definition_key': 'server_apply',
        'started_by': 'admin',
        'current_node_key': 'end',
        'variables': {
            'hostname': 'demo-cmdb-01', 'os': 'CentOS 7.9',
            'cpu': 8, 'memory': 32, 'disk_size': 200, 'data_disk_size': 500,
            'zone': 'cn-hangzhou', 'quantity': 1, 'network_segment': '10.20.3.0/24',
            'email': 'admin@company.com',
            'reason': '演示流程：管理员自行发起并审批的服务器申请',
        },
        'approve_task': {
            'node_key': 'ops_approve', 'node_name': '运维审批',
            'assignee': 'admin', 'result': 'approve',
            'opinion': '同意，按标准配置开通',
        },
        'cc_task': {
            'node_key': 'cc_notify', 'node_name': '抄送通知',
            'cc_users': ['admin', 'xiaoming'],
        },
    },
    {
        'instance_no': 'DM-2026-012',
        'definition_key': 'new_service_apply',
        'started_by': 'admin',
        'current_node_key': 'end',
        'variables': {
            'service_name': 'demo-report-service', 'service_type': 'web',
            'environment': 'production', 'language_runtime': 'java17',
            'resource_request': '4C8G，50G 磁盘', 'dependency': 'demo-user-api',
            'domain_request': 'report.demo.com', 'db_required': False,
            'db_type': None, 'expected_date': '2026-10-01',
            'notify_email': 'admin@company.com',
            'reason': '演示流程：管理员发起并审批的新增报表服务',
        },
        'approve_task': {
            'node_key': 'manager_approve', 'node_name': '部门主管审批',
            'assignee': 'admin', 'result': 'approve',
            'opinion': '同意，安排上线',
        },
        'cc_task': {
            'node_key': 'cc_notify', 'node_name': '抄送通知',
            'cc_users': ['admin', 'xiaohong'],
        },
        # 办理节点：同步/异步混合（演示队列语义日志）
        'handle_tasks': [
            {
                'node_key': 'env_prepare', 'node_name': '环境准备', 'sync': True,
                'actions': [
                    {
                        'action_key': 'act_prepare_dns', 'action_name': '预分配域名解析',
                        'capability_code': 'dns.add_record',
                        'input_data': {'domain': 'report.demo.com', 'record_type': 'CNAME', 'record_value': 'demo-report-service'},
                        'output_data': {'record_id': 'mock-dns-001', 'domain': 'report.demo.com', 'record_type': 'CNAME', 'status': 'created'},
                    },
                ],
            },
            {
                'node_key': 'app_deploy', 'node_name': '应用部署', 'sync': False,
                'actions': [
                    {
                        'action_key': 'act_deploy_host', 'action_name': '创建应用主机并部署',
                        'capability_code': 'cmdb.create_host',
                        'input_data': {'hostname': 'demo-report-service', 'cpu': 4, 'memory': 8, 'os': 'Ubuntu 22.04'},
                        'output_data': {'host_id': 'mock-host-001', 'hostname': 'demo-report-service', 'ip': '10.0.0.100', 'status': 'active'},
                    },
                ],
            },
            {
                'node_key': 'health_check', 'node_name': '健康检查', 'sync': False,
                'actions': [
                    {
                        'action_key': 'act_health_check', 'action_name': '外部健康检查确认',
                        'capability_code': 'external.approve',
                        'input_data': {'title': 'demo-report-service', 'content': '4C8G，50G 磁盘', 'approver': '技术负责人'},
                        'output_data': {'approval_id': 'mock-approval-001', 'status': 'approved', 'approver': 'mock-system'},
                    },
                ],
            },
            {
                'node_key': 'release_notify', 'node_name': '发布通知', 'sync': True,
                'actions': [
                    {
                        'action_key': 'act_release_notify', 'action_name': '发送发布结果通知',
                        'capability_code': 'mail.send',
                        'input_data': {'to': ['admin@company.com'], 'subject': '服务发布完成通知', 'body': 'demo-report-service'},
                        'output_data': {'message_id': 'mock-mail-001', 'to': ['admin@company.com'], 'status': 'sent'},
                    },
                ],
            },
        ],
    },
]


# 状态场景实例（办理中 / 办理失败，配合 DM-2026-012 的成功场景形成三种状态演示）
STATE_INSTANCES = [
    {
        # 办理中：异步任务已提交到队列，等待任务队列执行
        'instance_no': 'DM-2026-021',
        'definition_key': 'server_apply',
        'started_by': 'admin',
        'current_node_key': 'auto_create',
        'variables': {
            'hostname': 'demo-batch-01', 'os': 'CentOS 7.9',
            'cpu': 16, 'memory': 64, 'disk_size': 100, 'data_disk_size': 200,
            'zone': 'cn-hangzhou', 'quantity': 1, 'network_segment': '10.20.5.0/24',
            'email': 'xiaoming@company.com', 'reason': '批量计算任务，申请高配服务器',
        },
        'prev_approves': [
            {
                'node_key': 'ops_approve', 'node_name': '运维审批',
                'assignee': 'xiaoli', 'result': 'approve', 'opinion': '同意，按配置开通',
            },
            {
                'node_key': 'manager_approve', 'node_name': '部门主管审批',
                'assignee': 'admin', 'result': 'approve', 'opinion': '同意，高配资源',
            },
        ],
        'handle': {
            'node_key': 'auto_create', 'node_name': '自动创建主机',
            'status': 'running',
            'actions': [
                {
                    'action_key': 'act_create_host', 'action_name': '创建主机',
                    'capability_code': 'cmdb.create_host',
                    'input_data': {'hostname': 'demo-batch-01', 'cpu': 16, 'memory': 64, 'os': 'CentOS 7.9'},
                },
            ],
        },
    },
    {
        # 办理失败：异步任务执行失败，通知办理人（一键拉群）
        'instance_no': 'DM-2026-022',
        'definition_key': 'server_apply',
        'started_by': 'admin',
        'current_node_key': 'auto_create',
        'variables': {
            'hostname': 'demo-failed-01', 'os': 'Ubuntu 22.04',
            'cpu': 8, 'memory': 32, 'disk_size': 100, 'data_disk_size': 200,
            'zone': 'cn-beijing', 'quantity': 1, 'network_segment': '10.20.6.0/24',
            'email': 'xiaohong@company.com', 'reason': '演示：异步任务失败场景',
        },
        'prev_approve': {
            'node_key': 'ops_approve', 'node_name': '运维审批',
            'assignee': 'xiaoli', 'result': 'approve', 'opinion': '同意',
        },
        'handle': {
            'node_key': 'auto_create2', 'node_name': '自动创建主机',
            'status': 'abnormal',
            'error': '连接执行队列超时，重试 3 次后失败',
            'group_name': '主机创建异常群',
            'actions': [
                {
                    'action_key': 'act_create_host2', 'action_name': '创建主机',
                    'capability_code': 'cmdb.create_host',
                    'input_data': {'hostname': 'demo-failed-01', 'cpu': 8, 'memory': 32, 'os': 'Ubuntu 22.04'},
                },
            ],
        },
    },
]


class Command(BaseCommand):
    help = '补齐 Demo 演示数据（待办/已办/抄送），幂等可重复执行'

    def handle(self, *args, **options):
        self.stdout.write('开始补齐 Demo 演示数据（待办/已办/抄送）...')
        created_instances = 0
        created_tasks = 0
        created_records = 0

        # ---------- 1. 进行中实例（待办） ----------
        for item in PENDING_INSTANCES:
            definition = ProcessDefinition.objects.get(key=item['definition_key'])
            started_by = User.objects.get(username=item['started_by'])
            instance, created = ProcessInstance.objects.get_or_create(
                instance_no=item['instance_no'],
                defaults={
                    'definition': definition,
                    'started_by': started_by,
                    'current_node_key': item['current_node_key'],
                    'variables': item['variables'],
                    'business_key': None,
                },
            )
            if not created:
                continue  # 幂等：已存在则跳过
            created_instances += 1

            t = item['task']
            assignee = User.objects.get(username=t['assignee'])
            NodeTask.objects.get_or_create(
                instance=instance,
                node_key=t['node_key'],
                defaults={
                    'node_name': t['node_name'],
                    'node_type': NodeTask.NodeType.APPROVE,
                    'approval_type': NodeTask.ApprovalType.SINGLE,
                    'assignee': assignee,
                    'candidate_users': [assignee.id],
                    'status': NodeTask.Status.PENDING,
                },
            )
            created_tasks += 1

        # ---------- 2. 已完成实例（已办 + 抄送） ----------
        for item in DONE_INSTANCES:
            definition = ProcessDefinition.objects.get(key=item['definition_key'])
            started_by = User.objects.get(username=item['started_by'])
            instance, created = ProcessInstance.objects.get_or_create(
                instance_no=item['instance_no'],
                defaults={
                    'definition': definition,
                    'started_by': started_by,
                    'current_node_key': item['current_node_key'],
                    'variables': item['variables'],
                    'business_key': None,
                },
            )
            if not created:
                continue  # 幂等：已存在则跳过
            created_instances += 1

            # 标记完成（FSM transition: running -> completed）
            instance.complete()
            instance.ended_at = timezone.now() - timedelta(days=1)
            instance.save(update_fields=['status', 'ended_at', 'updated_at'])

            # 已办：审批任务（completed + approve 记录）
            at = item['approve_task']
            assignee = User.objects.get(username=at['assignee'])
            task, task_created = NodeTask.objects.get_or_create(
                instance=instance,
                node_key=at['node_key'],
                defaults={
                    'node_name': at['node_name'],
                    'node_type': NodeTask.NodeType.APPROVE,
                    'approval_type': NodeTask.ApprovalType.SINGLE,
                    'assignee': assignee,
                    'candidate_users': [assignee.id],
                    'status': NodeTask.Status.COMPLETED,
                    'result': at['result'],
                    'opinion': at['opinion'],
                },
            )
            if task_created:
                created_tasks += 1
                ApprovalRecord.objects.get_or_create(
                    instance=instance,
                    task=task,
                    user=assignee,
                    action='approve',
                    defaults={'opinion': at['opinion']},
                )
                created_records += 1

            # 抄送：抄送节点（自动完成 + cc 记录）
            ct = item['cc_task']
            cc_users = [User.objects.get(username=u) for u in ct['cc_users']]
            cc_task, cc_created = NodeTask.objects.get_or_create(
                instance=instance,
                node_key=ct['node_key'],
                defaults={
                    'node_name': ct['node_name'],
                    'node_type': NodeTask.NodeType.CC,
                    'candidate_users': [u.id for u in cc_users],
                    'status': NodeTask.Status.COMPLETED,
                },
            )
            if cc_created:
                created_tasks += 1
                for u in cc_users:
                    ApprovalRecord.objects.get_or_create(
                        instance=instance,
                        task=cc_task,
                        user=u,
                        action='cc',
                        defaults={'opinion': '已抄送'},
                    )
                    created_records += 1

            # 办理节点（同步/异步混合，模拟自动执行 + 队列语义日志）
            handle_tasks = item.get('handle_tasks') or []
            base_ts = timezone.now() - timedelta(hours=2)
            for ht in handle_tasks:
                htask, h_created = NodeTask.objects.get_or_create(
                    instance=instance,
                    node_key=ht['node_key'],
                    defaults={
                        'node_name': ht['node_name'],
                        'node_type': NodeTask.NodeType.HANDLE,
                        'status': NodeTask.Status.COMPLETED,
                        'result': 'success',
                    },
                )
                if not h_created:
                    continue
                created_tasks += 1
                for ai, act in enumerate(ht['actions']):
                    cap = Capability.objects.filter(code=act['capability_code'], is_active=True).first()
                    if not cap:
                        continue
                    job_id = f'demo-{item["instance_no"]}-{ht["node_key"]}-{act["action_key"]}'
                    step_ts = lambda s: (base_ts + timedelta(seconds=5 * (ai * 4 + s))).isoformat(timespec='seconds')
                    if ht['sync']:
                        logs = [
                            {'ts': step_ts(0), 'level': 'info', 'message': f"动作「{act['action_name']}」已创建，等待执行"},
                            {'ts': step_ts(1), 'level': 'info', 'message': f"开始执行动作「{act['action_name']}」"},
                            {'ts': step_ts(2), 'level': 'debug', 'message': f"入参：{act['input_data']}"},
                            {'ts': step_ts(3), 'level': 'info', 'message': f"动作「{act['action_name']}」执行成功"},
                        ]
                    else:
                        logs = [
                            {'ts': step_ts(0), 'level': 'info', 'message': f"动作「{act['action_name']}」已提交到执行队列（job_id={job_id}），流程无需等待，执行结果将通过队列消息/回调回写"},
                            {'ts': step_ts(1), 'level': 'info', 'message': f"收到队列执行消息，开始执行动作「{act['action_name']}」"},
                            {'ts': step_ts(2), 'level': 'debug', 'message': f"入参：{act['input_data']}"},
                            {'ts': step_ts(3), 'level': 'info', 'message': f"动作「{act['action_name']}」执行成功，已通过队列消息/回调回写执行状态"},
                        ]
                    TaskJob.objects.get_or_create(
                        instance=instance,
                        task=htask,
                        node_key=ht['node_key'],
                        action_key=act['action_key'],
                        defaults={
                            'capability': cap,
                            'action_name': act['action_name'],
                            'job_id': job_id,
                            'input_data': act['input_data'],
                            'output_data': act['output_data'],
                            'sync': ht['sync'],
                            'status': TaskJob.Status.SUCCEEDED,
                            'logs': logs,
                            'started_at': base_ts + timedelta(seconds=5 * (ai * 4)),
                            'completed_at': base_ts + timedelta(seconds=5 * (ai * 4 + 3)),
                        },
                    )

        # ---------- 3. 状态场景实例（办理中 / 办理失败） ----------
        for item in STATE_INSTANCES:
            definition = ProcessDefinition.objects.get(key=item['definition_key'])
            started_by = User.objects.get(username=item['started_by'])
            instance, created = ProcessInstance.objects.get_or_create(
                instance_no=item['instance_no'],
                defaults={
                    'definition': definition,
                    'started_by': started_by,
                    'current_node_key': item['current_node_key'],
                    'variables': item['variables'],
                    'business_key': None,
                },
            )
            if not created:
                continue
            created_instances += 1

            # 前置审批（已通过，支持多个）
            prevs = item.get('prev_approves') or ([item['prev_approve']] if item.get('prev_approve') else [])
            for prev in prevs:
                approver = User.objects.get(username=prev['assignee'])
                ptask, _ = NodeTask.objects.get_or_create(
                    instance=instance,
                    node_key=prev['node_key'],
                    defaults={
                        'node_name': prev['node_name'],
                        'node_type': NodeTask.NodeType.APPROVE,
                        'approval_type': NodeTask.ApprovalType.SINGLE,
                        'assignee': approver,
                        'candidate_users': [approver.id],
                        'status': NodeTask.Status.COMPLETED,
                        'result': prev['result'],
                        'opinion': prev['opinion'],
                    },
                )
                created_tasks += 1
                ApprovalRecord.objects.get_or_create(
                    instance=instance, task=ptask, user=approver,
                    action='approve', defaults={'opinion': prev['opinion']},
                )
                created_records += 1

            # 当前办理节点（办理中 running / 办理失败 abnormal）
            ht = item['handle']
            is_running = ht['status'] == 'running'
            hstatus = NodeTask.Status.RUNNING if is_running else NodeTask.Status.ABNORMAL
            htask, h_created = NodeTask.objects.get_or_create(
                instance=instance,
                node_key=ht['node_key'],
                defaults={
                    'node_name': ht['node_name'],
                    'node_type': NodeTask.NodeType.HANDLE,
                    'status': hstatus,
                    'result': '' if is_running else 'failed',
                    'opinion': '' if is_running else ht.get('error', ''),
                },
            )
            if not h_created:
                continue
            created_tasks += 1

            base_ts = timezone.now() - timedelta(minutes=20)
            for ai, act in enumerate(ht['actions']):
                cap = Capability.objects.filter(code=act['capability_code'], is_active=True).first()
                if not cap:
                    continue
                job_id = f'demo-{item["instance_no"]}-{ht["node_key"]}-{act["action_key"]}'
                step_ts = lambda s: (base_ts + timedelta(seconds=10 * s)).isoformat(timespec='seconds')
                if is_running:
                    logs = [
                        {'ts': step_ts(0), 'level': 'info', 'message': f"动作「{act['action_name']}」已提交到执行队列（job_id={job_id}），流程无需等待，执行结果将通过队列消息/回调回写"},
                        {'ts': step_ts(1), 'level': 'info', 'message': '正在等待任务队列执行（办理中）...'},
                        {'ts': step_ts(2), 'level': 'debug', 'message': f"入参：{act['input_data']}"},
                    ]
                    jstatus = TaskJob.Status.RUNNING
                else:
                    logs = [
                        {'ts': step_ts(0), 'level': 'info', 'message': f"动作「{act['action_name']}」已提交到执行队列（job_id={job_id}），流程无需等待，执行结果将通过队列消息/回调回写"},
                        {'ts': step_ts(1), 'level': 'info', 'message': f"收到队列执行消息，开始执行动作「{act['action_name']}」"},
                        {'ts': step_ts(2), 'level': 'error', 'message': f"动作「{act['action_name']}」执行失败：{ht.get('error', '连接执行队列超时')}"},
                        {'ts': step_ts(3), 'level': 'info', 'message': f"已通知办理人（一键拉群：{ht.get('group_name', '执行异常处理群')}），等待人工处理"},
                    ]
                    jstatus = TaskJob.Status.FAILED
                TaskJob.objects.get_or_create(
                    instance=instance,
                    task=htask,
                    node_key=ht['node_key'],
                    action_key=act['action_key'],
                    defaults={
                        'capability': cap,
                        'action_name': act['action_name'],
                        'job_id': job_id,
                        'input_data': act['input_data'],
                        'output_data': {},
                        'sync': False,
                        'status': jstatus,
                        'error_message': ht.get('error', '') if not is_running else '',
                        'logs': logs,
                        'started_at': base_ts,
                        'completed_at': None if is_running else base_ts + timedelta(seconds=30),
                    },
                )

        # ---------- 4. Webhook 订阅（接收订阅 + 推送上报） ----------
        # 4a. 接收订阅：本系统订阅「外部任务中心」的状态推送（不参与投递）
        WebhookSubscription.objects.get_or_create(
            name='任务执行状态推送（模拟任务中心）',
            defaults={
                'url': 'https://task-center.example.com/hook/task-status',
                'events': ['process.started', 'task.completed', 'task.failed', 'process.completed'],
                'secret': 'demo-webhook-secret',
                'direction': WebhookSubscription.Direction.RECEIVE,
                'is_active': True,
            },
        )
        # 4b. 推送上报：本系统推送到外部平台（真实投递目标）
        WebhookSubscription.objects.get_or_create(
            name='审计事件上报（推送到审计平台）',
            defaults={
                'url': 'https://audit.example.com/hook/events',
                'events': ['process.started', 'task.created', 'task.completed', 'process.completed'],
                'secret': 'demo-audit-secret',
                'direction': WebhookSubscription.Direction.PUSH,
                'is_active': True,
            },
        )
        # 4c. 推送上报：变更事件 → 变更中心
        WebhookSubscription.objects.get_or_create(
            name='变更事件上报（推送到变更中心）',
            defaults={
                'url': 'https://change.example.com/hook/events',
                'events': ['process.started', 'task.completed', 'process.completed'],
                'secret': 'demo-change-secret',
                'direction': WebhookSubscription.Direction.PUSH,
                'is_active': True,
            },
        )

        # ---------- 5. 开放 API 接入方（对应「真实业务场景」①监控告警 / ②CI 流水线） ----------
        open_api_apps = [
            {
                'code': 'monitor_alert',
                'name': '监控告警平台',
                'api_key': 'demo_monitor_alert_key_2026',
                'desc': '监控探测到故障自动调开放 API 建单',
            },
            {
                'code': 'ci_pipeline',
                'name': 'CI 流水线',
                'api_key': 'demo_ci_pipeline_key_2026',
                'desc': '流水线/脚本调开放 API 发起工单',
            },
        ]
        for ad in open_api_apps:
            _, created = InitiatorApp.objects.get_or_create(
                code=ad['code'],
                defaults={
                    'name': ad['name'],
                    'api_key_hash': hash_api_key(ad['api_key']),
                    'is_active': True,
                },
            )
            if created:
                self.stdout.write(f"  开放 API 接入方：{ad['code']}（{ad['name']}）API Key={ad['api_key']}")

        # ---------- 6. 开放 API 调用统计（演示历史调用） ----------
        api_calls_seed = [
            ('monitor_alert', 201, True, 'DM-2026-101'),
            ('monitor_alert', 201, True, 'DM-2026-102'),
            ('ci_pipeline', 201, True, 'DM-2026-103'),
            ('cloud_manager', 201, True, 'DM-2026-104'),
            ('cloud_manager', 500, False, ''),
            ('cmdb_sync', 201, True, 'DM-2026-105'),
            ('it_service', 201, True, 'DM-2026-106'),
            ('permission_center', 201, True, 'DM-2026-107'),
        ]
        api_call_created = 0
        for code, status_code, success, instance_no in api_calls_seed:
            app = InitiatorApp.objects.filter(code=code).first()
            _, created = ApiCallLog.objects.get_or_create(
                app_code=code,
                instance_no=instance_no,
                status_code=status_code,
                defaults={
                    'app': app,
                    'method': 'POST',
                    'path': '/api/v1/process-instances/start/',
                    'duration_ms': 150,
                    'success': success,
                },
            )
            if created:
                api_call_created += 1
        if api_call_created:
            self.stdout.write(f'  开放 API 调用统计演示：新增 {api_call_created} 条')

        # ---------- 7. Webhook 投递记录（推送上报演示：审计/变更投递成功） ----------
        from apps.events.models import EventLog as _EventLog
        delivery_created = 0
        for sub in WebhookSubscription.objects.filter(direction=WebhookSubscription.Direction.PUSH):
            for evt_type in (sub.events or []):
                evt = _EventLog.objects.filter(type=evt_type).order_by('-created_at').first()
                if not evt:
                    continue
                _, created = WebhookDelivery.objects.get_or_create(
                    subscription=sub,
                    event=evt,
                    status=WebhookDelivery.Status.DELIVERED,
                    defaults={
                        'attempt': 1,
                        'last_response': '200 OK（模拟投递）',
                        'last_attempt_at': timezone.now(),
                    },
                )
                if created:
                    delivery_created += 1
        if delivery_created:
            self.stdout.write(f'  Webhook 投递记录演示：新增 {delivery_created} 条（审计/变更推送）')

        self.stdout.write(self.style.SUCCESS(
            f'✓ 补齐完成：新增实例 {created_instances}、节点任务 {created_tasks}、审批记录 {created_records}'
        ))
        self.stdout.write('  - 待办：admin 2 条（DM-2026-001/002）、xiaoli 1 条（DM-2026-003）')
        self.stdout.write('  - 已办：admin 2 条（DM-2026-011/012 审批通过）')
        self.stdout.write('  - 抄送：admin/xiaoming/xiaohong 均有抄送记录')
