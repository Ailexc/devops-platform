"""
流程端到端测试服务（方案 B · HTTP 驱动）

用途：按「测试场景」对单个流程跑通完整生命周期（提交 → 审批 → 自动办理 → 完成），
记录每一步的真实 HTTP 调用（接口 / 请求 / 响应），供前端「测试模块」展示。

测试场景（TEST_SCENARIOS）按流程配置，支持多种终态：
- completed  正常完成：完整走通，实例完成
- running    流程进行中：发起后停留在审批节点，实例运行中（可到「我的待办」查看）
- abnormal   流程异常：自动办理动作 mock 失败，节点标记异常（可重新执行）
- rejected   审批驳回：首个审批驳回，实例终止

设计要点：
- 审批 / 办理推进：走真实 HTTP 接口（多用户 token 自动切换：admin 提单，审批按任务 assignee/candidate 切换用户）
- 发起：submit_scope 允许人员提交的流程走 HTTP 人员发起；仅程序发起的流程（如 permission_apply）用引擎程序发起（initiator_source 标注），避免依赖 app key 明文
- 真实落库：实例 / 待办 / 审批记录 / 办理日志均生成，系统「我的申请 / 待办 / 已办」可见
- 每次场景测试落库一条 TestScenarioRun，供前端「测试记录」展示
"""
import logging
import os
import time

import requests
from django.contrib.auth import get_user_model

from apps.processes.models import ProcessDefinition, ProcessInstance, NodeTask, TestScenarioRun

logger = logging.getLogger(__name__)

User = get_user_model()

# 容器内访问自身 API
BASE_URL = os.environ.get('E2E_API_URL', 'http://127.0.0.1:8000/api/v1')
TIMEOUT = 20
MAX_STEPS = 60

DEFAULT_OPINION = 'E2E 自动化测试通过（测试模块）'
REJECT_OPINION = '不同意（测试场景：审批驳回，验证驳回终止）'
INITIATOR_USERNAME = 'admin'

# 预设表单（合法值，走通完整生命周期）
PRESET_FORMS = {
    'server_apply': {
        'hostname': 'e2e-server-01', 'os': 'CentOS 7.9',
        'cpu': 8, 'memory': 16, 'disk_size': 100, 'data_disk_size': 50,
        'zone': 'cn-hangzhou', 'quantity': 1, 'network_segment': '10.0.1.0/24',
        'email': 'admin@company.com', 'reason': 'E2E 自动化测试：申请一台服务器验证全流程',
    },
    'permission_apply': {
        'system': 'cmdb_platform', 'account': 'e2e-user',
        'permission_level': 'readonly', 'permission_scope': 'CMDB 资产查询权限',
        'duration_type': 'permanent', 'duration_days': None,
        'notify_email': 'admin@company.com', 'reason': 'E2E 自动化测试：权限开通验证全流程',
    },
    'new_service_apply': {
        'service_name': 'e2e-order-service', 'service_type': 'api', 'environment': 'test',
        'language_runtime': 'go122', 'resource_request': '2C4G，20G 磁盘',
        'dependency': '', 'domain_request': '', 'db_required': False, 'db_type': None,
        'expected_date': '2026-09-01', 'notify_email': 'admin@company.com',
        'reason': 'E2E 自动化测试：新增服务验证全流程',
    },
    'server_restart': {
        'hostname': 'e2e-server-01', 'restart_type': 'system',
        'reason': 'E2E 自动化测试：重启主机验证全流程', 'urgency': 'normal',
        'downtime_expected': 30, 'notify_list': 'admin@company.com',
    },
}


