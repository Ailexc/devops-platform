"""
办理节点「任务配置」自动执行引擎

支持：
- 多动作（每个动作 = 一个能力 + 字段映射）
- 串行 / 并行执行（并行等待全部完成，结果统一返回）
- 代理办理人：进入节点时从已配置办理人中随机选择（正常与异常均记录）
- 字段绑定来源：表单字段 / 上游节点输出 / 常量 / 串行前序动作输出
- 失败：不做重试，记录日志并将节点标记为异常，转代理办理人人工处理
- 重新执行：代理可重跑失败动作（串行从失败动作起续跑，并行只重跑失败动作）
"""
import logging
import random
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.capabilities.models import Capability, TaskJob
from apps.capabilities.services.executor import default_executor
from apps.processes.models import NodeTask, ProcessInstance

logger = logging.getLogger(__name__)
User = get_user_model()

# 办理人类型（与前端 FlowConstant ASSIGNEE 一致）
TRAN_SELF = 0
TRAN_SUPERIOR = 1
TRAN_DEPT_LEADER = 2
TRAN_ROLE = 3
TRAN_SPECIFIED = 4
TRAN_INITIATOR_CHOICE = 7


class AutoTaskError(Exception):
    """自动执行失败"""

    def __init__(self, action_key, message, job=None):
        self.action_key = action_key
        self.message = message
        self.job = job
        super().__init__(message)


def _append_log(job, level, message):
    logs = list(job.logs or [])
    logs.append({
        'ts': datetime.now().isoformat(timespec='seconds'),
        'level': level,
        'message': message,
    })
    job.logs = logs
    job.save(update_fields=['logs', 'updated_at'])


# ---------------------------------------------------------------------------
# 办理人解析（用于代理随机选择）
# ---------------------------------------------------------------------------
def resolve_transactor_ids(instance, node_config):
    """解析办理人配置为实际用户 ID 列表（发起人/上级/部门负责人/角色/指定成员/发起人自选）"""
    transactors = node_config.get('transactors') or []
    ids = []
    started_by = instance.started_by
    for t in transactors:
        ttype = t.get('transactorType')
        if ttype == TRAN_SELF:
            if started_by:
                ids.append(started_by.id)
        elif ttype in (TRAN_SUPERIOR, TRAN_DEPT_LEADER):
            if started_by:
                level = int(t.get('layer', 0) or 0) + 1
                manager = started_by.get_manager(level=level)
                if manager:
                    ids.append(manager.id)
                elif t.get('layerType') == 1:
                    # 最高上级向下：退化为取最高级主管
                    manager = started_by.get_manager(level=99)
                    if manager:
                        ids.append(manager.id)
        elif ttype == TRAN_ROLE:
            role_ids = t.get('roles') or []
            ids.extend(
                User.objects.filter(groups__id__in=role_ids, is_active=True)
                .values_list('id', flat=True)
            )
        elif ttype == TRAN_SPECIFIED:
            ids.extend(t.get('assignees') or [])
        elif ttype == TRAN_INITIATOR_CHOICE:
            # demo：发起人自选尚未在申请环节实现，暂以发起人本人兜底
            if started_by:
                ids.append(started_by.id)
    return list(dict.fromkeys(ids))


def pick_proxy(instance, node_config):
    """随机从已配置办理人中选一位代理办理人"""
    ids = resolve_transactor_ids(instance, node_config)
    if not ids:
        return None
    return random.choice(ids)


# ---------------------------------------------------------------------------
# 字段绑定解析
# ---------------------------------------------------------------------------
def get_node_output(instance, node_key):
    """读取某节点执行后的合并输出 {field: value}"""
    outputs = (instance.variables or {}).get('_node_outputs') or {}
    return outputs.get(node_key) or {}


def _save_node_outputs(instance, node_key, outputs):
    variables = dict(instance.variables or {})
    node_outputs = dict(variables.get('_node_outputs') or {})
    node_outputs[node_key] = outputs
    variables['_node_outputs'] = node_outputs
    instance.variables = variables
    instance.save(update_fields=['variables', 'updated_at'])


def resolve_action_input(instance, action, previous_outputs):
    """将动作的字段绑定解析为能力入参"""
    input_data = {}
    for bind in action.get('fieldBindings') or []:
        field = bind.get('capabilityField')
        if not field:
            continue
        source = bind.get('source', 'form')
        if source == 'form':
            input_data[field] = instance.variables.get(bind.get('formField'))
        elif source == 'constant':
            input_data[field] = bind.get('constant')
        elif source == 'upstream':
            node_out = get_node_output(instance, bind.get('upstreamNode'))
            input_data[field] = (node_out or {}).get(bind.get('upstreamField'))
        elif source == 'previous':
            prev = previous_outputs.get(bind.get('previousActionKey')) or {}
            input_data[field] = prev.get(bind.get('previousField'))
    return input_data


