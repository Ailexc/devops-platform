"""
流程引擎核心类

负责流程的启动、推进、审批、转办、挂起/恢复、终止等全部操作。
所有推进操作都在单个数据库事务内完成（select_for_update）。
"""
import logging
import re
from typing import Optional

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.processes.models import (
    ProcessDefinition,
    ProcessInstance,
    NodeTask,
    TaskInstance,
    ApprovalRecord,
)
from apps.common.utils import generate_instance_no

logger = logging.getLogger(__name__)


def evaluate_condition(expression: str, variables: dict) -> bool:
    """
    安全地评估条件表达式（与流程推进共享）。
    支持简单比较运算: amount > 10000, status == 'approved', department == 'tech'
    对数字变量自动做类型兼容：表单提交数字，而条件字面量可能是 '8' 这样的字符串，
    直接 eval `cpu > '8'` 会抛类型错误，这里把数字变量的数字字符串字面量转成数字。
    """
    if not expression:
        return True

    expr = expression
    for var_name, val in variables.items():
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            expr = re.sub(
                rf"{re.escape(str(var_name))}\s*(==|!=|>=|<=|>|<)\s*['\"]([+-]?\d+(?:\.\d+)?)['\"]",
                rf"{var_name} \1 \2",
                expr,
            )

    safe_namespace = {
        **variables,
        '__builtins__': {},  # 禁止调用任何内置函数
    }
    try:
        result = eval(expr, safe_namespace)
        return bool(result)
    except Exception as e:
        logger.warning(f'条件评估失败: expression={expression}, error={e}')
        return False