# ---------------------------------------------------------------------------
# 测试场景配置（按流程 key 定义，每个场景有独立预设表单与运行模式）
#   mode: completed 正常完成 / running 流程进行中 / abnormal 流程异常 / rejected 审批驳回
# ---------------------------------------------------------------------------
TEST_SCENARIOS = {
    'server_apply': [
        {
            'key': 'happy',
            'name': '流程正常完成',
            'mode': 'completed',
            'desc': '提交申请 → 运维审批通过 → 自动创建主机 → 发送通知 → 流程完成',
            'form': {
                'hostname': 'e2e-server-01', 'os': 'CentOS 7.9',
                'cpu': 8, 'memory': 16, 'disk_size': 100, 'data_disk_size': 50,
                'zone': 'cn-hangzhou', 'quantity': 1, 'network_segment': '10.0.1.0/24',
                'email': 'admin@company.com', 'reason': 'E2E 自动化测试：申请一台服务器验证全流程',
            },
        },
        {
            'key': 'in_progress',
            'name': '流程进行中（审批中）',
            'mode': 'running',
            'desc': '提交申请后停留在「运维审批」节点，流程处于运行中，待办可继续处理',
            'form': {
                'hostname': 'e2e-server-pending', 'os': 'Ubuntu 22.04',
                'cpu': 8, 'memory': 32, 'disk_size': 100, 'data_disk_size': 100,
                'zone': 'cn-beijing', 'quantity': 1, 'network_segment': '10.0.2.0/24',
                'email': 'admin@company.com', 'reason': 'E2E 自动化测试：演示审批中的流程进行中状态',
            },
        },
        {
            'key': 'abnormal',
            'name': '流程异常（自动办理失败）',
            'mode': 'abnormal',
            'desc': '运维审批通过后，「自动创建主机」动作执行失败，节点标记异常（可重新执行）',
            'form': {
                'hostname': 'e2e-server-fail', 'os': 'Ubuntu 22.04',
                'cpu': 8, 'memory': 32, 'disk_size': 100, 'data_disk_size': 200,
                'zone': 'cn-beijing', 'quantity': 1, 'network_segment': '10.0.3.0/24',
                'email': 'admin@company.com', 'reason': 'E2E 自动化测试：演示自动办理失败进入异常',
            },
        },
    ],
    'new_service_apply': [
        {
            'key': 'happy',
            'name': '流程正常完成',
            'mode': 'completed',
            'desc': '提交申请 → 部门主管审批 → 运维评估 → 流程完成',
            'form': {
                'service_name': 'e2e-order-service', 'service_type': 'api', 'environment': 'test',
                'language_runtime': 'go122', 'resource_request': '2C4G，20G 磁盘',
                'dependency': '', 'domain_request': '', 'db_required': False, 'db_type': None,
                'expected_date': '2026-09-01', 'notify_email': 'admin@company.com',
                'reason': 'E2E 自动化测试：新增服务验证全流程',
            },
        },
        {
            'key': 'in_progress',
            'name': '流程进行中（审批中）',
            'mode': 'running',
            'desc': '提交申请后停留在「部门主管审批」节点，流程处于运行中',
            'form': {
                'service_name': 'e2e-service-pending', 'service_type': 'web', 'environment': 'test',
                'language_runtime': 'python312', 'resource_request': '1C2G，10G 磁盘',
                'dependency': '', 'domain_request': 'demo-pending.example.com',
                'db_required': False, 'db_type': None,
                'expected_date': '2026-09-15', 'notify_email': 'admin@company.com',
                'reason': 'E2E 自动化测试：演示新增服务审批中',
            },
        },
        {
            'key': 'rejected',
            'name': '流程驳回（审批驳回终止）',
            'mode': 'rejected',
            'desc': '部门主管审批驳回，流程终止（验证驳回场景）',
            'form': {
                'service_name': 'e2e-service-reject', 'service_type': 'api', 'environment': 'prod',
                'language_runtime': 'go122', 'resource_request': '8C16G，100G 磁盘',
                'dependency': '', 'domain_request': '', 'db_required': True, 'db_type': 'mysql',
                'expected_date': '2026-08-30', 'notify_email': 'admin@company.com',
                'reason': 'E2E 自动化测试：演示审批驳回终止',
            },
        },
    ],
    'permission_apply': [
        {
            'key': 'happy',
            'name': '流程正常完成',
            'mode': 'completed',
            'desc': '程序发起 → 自动授权（授权 + 通知）→ 流程完成',
            'form': {
                'system': 'cmdb_platform', 'account': 'e2e-user',
                'permission_level': 'readonly', 'permission_scope': 'CMDB 资产查询权限',
                'duration_type': 'permanent', 'duration_days': None,
                'notify_email': 'admin@company.com', 'reason': 'E2E 自动化测试：权限开通验证全流程',
            },
        },
        {
            'key': 'abnormal',
            'name': '流程异常（自动授权失败）',
            'mode': 'abnormal',
            'desc': '程序发起后，「自动授权」动作执行失败，节点标记异常',
            'form': {
                'system': 'cmdb_platform', 'account': 'e2e-user-fail',
                'permission_level': 'admin', 'permission_scope': 'CMDB 全量管理权限',
                'duration_type': 'permanent', 'duration_days': None,
                'notify_email': 'admin@company.com', 'reason': 'E2E 自动化测试：演示自动授权失败',
            },
        },
    ],
    'server_restart': [
        {
            'key': 'happy',
            'name': '流程正常完成',
            'mode': 'completed',
            'desc': '程序发起 → 自动重启（重启 + 通知）→ 流程完成',
            'form': {
                'hostname': 'e2e-server-01', 'restart_type': 'system',
                'reason': 'E2E 自动化测试：重启主机验证全流程', 'urgency': 'normal',
                'downtime_expected': 30, 'notify_list': 'admin@company.com',
            },
        },
        {
            'key': 'abnormal',
            'name': '流程异常（自动重启失败）',
            'mode': 'abnormal',
            'desc': '程序发起后，「自动重启」动作执行失败，节点标记异常',
            'form': {
                'hostname': 'e2e-server-fail', 'restart_type': 'system',
                'reason': 'E2E 自动化测试：演示自动重启失败', 'urgency': 'high',
                'downtime_expected': 10, 'notify_list': 'admin@company.com',
            },
        },
    ],
}