# ---------------------------------------------------------------------------
# 动作执行
# ---------------------------------------------------------------------------
def create_job(instance, node_task, node_key, action, input_data):
    capability = Capability.objects.filter(
        pk=action.get('capabilityId'), is_active=True,
    ).first()
    if capability is None:
        raise AutoTaskError(
            action.get('key'),
            f'能力不存在或已停用（{action.get("capabilityCode", "")}）',
        )
    sync = capability.execute_mode == Capability.ExecuteMode.SYNC
    job = TaskJob.objects.create(
        instance=instance,
        task=node_task,
        capability=capability,
        node_key=node_key,
        action_key=action.get('key', ''),
        action_name=action.get('name', capability.name),
        input_data=input_data or {},
        sync=sync,  # 同步：流程阻塞等待结果；异步：提交队列即返回，结果经队列消息/回调回写
        status=TaskJob.Status.QUEUED,
    )
    if sync:
        _append_log(job, 'info', f'动作「{job.action_name}」已创建，等待执行')
    else:
        _append_log(job, 'info', f'动作「{job.action_name}」已提交到执行队列（job_id={job.job_id}），流程无需等待，执行结果将通过队列消息/回调回写')
    return job


def _should_simulate_failure(instance, capability_code):
    """测试场景异常模拟：按实例变量标记模拟能力执行失败。

    标记从实例 variables 读取（发起时写入），跨进程生效——
    无论引擎在调用方进程（程序发起）还是 runserver 进程（HTTP 发起）执行，
    都能读到同一份 DB 数据，从而让「自动办理失败」场景真正复现。
    标记取值：'*' 表示任意能力失败；list 表示指定能力编码失败。
    """
    marker = (instance.variables or {}).get('_simulate_failure')
    if not marker:
        return False
    if marker == '*':
        return True
    if isinstance(marker, list):
        return capability_code in marker or capability_code.replace('.', '_') in marker
    return marker == capability_code


def execute_job(job):
    """执行单个动作并返回输出；失败抛出 AutoTaskError"""
    if job.sync:
        _append_log(job, 'info', f'开始执行动作「{job.action_name}」')
    else:
        _append_log(job, 'info', f'收到队列执行消息，开始执行动作「{job.action_name}」')
    _append_log(job, 'debug', f'入参：{job.input_data}')
    # 测试场景异常模拟：命中标记则直接失败（不调用真实能力）
    if _should_simulate_failure(job.instance, job.capability.code):
        msg = '模拟自动办理失败：连接执行队列超时，重试 3 次后仍失败'
        _append_log(job, 'error', f'动作执行失败：{msg}')
        job.status = TaskJob.Status.FAILED
        job.error_message = msg
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
        raise AutoTaskError(job.action_key, msg, job)
    try:
        output = default_executor.execute_capability(
            job_id=job.job_id,
            capability_code=job.capability.code,
            input_data=job.input_data,
        )
    except Exception as e:
        # 执行器异常兜底：标记失败并记录日志（与执行器内部失败语义一致）
        job.status = TaskJob.Status.FAILED
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
        _append_log(job, 'error', f'动作执行异常：{e}')
        raise AutoTaskError(job.action_key, str(e), job)
    if job.status == TaskJob.Status.FAILED:
        raise AutoTaskError(job.action_key, job.error_message, job)
    if job.sync:
        _append_log(job, 'info', f'动作「{job.action_name}」执行成功')
    else:
        _append_log(job, 'info', f'动作「{job.action_name}」执行成功，已通过队列消息/回调回写执行状态')
    return output


def _execute_actions(instance, node_task, node_key, actions, previous_outputs=None, only_keys=None):
    """
    按顺序执行一批动作（供串行与重新执行使用）。
    only_keys 指定时只执行这些动作（重新执行场景）。
    返回 {action_key: output}。
    """
    outputs = dict(previous_outputs or {})
    for action in actions:
        key = action.get('key')
        if only_keys is not None and key not in only_keys:
            continue
        # 已成功执行过的动作（串行重跑时跳过失败点之前的动作）
        if key in outputs and only_keys is not None:
            continue
        job = create_job(instance, node_task, node_key, action, resolve_action_input(instance, action, outputs))
        outputs[key] = execute_job(job)
    return outputs


def _join_node_success(instance, node_task, node_key, outputs):
    node_task.status = NodeTask.Status.COMPLETED
    node_task.result = 'success'
    node_task.save(update_fields=['status', 'result', 'updated_at'])
    _save_node_outputs(instance, node_key, outputs)
    # 推进到下一节点
    from .engine import ProcessEngine
    next_key = ProcessEngine._resolve_next_node(instance, node_key, instance.variables)
    if next_key:
        instance.current_node_key = next_key
        instance.save(update_fields=['current_node_key', 'updated_at'])
        ProcessEngine._advance(instance, instance.variables)


def _mark_node_abnormal(instance, node_task, error):
    node_task.status = NodeTask.Status.ABNORMAL
    node_task.result = 'failed'
    node_task.opinion = error.message
    node_task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])
    logger.warning(
        '自动执行异常: instance=%s node=%s action=%s error=%s',
        instance.instance_no, node_task.node_key, error.action_key, error.message,
    )