class ProcessEngine:
    """
    流程引擎核心。

    definition_json 示例结构:
    {
        "nodes": [
            {"key": "start", "type": "start", "name": "开始"},
            {"key": "approve", "type": "approve", "name": "主管审批",
             "approval_type": "single", "assignees": [{"type": "manager", "level": 1}]},
            {"key": "condition_1", "type": "condition", "name": "金额判断",
             "conditions": [{"expression": "amount > 10000", "next_node": "manager_approve"},
                           {"default": "end"}]},
            {"key": "manager_approve", "type": "approve", "name": "总监审批",
             "approval_type": "single", "assignees": [{"type": "manager", "level": 2}]},
            {"key": "service_notify", "type": "service", "name": "发送通知",
             "capability_code": "mail_send"},
            {"key": "cc_finance", "type": "cc", "name": "抄送财务",
             "candidates": [{"type": "group", "name": "finance"}]},
            {"key": "end", "type": "end", "name": "结束"}
        ],
        "edges": [
            {"from": "start", "to": "approve"},
            {"from": "approve", "to": "condition_1"},
            {"from": "condition_1", "to": "manager_approve", "label": "金额>10000"},
            {"from": "condition_1", "to": "end", "label": "默认"},
            {"from": "manager_approve", "to": "service_notify"},
            {"from": "service_notify", "to": "cc_finance"},
            {"from": "cc_finance", "to": "end"}
        ]
    }
    """

    # ========================================================================
    # Public API
    # ========================================================================

    @classmethod
    def start(cls, definition: ProcessDefinition, form_data: dict, started_by, business_key: str = '', initiator_source: str = '') -> ProcessInstance:
        """
        启动流程实例。
        1. 创建 ProcessInstance
        2. 创建第一条 ApprovalRecord
        3. 推进到第一个节点

        initiator_source: 发起来源。人员发起为空；程序发起记录程序标识。
        """
        with transaction.atomic():
            instance = ProcessInstance.objects.select_for_update().create(
                definition=definition,
                instance_no=generate_instance_no(),
                variables=form_data,
                business_key=business_key or None,
                started_by=started_by,
                status=ProcessInstance.Status.RUNNING,
            )
            # 记录发起
            ApprovalRecord.objects.create(
                instance=instance,
                user=started_by,
                action='comment',
                opinion='发起流程',
                initiator_source=initiator_source,
            )
            # 发布启动事件
            cls._publish_event(
                'process.started',
                instance,
                payload={
                    'instance_no': instance.instance_no,
                    'definition': definition.key,
                    'initiator_source': initiator_source,
                },
            )
            # 推进
            cls._advance(instance, form_data)
            logger.info(f'流程启动: {instance.instance_no}, definition={definition.key}')
            return instance

    @classmethod
    @transaction.atomic
    def claim(cls, task_id: int, user) -> NodeTask:
        """签收任务（会签/或签场景下，候选人主动签收）"""
        task = NodeTask.objects.select_for_update().get(pk=task_id)
        cls._assert_task_pending(task)
        cls._assert_user_is_candidate(task, user)

        task.assignee = user
        task.status = NodeTask.Status.CLAIMED
        task.save(update_fields=['assignee', 'status', 'updated_at'])
        logger.info(f'任务签收: task={task.id}, user={user.username}')
        return task

    @classmethod
    @transaction.atomic
    def complete(cls, task_id: int, user, result: str = 'approve', opinion: str = '') -> NodeTask:
        """
        完成任务（审批通过 / 办理完成）。
        对于会签场景，只有当所有候选人都完成后才真正推进。
        """
        task = NodeTask.objects.select_for_update().get(pk=task_id)
        cls._assert_task_pending_or_claimed(task)
        cls._assert_user_authorized(task, user)
        was_abnormal = task.status == NodeTask.Status.ABNORMAL
        was_confirm_pending = task.status in (
            NodeTask.Status.PENDING,
            NodeTask.Status.CLAIMED,
        ) and cls._is_confirm_node(task)

        # 记录审批
        ApprovalRecord.objects.create(
            instance=task.instance,
            task=task,
            user=user,
            action=result,
            opinion=opinion,
        )

        task.result = result
        task.opinion = opinion

        if task.approval_type == NodeTask.ApprovalType.COUNTERSIGN:
            cls._handle_countersign(task, user, result, opinion)
        elif task.approval_type == NodeTask.ApprovalType.OR_SIGN:
            # 或签：一人通过即完成
            task.status = NodeTask.Status.COMPLETED
            task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])
            cls._advance(task.instance, task.instance.variables)
        else:
            # 单人审批
            if was_abnormal:
                # 异常任务由代理「标记处理完成」：直接从该节点推进，不再重新触发自动执行
                task.status = NodeTask.Status.COMPLETED
                task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])
                next_key = cls._resolve_next_node(task.instance, task.node_key, task.instance.variables)
                if next_key:
                    task.instance.current_node_key = next_key
                    task.instance.save(update_fields=['current_node_key', 'updated_at'])
                    cls._advance(task.instance, task.instance.variables)
            elif was_confirm_pending:
                # 「自动执行+人工确认」：办理人确认（已记录办理说明）后，执行节点动作
                task.status = NodeTask.Status.RUNNING
                task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])
                from .task_runner import execute_node_actions
                execute_node_actions(
                    task.instance,
                    cls._find_node_config(task.instance, task.node_key),
                    task,
                )
            else:
                task.status = NodeTask.Status.COMPLETED
                task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])
                cls._advance(task.instance, task.instance.variables)

        cls._publish_event(
            'task.completed',
            task.instance,
            task=task,
            payload={'node_key': task.node_key, 'node_name': task.node_name, 'result': result},
        )
        logger.info(f'任务完成: task={task.id}, result={result}')
        return task

    @classmethod
    @transaction.atomic
    def delegate(cls, task_id: int, from_user, to_user) -> NodeTask:
        """转办：将任务转给其他人"""
        task = NodeTask.objects.select_for_update().get(pk=task_id)
        cls._assert_task_pending_or_claimed(task)
        cls._assert_user_authorized(task, from_user)

        # 记录
        ApprovalRecord.objects.create(
            instance=task.instance,
            task=task,
            user=from_user,
            action='delegate',
            opinion=f'转办给 {to_user.username}',
        )

        task.assignee = to_user
        task.status = NodeTask.Status.PENDING
        task.candidate_users = [to_user.id]
        task.save(update_fields=['assignee', 'status', 'candidate_users', 'updated_at'])
        logger.info(f'任务转办: task={task.id}, from={from_user.username}, to={to_user.username}')
        return task

    @classmethod
    @transaction.atomic
    def reject(cls, task_id: int, user, opinion: str = '') -> NodeTask:
        """驳回任务"""
        task = NodeTask.objects.select_for_update().get(pk=task_id)
        cls._assert_task_pending_or_claimed(task)
        cls._assert_user_authorized(task, user)

        ApprovalRecord.objects.create(
            instance=task.instance,
            task=task,
            user=user,
            action='reject',
            opinion=opinion,
        )

        task.status = NodeTask.Status.COMPLETED
        task.result = 'reject'
        task.opinion = opinion
        task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])

        # 驳回 → 终止实例（FSM 转换，禁止直接改 status）
        instance = task.instance
        instance.terminate()
        # 指针回到驳回节点（此前已推进到下一节点），便于详情页展示终止位置
        instance.current_node_key = task.node_key
        instance.ended_at = timezone.now()
        instance.save(update_fields=['status', 'current_node_key', 'ended_at', 'updated_at'])

        # 取消后续所有待办
        NodeTask.objects.filter(
            instance=instance,
            status__in=[NodeTask.Status.PENDING, NodeTask.Status.CLAIMED],
        ).update(status=NodeTask.Status.CANCELLED)

        cls._publish_event(
            'task.rejected',
            instance,
            task=task,
            payload={'node_key': task.node_key, 'node_name': task.node_name, 'opinion': opinion},
        )
        cls._publish_event(
            'process.terminated',
            instance,
            payload={'instance_no': instance.instance_no, 'reason': 'rejected'},
        )
        logger.info(f'任务驳回: task={task.id}, instance={instance.instance_no}')
        return task

    @classmethod
    def suspend(cls, instance_id: int) -> ProcessInstance:
        """挂起流程"""
        instance = ProcessInstance.objects.get(pk=instance_id)
        instance.suspend()
        instance.save(update_fields=['status', 'updated_at'])
        logger.info(f'流程挂起: {instance.instance_no}')
        return instance

    @classmethod
    def resume(cls, instance_id: int) -> ProcessInstance:
        """恢复流程"""
        instance = ProcessInstance.objects.get(pk=instance_id)
        instance.resume()
        instance.save(update_fields=['status', 'updated_at'])
        logger.info(f'流程恢复: {instance.instance_no}')
        return instance

    @classmethod
    def terminate(cls, instance_id: int, user) -> ProcessInstance:
        """终止流程"""
        with transaction.atomic():
            instance = ProcessInstance.objects.select_for_update().get(pk=instance_id)
            instance.terminate()
            instance.ended_at = timezone.now()
            instance.save(update_fields=['status', 'ended_at', 'updated_at'])

            # 取消所有待办
            NodeTask.objects.filter(
                instance=instance,
                status__in=[NodeTask.Status.PENDING, NodeTask.Status.CLAIMED],
            ).update(status=NodeTask.Status.CANCELLED)

            ApprovalRecord.objects.create(
                instance=instance,
                user=user,
                action='comment',
                opinion='终止流程',
            )
            cls._publish_event(
                'process.terminated',
                instance,
                payload={'instance_no': instance.instance_no, 'by': user.username},
            )
            logger.info(f'流程终止: {instance.instance_no}, by={user.username}')
            return instance

    # ========================================================================
    # Internal helpers
    # ========================================================================

    @classmethod
    def _publish_event(cls, event_type: str, instance, task=None, payload: dict = None):
        """发布领域事件（事件总线）：写入 EventLog 并触发 Webhook 投递"""
        try:
            from apps.events.services.event_bus import EventBus
            EventBus.publish(
                event_type=event_type,
                instance=instance,
                task=task,
                payload=payload or {},
            )
        except Exception as e:  # 事件发布失败不影响流程主流程
            logger.warning(f'事件发布失败: {event_type}, error={e}')

    @classmethod
    def _advance(cls, instance: ProcessInstance, variables: dict):
        """
        内部推进方法：根据当前节点找到下一个节点，创建任务或完成实例。
        """
        definition = instance.definition
        from .definition_convert import normalized_definition
        flow_def = normalized_definition(definition.definition_json)
        nodes = flow_def['nodes']
        edges = flow_def['edges']

        if not instance.current_node_key:
            # 还没开始，找到 start 节点
            start_node = next((n for n in nodes if n.get('type') == 'start'), None)
            if start_node:
                instance.current_node_key = start_node['key']
                instance.save(update_fields=['current_node_key', 'updated_at'])
                # start 节点直接推进
                cls._advance(instance, variables)
            return

        # 找到当前节点
        current_node = next((n for n in nodes if n['key'] == instance.current_node_key), None)
        if not current_node:
            logger.error(f'找不到当前节点: {instance.current_node_key}')
            return

        node_type = current_node.get('type', '')

        if node_type in ('start', 'gateway', 'trigger'):
            # 找到下一条边，推进
            next_key = cls._resolve_next_node(instance, current_node['key'], variables)
            if next_key:
                instance.current_node_key = next_key
                instance.save(update_fields=['current_node_key', 'updated_at'])
                cls._advance(instance, variables)

        elif node_type in ('approve', 'handle'):
            # 创建审批/办理任务，等待处理；同时把指针推进到下一节点，
            # 任务完成后 _advance 从下一节点继续，避免重复创建任务
            if node_type == 'handle':
                task_mode = (current_node.get('taskConfig') or {}).get('mode', 'manual')
                if task_mode == 'auto':
                    # 「任务配置」完全自动执行：交给任务执行器（串行/并行、日志、异常转人工）
                    from .task_runner import run_auto_node
                    run_auto_node(instance, current_node)
                    return
                if task_mode == 'confirm':
                    # 「任务配置」自动执行+人工确认：生成确认待办（随机办理人），确认后执行动作
                    from .task_runner import create_confirm_task
                    create_confirm_task(instance, current_node)
                    return
            cls._create_tasks_for_node(instance, current_node)
            next_key = cls._resolve_next_node(instance, current_node['key'], variables)
            if next_key:
                instance.current_node_key = next_key
                instance.save(update_fields=['current_node_key', 'updated_at'])

        elif node_type == 'service':
            # 服务调用节点 → 创建 TaskJob（由 capabilities app 处理）
            cls._create_service_job(instance, current_node)

        elif node_type == 'cc':
            # 抄送节点 → 自动创建并完成
            cls._handle_cc_node(instance, current_node)

        elif node_type == 'condition':
            # 条件节点 → 求值后跳转
            next_key = cls._evaluate_condition_node(instance, current_node, variables)
            if next_key:
                instance.current_node_key = next_key
                instance.save(update_fields=['current_node_key', 'updated_at'])
                cls._advance(instance, variables)

        elif node_type == 'end':
            # 结束节点 → 完成实例
            instance.complete()
            instance.ended_at = timezone.now()
            instance.save(update_fields=['status', 'ended_at', 'updated_at'])
            cls._publish_event(
                'process.completed',
                instance,
                payload={'instance_no': instance.instance_no},
            )
            logger.info(f'流程完成: {instance.instance_no}')

    @classmethod
    def _resolve_next_node(cls, instance, current_node_key: str, variables: dict) -> Optional[str]:
        """根据当前节点 Key 和变量，找到下一个节点 Key"""
        from .definition_convert import normalized_definition
        edges = normalized_definition(instance.definition.definition_json)['edges']
        outgoing = [e for e in edges if e.get('from') == current_node_key]

        if not outgoing:
            return None

        if len(outgoing) == 1:
            return outgoing[0].get('to')

        # 多条边：按优先级求值条件
        for edge in outgoing:
            condition = edge.get('condition')
            if condition and cls._evaluate_condition(condition, variables):
                return edge.get('to')

        # 没有条件匹配，走默认（最后一条）
        return outgoing[-1].get('to')

    @classmethod
    def _evaluate_condition_node(cls, instance, node_config: dict, variables: dict) -> Optional[str]:
        """条件判断节点：遍历 outgoing edges，求值"""
        from .definition_convert import normalized_definition
        edges = normalized_definition(instance.definition.definition_json)['edges']
        outgoing = [e for e in edges if e.get('from') == node_config['key']]

        for edge in outgoing:
            condition = edge.get('condition')
            if condition and cls._evaluate_condition(condition, variables):
                return edge.get('to')

        # 走 default
        default_edge = next((e for e in outgoing if e.get('is_default')), None)
        if default_edge:
            return default_edge.get('to')
        return outgoing[-1]['to'] if outgoing else None

    @classmethod
    def _evaluate_condition(cls, expression: str, variables: dict) -> bool:
        """安全评估条件表达式（委托给模块级 evaluate_condition）"""
        return evaluate_condition(expression, variables)

    @classmethod
    def _resolve_assignees(cls, node_config: dict, instance, variables: dict) -> list[int]:
        """
        解析节点配置中的候选人。
        支持:
          - {"type": "user", "id": 1} → 直接指定用户
          - {"type": "manager", "level": 1} → 部门主管
          - {"type": "variable", "key": "approver_id"} → 从变量中读取
          - {"type": "group", "name": "finance"} → 部门成员
        """
        assignee_configs = node_config.get('assignees', [])
        if not assignee_configs:
            return []

        from django.contrib.auth import get_user_model
        from apps.accounts.models import Department

        User = get_user_model()
        user_ids = []

        for cfg in assignee_configs:
            # ---- Beeflow 设计器格式：assigneeType ----
            if 'assigneeType' in cfg:
                atype = cfg.get('assigneeType')
                started_by = instance.started_by
                if atype == 0:  # 发起人本人
                    if started_by:
                        user_ids.append(started_by.id)
                elif atype in (1, 2):  # 直属上级 / 部门负责人
                    if started_by:
                        level = int(cfg.get('layer', 0) or 0) + 1
                        manager = started_by.get_manager(level=level)
                        if manager:
                            user_ids.append(manager.id)
                        elif cfg.get('layerType') == 1:  # 最高向上
                            manager = started_by.get_manager(level=99)
                            if manager:
                                user_ids.append(manager.id)
                elif atype == 3:  # 角色
                    role_ids = cfg.get('roles') or []
                    user_ids.extend(
                        User.objects.filter(groups__id__in=role_ids, is_active=True)
                        .values_list('id', flat=True)
                    )
                elif atype == 4:  # 指定用户
                    user_ids.extend(cfg.get('assignees') or [])
                elif atype == 7:  # 发起人自选（demo 兜底发起人）
                    if started_by:
                        user_ids.append(started_by.id)
                continue

            # ---- 引擎平铺格式：type ----
            cfg_type = cfg.get('type', '')

            if cfg_type == 'user':
                user_ids.append(cfg['id'])

            elif cfg_type == 'manager':
                level = cfg.get('level', 1)
                if instance.started_by:
                    manager = instance.started_by.get_manager(level=level)
                    if manager:
                        user_ids.append(manager.id)

            elif cfg_type == 'variable':
                val = variables.get(cfg.get('key', ''))
                if isinstance(val, int):
                    user_ids.append(val)
                elif isinstance(val, list):
                    user_ids.extend(val)

            elif cfg_type == 'group':
                dept_name = cfg.get('name', '')
                dept = Department.objects.filter(name=dept_name).first()
                if dept:
                    user_ids.extend(dept.members.values_list('id', flat=True))

        return list(set(user_ids))

    @classmethod
    def _create_tasks_for_node(cls, instance, node_config: dict):
        """为审批/办理节点创建任务"""
        candidate_ids = cls._resolve_assignees(node_config, instance, instance.variables)
        approval_type = node_config.get('approval_type', 'single')

        if approval_type == 'countersign':
            # 会签：为每个候选人创建一个 NodeTask
            for uid in candidate_ids:
                NodeTask.objects.create(
                    instance=instance,
                    node_key=node_config['key'],
                    node_name=node_config.get('name', ''),
                    node_type=node_config.get('type', 'approve'),
                    approval_type=NodeTask.ApprovalType.COUNTERSIGN,
                    candidate_users=candidate_ids,
                    status=NodeTask.Status.PENDING,
                )
        elif approval_type == 'or_sign':
            # 或签：创建一个 NodeTask，所有候选人都可处理
            NodeTask.objects.create(
                instance=instance,
                node_key=node_config['key'],
                node_name=node_config.get('name', ''),
                node_type=node_config.get('type', 'approve'),
                approval_type=NodeTask.ApprovalType.OR_SIGN,
                candidate_users=candidate_ids,
                status=NodeTask.Status.PENDING,
            )
        else:
            # 单人审批：创建一个 NodeTask，assign 第一个候选人
            first_user = candidate_ids[0] if candidate_ids else None
            NodeTask.objects.create(
                instance=instance,
                node_key=node_config['key'],
                node_name=node_config.get('name', ''),
                node_type=node_config.get('type', 'approve'),
                approval_type=NodeTask.ApprovalType.SINGLE,
                assignee_id=first_user,
                candidate_users=candidate_ids,
                status=NodeTask.Status.PENDING,
            )

        cls._publish_event(
            'task.created',
            instance,
            payload={
                'node_key': node_config['key'],
                'node_name': node_config.get('name', ''),
                'node_type': node_config.get('type', 'approve'),
                'approval_type': approval_type,
            },
        )

    @classmethod
    def _handle_countersign(cls, task: NodeTask, user, result: str, opinion: str):
        """
        会签处理：
        - 更新 countersign 字段记录每个人的审批状态
        - 当所有候选人都完成时，才真正推进
        """
        countersign = task.countersign or {}
        countersign[str(user.id)] = {
            'result': result,
            'opinion': opinion,
            'time': timezone.now().isoformat(),
        }
        task.countersign = countersign

        # 检查是否所有人都已审批
        all_done = all(
            str(uid) in countersign
            for uid in task.candidate_users
        )

        if all_done:
            # 检查是否全部通过
            all_approve = all(
                countersign[str(uid)].get('result') == 'approve'
                for uid in task.candidate_users
            )
            task.status = NodeTask.Status.COMPLETED
            task.result = 'approve' if all_approve else 'reject'
            task.save(update_fields=['status', 'result', 'countersign', 'updated_at'])
            cls._advance(task.instance, task.instance.variables)
        else:
            task.save(update_fields=['countersign', 'updated_at'])

    @classmethod
    def _create_service_job(cls, instance, node_config: dict):
        """创建服务调用任务（异步由 capabilities executor 处理）"""
        from apps.capabilities.models import TaskJob, Capability
        from apps.common.utils import generate_job_id

        capability_code = node_config.get('capability_code', '')
        capability = Capability.objects.filter(code=capability_code, is_active=True).first()

        if not capability:
            logger.error(f'能力不存在或未启用: {capability_code}')
            # 跳过该节点
            next_key = cls._resolve_next_node(instance, node_config['key'], instance.variables)
            if next_key:
                instance.current_node_key = next_key
                instance.save(update_fields=['current_node_key', 'updated_at'])
                cls._advance(instance, instance.variables)
            return

        # 创建待办 NodeTask
        task = NodeTask.objects.create(
            instance=instance,
            node_key=node_config['key'],
            node_name=node_config.get('name', ''),
            node_type=NodeTask.NodeType.SERVICE,
            status=NodeTask.Status.PENDING,
        )

        # 创建 TaskJob
        input_data = node_config.get('input_template', {})
        # 用变量替换模板中的占位符
        for key, val in input_data.items():
            if isinstance(val, str) and val.startswith('${') and val.endswith('}'):
                var_key = val[2:-1]
                input_data[key] = instance.variables.get(var_key, val)

        TaskJob.objects.create(
            instance=instance,
            task=task,
            capability=capability,
            job_id=generate_job_id(),
            input_data=input_data,
            sync=capability.execute_mode == 'sync',
        )

    @classmethod
    def _handle_cc_node(cls, instance, node_config: dict):
        """处理抄送节点：创建抄送记录，自动完成"""
        candidate_ids = cls._resolve_assignees(node_config, instance, instance.variables)

        task = NodeTask.objects.create(
            instance=instance,
            node_key=node_config['key'],
            node_name=node_config.get('name', ''),
            node_type=NodeTask.NodeType.CC,
            candidate_users=candidate_ids,
            status=NodeTask.Status.COMPLETED,  # 抄送自动完成
        )

        # 记录审批
        for uid in candidate_ids:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(pk=uid)
                ApprovalRecord.objects.create(
                    instance=instance,
                    task=task,
                    user=user,
                    action='cc',
                    opinion='已抄送',
                )
            except User.DoesNotExist:
                pass

        # 推进
        next_key = cls._resolve_next_node(instance, node_config['key'], instance.variables)
        if next_key:
            instance.current_node_key = next_key
            instance.save(update_fields=['current_node_key', 'updated_at'])
            cls._advance(instance, instance.variables)

    # ========================================================================
    # Assertion helpers
    # ========================================================================

    @classmethod
    def _assert_task_pending(cls, task: NodeTask):
        if task.status not in (NodeTask.Status.PENDING,):
            from apps.common.exceptions import TaskAlreadyCompletedError
            raise TaskAlreadyCompletedError()

    @classmethod
    def _assert_task_pending_or_claimed(cls, task: NodeTask):
        if task.status not in (NodeTask.Status.PENDING, NodeTask.Status.CLAIMED, NodeTask.Status.ABNORMAL):
            from apps.common.exceptions import TaskAlreadyCompletedError
            raise TaskAlreadyCompletedError()

    @classmethod
    def _assert_user_is_candidate(cls, task: NodeTask, user):
        if user.id not in task.candidate_users and task.assignee_id != user.id:
            from apps.common.exceptions import PermissionDeniedError
            raise PermissionDeniedError()

    @classmethod
    def _assert_user_authorized(cls, task: NodeTask, user):
        if task.assignee_id and task.assignee_id != user.id:
            if user.id not in task.candidate_users:
                from apps.common.exceptions import PermissionDeniedError
                raise PermissionDeniedError()

    @classmethod
    def _find_node_config(cls, instance, node_key):
        from .definition_convert import normalized_definition
        nodes = normalized_definition(instance.definition.definition_json)['nodes']
        return next((n for n in nodes if n.get('key') == node_key), None)

    @classmethod
    def _is_confirm_node(cls, task):
        node = cls._find_node_config(task.instance, task.node_key)
        return bool(node and (node.get('taskConfig') or {}).get('mode') == 'confirm')