def get_scenarios(definition_key):
    """返回某流程的全部测试场景"""
    return TEST_SCENARIOS.get(definition_key, [])


def _resolve_scenario(definition_key, scenario_key):
    """按 key 解析场景；未指定时取第一个场景（默认 happy）"""
    scenarios = get_scenarios(definition_key)
    if not scenarios:
        return None
    if not scenario_key:
        return scenarios[0]
    for s in scenarios:
        if s.get('key') == scenario_key:
            return s
    return None


# ---------------------------------------------------------------------------
# HTTP 工具
# ---------------------------------------------------------------------------
def _post(path, token, payload=None):
    resp = requests.post(
        f'{BASE_URL}{path}',
        json=payload or {},
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        timeout=TIMEOUT,
    )
    data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
    return resp.status_code, data


def _login(username, password):
    code, data = _post('/auth/token/', None, {'username': username, 'password': password})
    if code >= 300 or 'access' not in data:
        raise RuntimeError(f'登录失败 {username}: {code} {data}')
    return data['access']


def _password_of(user):
    return 'admin123' if user.username == 'admin' else 'user123'


def _pick(keys, obj):
    return {k: obj.get(k) for k in keys if k in obj}


def _resolve_approver(task):
    """解析任务的审批/办理人：assignee → candidate[0] → 发起人（兜底，允许自批）"""
    if task.assignee:
        return task.assignee
    if task.candidate_users:
        return User.objects.filter(id__in=task.candidate_users).first()
    return task.instance.started_by