def run_auto_node(instance, node_config):
    """办理节点完全自动执行入口（由引擎 _advance 调用）"""
    proxy_id = pick_proxy(instance, node_config)
    node_task = NodeTask.objects.create(
        instance=instance,
        node_key=node_config['key'],
        node_name=node_config.get('name', '办理'),
        node_type=NodeTask.NodeType.HANDLE,
        status=NodeTask.Status.RUNNING,
        assignee_id=proxy_id,
        candidate_users=[proxy_id] if proxy_id else [],
    )
    proxy_name = ''
    if proxy_id:
        proxy = User.objects.filter(pk=proxy_id).first()
        proxy_name = proxy.get_full_name() or proxy.username if proxy else ''
    logger.info('自动办理开始: instance=%s node=%s proxy=%s', instance.instance_no, node_config['key'], proxy_name)
    execute_node_actions(instance, node_config, node_task)


def create_confirm_task(instance, node_config):
    """「自动执行+人工确认」：生成确认待办（随机办理人），确认后执行动作"""
    proxy_id = pick_proxy(instance, node_config)
    node_task = NodeTask.objects.create(
        instance=instance,
        node_key=node_config['key'],
        node_name=node_config.get('name', '办理'),
        node_type=NodeTask.NodeType.HANDLE,
        status=NodeTask.Status.PENDING,
        assignee_id=proxy_id,
        candidate_users=[proxy_id] if proxy_id else [],
    )
    return node_task


def execute_node_actions(instance, node_config, node_task):
    """
    执行节点动作（串行 / 并行），成功后完成节点并推进，失败标记异常。
    供「完全自动执行」与「人工确认后执行」两种模式复用。
    """
    node_key = node_config['key']
    task_config = node_config.get('taskConfig') or {}
    actions = task_config.get('actions') or []
    mode = task_config.get('executionMode', 'sequential')

    if not actions:
        _mark_node_abnormal(instance, node_task, AutoTaskError('', '未配置任何执行动作'))
        return

    try:
        if mode == 'parallel':
            # 并行：全部动作同时创建并执行，等待全部完成后统一判定
            jobs = [
                create_job(
                    instance, node_task, node_key, action,
                    resolve_action_input(instance, action, {}),
                )
                for action in actions
            ]
            outputs = {}
            errors = []
            for action, job in zip(actions, jobs):
                try:
                    outputs[action.get('key')] = execute_job(job)
                except AutoTaskError as e:
                    errors.append(e)
            if errors:
                first = errors[0]
                failed_keys = [e.action_key for e in errors]
                # 保留已成功动作的输出，便于排查与重新执行
                _save_node_outputs(instance, node_key, outputs)
                message = f'并行执行完成，以下动作失败：{", ".join(failed_keys) or "未知"}；{first.message}'
                raise AutoTaskError(first.action_key, message, first.job)
        else:
            # 串行：动作逐个执行，前序输出可供后续绑定
            outputs = _execute_actions(instance, node_task, node_key, actions)
        _join_node_success(instance, node_task, node_key, outputs)
    except AutoTaskError as e:
        _mark_node_abnormal(instance, node_task, e)


def rerun_node_actions(instance, node_task):
    """代理办理人重新执行失败动作；全部成功则完成节点并推进"""
    definition = instance.definition
    from .definition_convert import normalized_definition
    nodes = normalized_definition(definition.definition_json)['nodes']
    node_config = next((n for n in nodes if n.get('key') == node_task.node_key), None)
    if not node_config:
        raise AutoTaskError('', '未找到节点配置')
    task_config = node_config.get('taskConfig') or {}
    actions = task_config.get('actions') or []
    mode = task_config.get('executionMode', 'sequential')

    # 收集已成功的动作输出（历史任务）
    succeeded_outputs = {}
    for job in TaskJob.objects.filter(task=node_task, status=TaskJob.Status.SUCCEEDED):
        succeeded_outputs[job.action_key] = job.output_data

    if mode == 'parallel':
        failed_keys = list(
            TaskJob.objects.filter(task=node_task, status=TaskJob.Status.FAILED)
            .values_list('action_key', flat=True)
        )
        outputs = dict(succeeded_outputs)
        try:
            outputs.update(_execute_actions(instance, node_task, node_task.node_key, actions, previous_outputs=outputs, only_keys=failed_keys))
        except AutoTaskError as e:
            _mark_node_abnormal(instance, node_task, e)
            return
    else:
        # 串行：从第一个失败动作开始续跑（失败点之前的输出保留）
        order = [a.get('key') for a in actions]
        failed_indexes = [
            order.index(j.action_key)
            for j in TaskJob.objects.filter(task=node_task, status=TaskJob.Status.FAILED)
            if j.action_key in order
        ]
        start_index = min(failed_indexes) if failed_indexes else len(order)
        to_run = order[start_index:]
        outputs = dict(succeeded_outputs)
        try:
            outputs.update(_execute_actions(instance, node_task, node_task.node_key, actions, previous_outputs=outputs, only_keys=to_run))
        except AutoTaskError as e:
            _mark_node_abnormal(instance, node_task, e)
            return

    _join_node_success(instance, node_task, node_task.node_key, outputs)
