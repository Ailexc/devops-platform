"""
场景编排执行器：按步骤定义依次/并行执行原子操作，
每步骤落一条工单任务（TicketTask），支持重试，失败可人工重试。
"""
import logging
import uuid

from django.utils import timezone

logger = logging.getLogger(__name__)


def execute_scenario(ticket):
    """执行场景工单（由工单审批通过后调用）"""
    from provider.actions import ActionRegistry
    from ticket.models import TicketTask
    from .models import Scenario, ScenarioStep

    scenario = Scenario.objects.filter(id=ticket.scenario_id).first()
    if not scenario:
        ticket.status = 'failed'
        ticket.fail_reason = '场景定义不存在'
        ticket.finished_at = timezone.now()
        ticket.save()
        return

    steps = list(ScenarioStep.objects.filter(scenario=scenario, enabled=True).order_by('step_no'))
    base_params = dict(ticket.request_content or {})
    executed = []
    context = {}
    # 资源上下文注入：从资源详情发起的运维场景（如对某实例做安全组变更）
    if base_params.get('resource_id'):
        rid = base_params['resource_id']
        if base_params.get('resource_type') == 'instance':
            context['instance_id'] = rid
        elif base_params.get('resource_type') == 'security_group':
            context['security_group_id'] = rid
        context['resource_id'] = rid

    for step in steps:
        task = TicketTask.objects.create(
            ticket=ticket,
            task_type=f'step:{step.action_type}',
            provider_type='mock',
            request_id=str(uuid.uuid4()),
            max_retry=step.retry_max,
        )
        params = {**base_params, **context, **(step.action_params_template or {})}
        # 别名兼容：后续步骤需要实例 ID 时自动回填（如 write_cmdb 的 resource_id）
        if params.get('resource_id') is None and context.get('instance_id'):
            params['resource_id'] = context['instance_id']
        params.pop('impact_analysis', None)

        # 条件跳过：缺少声明参数时跳过（如从安全组上下文发起时无实例可绑定）
        missing = [k for k in (step.skip_if_missing or []) if k not in params and k not in context]
        if missing:
            task.status = 'success'
            task.finished_at = timezone.now()
            task.exec_log = f'步骤「{step.name}」已跳过（缺少参数: {", ".join(missing)}）'
            task.save()
            executed.append({
                'step_no': step.step_no,
                'name': step.name,
                'action_type': step.action_type,
                'status': 'skipped',
                'result': {'message': f'缺少参数跳过: {", ".join(missing)}'},
            })
            continue

        success = False
        attempt = 0

        while attempt <= task.max_retry:
            attempt += 1
            task.status = 'running'
            task.started_at = task.started_at or timezone.now()
            task.save()
            ticket.status = 'running'
            ticket.save()
            try:
                action = ActionRegistry.get(step.action_type)
                result = action.handler(params)
                task.status = 'success'
                task.finished_at = timezone.now()
                task.exec_log += f'\n[尝试{attempt}] 步骤「{step.name}」执行成功: {result.get("message", "")}'
                task.save()
                # 将步骤产物注入上下文，供后续步骤引用（按操作类型映射，避免互相覆盖）
                alias = {
                    'create_instance': 'instance_id',
                    'create_subnet': 'subnet_id',
                    'create_security_group': 'security_group_id',
                }
                key = alias.get(step.action_type)
                if key and result.get('resource_id') is not None:
                    context[key] = result['resource_id']
                if result.get('cloud_resource_id') is not None:
                    context['cloud_resource_id'] = result['cloud_resource_id']
                executed.append({
                    'step_no': step.step_no,
                    'name': step.name,
                    'action_type': step.action_type,
                    'status': 'success',
                    'result': result,
                })
                success = True
                break
            except Exception as e:  # noqa: BLE001
                logger.warning('场景 %s 步骤 %s 失败(第%s次): %s',
                               scenario.code, step.name, attempt, e)
                task.retry_count = attempt
                task.exec_log += f'\n[尝试{attempt}] 步骤「{step.name}」执行失败: {e}'
                task.status = 'pending' if attempt <= task.max_retry else 'failed'
                task.save()

        if not success:
            task.finished_at = timezone.now()
            task.save()
            ticket.status = 'failed'
            ticket.fail_reason = f'步骤「{step.name}」重试 {task.max_retry} 次后仍失败'
            ticket.finished_at = timezone.now()
            ticket.result_content = {'steps': executed}
            ticket.save()
            return

    ticket.status = 'success'
    ticket.finished_at = timezone.now()
    ticket.result_content = {'steps': executed}
    ticket.save()