# ---------------------------------------------------------------------------
# E2E 主流程
# ---------------------------------------------------------------------------
def run_e2e(definition_id=None, definition_key=None, form_data=None, title='', scenario_key='') -> dict:
    if definition_id:
        definition = ProcessDefinition.objects.filter(pk=definition_id).first()
    else:
        definition = ProcessDefinition.objects.filter(key=definition_key).first()
    if not definition:
        return {'ok': False, 'error': '流程定义不存在', 'steps': []}

    # 解析测试场景：未配置场景的流程按旧逻辑跑完整生命周期
    scenario = _resolve_scenario(definition.key, scenario_key)
    mode = (scenario or {}).get('mode', 'completed')
    if scenario:
        form_data = scenario['form']
    else:
        form_data = form_data or (PRESET_FORMS.get(definition.key) or {})

    # 异常场景：注入 DB 标记（随 form_data 存入实例 variables，供 task_runner 跨进程模拟能力失败）
    if mode == 'abnormal':
        form_data = {**form_data, '_simulate_failure': '*'}
    # 展示用表单：剔除内部标记，避免在前端暴露测试参数
    display_form = {k: v for k, v in form_data.items() if k != '_simulate_failure'}

    steps = []
    admin_token = None
    started = time.time()

    def add_step(step, action, api, request_payload, response_payload, user='admin', ok=True, note='', method=None):
        method = method or ('POST' if action != '查询' else 'GET')
        # 归一化：api 参数里若已含方法前缀（如 "POST /auth/token/"），去掉避免与 method 重复展示
        if api.upper().startswith(('POST ', 'GET ')):
            api = api.split(' ', 1)[1]
        steps.append({
            'step': step,
            'action': action,
            'user': user,
            'api': api,
            'method': method,
            'request': request_payload,
            'response': response_payload,
            'ok': ok,
            'note': note,
        })

    # ---- 1. 登录（admin 提单） ----
    try:
        admin_token = _login(INITIATOR_USERNAME, _password_of(User.objects.get(username=INITIATOR_USERNAME)))
    except Exception as e:
        add_step(1, '登录', 'POST /auth/token/', {'username': INITIATOR_USERNAME}, {}, ok=False, note=str(e))
        return {'ok': False, 'error': '登录失败', 'steps': steps, 'summary': {'fail_count': 1}}

    # ---- 2. 发起流程 ----
    instance = None
    initiator_note = '人员发起（admin）'
    if definition.submit_scope == 'none':
        # 仅程序发起的流程：引擎程序发起（等价程序发起语义，标注来源）
        from .engine import ProcessEngine
        instance = ProcessEngine.start(
            definition=definition,
            form_data=form_data,
            started_by=User.objects.get(username=INITIATOR_USERNAME),
            business_key='',
            initiator_source='permission_center',
        )
        add_step(
            2, '程序发起', 'ProcessEngine.start(initiator=permission_center)',
            {'definition_key': definition.key, 'form_data': display_form},
            {'instance_no': instance.instance_no, 'status': instance.status},
            note='仅程序发起的流程，等价权限中心程序发起',
        )
    else:
        code, data = _post('/process-instances/start/', admin_token, {
            'definition_id': definition.id,
            'form_data': form_data,
        })
        ok = code < 300
        add_step(
            2, '发起流程', 'POST /process-instances/start/',
            {'definition_id': definition.id, 'form_data': display_form},
            _pick(['id', 'instance_no', 'status', 'current_node_key', 'definition_name'], data) if ok else data,
            ok=ok, note=initiator_note,
        )
        if not ok:
            return {'ok': False, 'error': data.get('detail') or '发起失败', 'steps': steps, 'summary': {'fail_count': 1}}
        instance = ProcessInstance.objects.filter(pk=data['id']).first()

    if instance is None:
        return {'ok': False, 'error': '实例创建失败', 'steps': steps, 'summary': {'fail_count': 1}}

    instance_id = instance.id
    step_no = 3

    # 已由循环驱动处理的节点任务（审批/确认办理），避免与自动办理补录重复
    processed_task_ids = set()

    def record_auto_handle_steps():
        """补录「完全自动执行」办理节点的执行步骤（引擎在审批完成后同步触发，无待办）"""
        nonlocal step_no
        from apps.capabilities.models import TaskJob
        handle_tasks = instance.node_tasks.filter(
            node_type=NodeTask.NodeType.HANDLE,
        ).order_by('id')
        for ht in handle_tasks:
            if ht.id in processed_task_ids:
                continue
            jobs = list(TaskJob.objects.filter(task=ht).order_by('created_at'))
            if not jobs:
                continue
            processed_task_ids.add(ht.id)
            proxy_name = ''
            if ht.assignee_id:
                proxy = User.objects.filter(pk=ht.assignee_id).first()
                if proxy:
                    proxy_name = proxy.get_full_name() or proxy.username
            ok = all(j.status == 'succeeded' for j in jobs)
            add_step(
                step_no, f'自动办理：{ht.node_name}',
                '（引擎自动执行 · task_runner）',
                {
                    'node_key': ht.node_key,
                    'actions': [
                        {
                            'key': j.action_key,
                            'name': j.action_name or (j.capability.code if j.capability else ''),
                            'status': j.status,
                        }
                        for j in jobs
                    ],
                },
                {
                    'jobs': [
                        {
                            'status': j.status,
                            'input': j.input_data,
                            'output': j.output_data,
                            'error': j.error_message,
                        }
                        for j in jobs
                    ],
                },
                user=proxy_name or '系统',
                ok=ok,
                note=f'{len(jobs)} 个动作 · 执行完成' if ok else f'{len(jobs)} 个动作 · 有失败',
                method='-',
            )
            step_no += 1

    def _drive_loop():
        """驱动审批/办理推进（completed / abnormal / rejected）"""
        nonlocal step_no
        rejected = False
        while step_no <= MAX_STEPS:
            tasks = NodeTask.objects.filter(
                instance_id=instance_id,
                status__in=[NodeTask.Status.PENDING, NodeTask.Status.CLAIMED, NodeTask.Status.ABNORMAL],
            ).order_by('id')
            if not tasks:
                break
            task = tasks[0]
            # 异常任务不再自动推进（停留在异常节点，供演示「重新执行」）
            if task.status == NodeTask.Status.ABNORMAL:
                break
            processed_task_ids.add(task.id)
            approver = _resolve_approver(task)
            if not approver:
                add_step(step_no, f'处理任务（{task.node_name}）', '-', {}, {}, ok=False, note='未解析到审批/办理人')
                break

            try:
                token = _login(approver.username, _password_of(approver))
            except Exception as e:
                add_step(step_no, f'登录 {approver.username}', 'POST /auth/token/', {}, {}, ok=False, note=str(e))
                break

            node_label = f'{task.node_name}（{task.get_node_type_display()}）'
            user_label = approver.get_full_name() or approver.username

            # 签收（仅 pending 需要；claimed 可跳过）
            if task.status == NodeTask.Status.PENDING:
                code, data = _post(f'/node-tasks/{task.id}/claim/', token)
                add_step(
                    step_no, f'签收：{node_label}', f'POST /node-tasks/{task.id}/claim/',
                    {}, _pick(['id', 'node_name', 'status', 'assignee_name'], data) if code < 300 else data,
                    user=user_label, ok=code < 300,
                )
                step_no += 1
                if code >= 300:
                    break

            # 完成：驳回场景在首个审批节点驳回；其余 approve
            is_reject = mode == 'rejected' and not rejected and task.node_type == NodeTask.NodeType.APPROVE
            result = 'reject' if is_reject else 'approve'
            opinion = REJECT_OPINION if is_reject else DEFAULT_OPINION
            code, data = _post(f'/node-tasks/{task.id}/complete/', token, {
                'result': result, 'opinion': opinion,
            })
            add_step(
                step_no, f'完成：{node_label}', f'POST /node-tasks/{task.id}/complete/',
                {'result': result, 'opinion': opinion},
                _pick(['id', 'node_name', 'status', 'result'], data) if code < 300 else data,
                user=user_label, ok=code < 300,
            )
            step_no += 1
            if code >= 300:
                break
            if is_reject:
                rejected = True
                break
            # 审批完成后，引擎可能已同步触发「完全自动执行」的办理节点 → 补录
            record_auto_handle_steps()
            # 异常模式：一旦出现异常节点即停止（供演示）
            if NodeTask.objects.filter(instance_id=instance_id, status=NodeTask.Status.ABNORMAL).exists():
                break

    # ---- 3. 按场景模式推进 ----
    if mode == 'running':
        # 流程进行中：发起后停留在首个待处理节点，不推进
        pending_tasks = instance.node_tasks.filter(
            status__in=[NodeTask.Status.PENDING, NodeTask.Status.CLAIMED],
        ).order_by('id')
        first_pending = pending_tasks.first()
        add_step(
            step_no, '流程进行中（停留在待处理节点）', '-', {},
            {
                'current_node_key': instance.current_node_key,
                'pending_tasks': [
                    {
                        'node_key': t.node_key,
                        'node_name': t.node_name,
                        'node_type': t.get_node_type_display(),
                        'status': t.get_status_display(),
                    }
                    for t in pending_tasks
                ],
            },
            ok=True,
            note=f'场景：流程进行中 — 已提交，等待「{(first_pending.node_name if first_pending else instance.current_node_key)}」处理',
            method='-',
        )
        step_no += 1
    else:
        # 先补录发起时已触发失败的自动办理（纯自动流程异常场景）
        record_auto_handle_steps()
        _drive_loop()
        # 循环退出后兜底补录（例如最后一步审批直接完成、无后续待办）
        record_auto_handle_steps()

    # ---- 4. 最终状态 ----
    instance = ProcessInstance.objects.filter(pk=instance_id).first()
    add_step(
        step_no, '查询最终状态', 'GET /process-instances/{id}/', {},
        _pick(['id', 'instance_no', 'status', 'status_display', 'current_node_key'], {
            'id': instance.id, 'instance_no': instance.instance_no, 'status': instance.status,
            'status_display': instance.get_status_display(), 'current_node_key': instance.current_node_key,
        }),
    )

    ok_count = sum(1 for s in steps if s['ok'])
    fail_count = len(steps) - ok_count

    # 场景预期达成度：ok = 场景到达了预期的终态（异常/进行中/驳回也算「符合预期的执行成功」）
    if mode == 'completed':
        scenario_ok = instance.status == ProcessInstance.Status.COMPLETED
    elif mode == 'running':
        scenario_ok = instance.status == ProcessInstance.Status.RUNNING
    elif mode == 'abnormal':
        scenario_ok = instance.status == ProcessInstance.Status.RUNNING and instance.node_tasks.filter(
            status=NodeTask.Status.ABNORMAL,
        ).exists()
    elif mode == 'rejected':
        scenario_ok = instance.status == ProcessInstance.Status.TERMINATED
    else:
        scenario_ok = fail_count == 0

    # ---- 5. 落库测试场景运行记录 ----
    TestScenarioRun.objects.create(
        definition=definition,
        instance=instance,
        scenario_key=(scenario or {}).get('key', ''),
        scenario_name=(scenario or {}).get('name', '流程正常完成'),
        scenario_mode=mode,
        ok=scenario_ok,
        summary={
            'steps_count': len(steps),
            'ok_count': ok_count,
            'fail_count': fail_count,
            'instance_status': instance.status,
            'instance_status_display': instance.get_status_display(),
        },
        duration_ms=int((time.time() - started) * 1000),
    )

    return {
        'ok': scenario_ok,
        'definition': {'id': definition.id, 'key': definition.key, 'name': definition.name},
        'scenario': {
            'key': (scenario or {}).get('key', ''),
            'name': (scenario or {}).get('name', '流程正常完成'),
            'mode': mode,
        },
        'instance': {
            'id': instance.id, 'instance_no': instance.instance_no,
            'status': instance.status, 'status_display': instance.get_status_display(),
        },
        'steps': steps,
        'summary': {
            'steps_count': len(steps), 'ok_count': ok_count, 'fail_count': fail_count,
            'expected_status': instance.get_status_display(),
        },
    }
