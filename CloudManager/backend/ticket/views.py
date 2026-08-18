import uuid
import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import TicketOrder, TicketApproval, TicketTask
from .serializers import (
    TicketOrderSerializer, TicketOrderListSerializer,
    TicketApprovalSerializer, TicketTaskSerializer
)

logger = logging.getLogger(__name__)


def write_audit_log(user, module, action, resource_id='', detail=None, ip=''):
    """写入操作审计日志"""
    from accounts.models import OperationLog
    OperationLog.objects.create(
        user=user,
        username=user.display_name or user.username,
        module=module,
        action=action,
        resource_id=str(resource_id),
        detail=detail or {},
        ip=ip,
    )


def write_resource_change(resource, action, operator, ticket_no, before=None, after=None):
    """写入资源变更记录"""
    from cmdb.models import ResourceChange
    ResourceChange.objects.create(
        resource=resource,
        action=action,
        before_data=before or {},
        after_data=after or {},
        operator=operator,
        source='ticket',
        ticket_id=ticket_no,
    )


class TicketOrderViewSet(viewsets.ModelViewSet):
    """工单管理"""
    queryset = TicketOrder.objects.all()
    serializer_class = TicketOrderSerializer
    filterset_fields = ['status', 'ticket_type', 'applicant', 'provider_type']
    search_fields = ['ticket_no', 'title', 'applicant']
    ordering_fields = ['created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketOrderListSerializer
        return TicketOrderSerializer

    def perform_create(self, serializer):
        """创建工单时自动生成工单号"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"{'SO' if serializer.validated_data.get('ticket_type') == 'scenario' else 'WO'}{today}"
        last = TicketOrder.objects.filter(
            ticket_no__startswith=prefix
        ).order_by('-ticket_no').first()
        if last:
            seq = int(last.ticket_no[-4:]) + 1
        else:
            seq = 1
        ticket_no = f'{prefix}{seq:04d}'
        user = self.request.user
        request_content = dict(serializer.validated_data.get('request_content') or {})
        impact = _compute_impact(
            serializer.validated_data.get('resource_id'),
            request_content.get('application_id'),
        )
        if impact:
            request_content['impact_analysis'] = impact

        serializer.save(
            ticket_no=ticket_no,
            applicant=user.display_name or user.username,
            applicant_id=user.id,
            request_content=request_content,
        )
        # 审计日志
        write_audit_log(user, 'ticket', 'create', ticket_no,
                        {'type': serializer.instance.ticket_type, 'title': serializer.instance.title})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批工单 - 完整状态机"""
        ticket = self.get_object()
        VALID_APPROVE_STATUSES = ('pending', 'approving')
        if ticket.status not in VALID_APPROVE_STATUSES:
            return Response(
                {'error': f'当前状态「{ticket.get_status_display()}」不允许审批'},
                status=status.HTTP_400_BAD_REQUEST
            )

        action_val = request.data.get('action')  # 1-同意 2-驳回
        comment = request.data.get('comment', '')
        user = request.user

        if action_val not in (1, 2):
            return Response({'error': '审批动作无效'}, status=status.HTTP_400_BAD_REQUEST)

        # 写入审批记录
        TicketApproval.objects.create(
            ticket=ticket,
            approver=user.display_name or user.username,
            approver_id=user.id,
            action=action_val,
            comment=comment,
        )

        if action_val == 1:
            # 审批通过 → 进入待执行 → 立即创建任务
            ticket.status = 'executing'
            ticket.approver = user.display_name or user.username
            ticket.save()
            if ticket.ticket_type == 'scenario':
                from scenario.executor import execute_scenario
                execute_scenario(ticket)
            elif ticket.ticket_type == 'relation_change':
                from cmdb.relation_change import apply_relation_changes
                apply_relation_changes(ticket)
            else:
                self._create_and_execute_task(ticket)
        else:
            # 审批驳回 → 终态
            ticket.status = 'rejected'
            ticket.fail_reason = comment or '审批驳回'
            ticket.finished_at = timezone.now()
            ticket.save()

        # 审计日志
        write_audit_log(user, 'ticket', 'approve',
                        ticket.ticket_no,
                        {'action': 'agree' if action_val == 1 else 'reject', 'comment': comment})

        return Response({'message': '审批完成', 'status': ticket.status})

    def _create_and_execute_task(self, ticket):
        """创建任务并执行（含重试机制）"""
        request_content = ticket.request_content or {}
        task = TicketTask.objects.create(
            ticket=ticket,
            task_type=ticket.ticket_type,
            provider_type=ticket.provider_type or 'mock',
            request_id=str(uuid.uuid4()),
        )
        if ticket.ticket_type == 'scenario':
            from scenario.executor import execute_scenario
            execute_scenario(ticket)
        elif ticket.ticket_type == 'relation_change':
            from cmdb.relation_change import apply_relation_changes
            apply_relation_changes(ticket)
        else:
            self._execute_task_with_retry(task, ticket, request_content)

    def _execute_task_with_retry(self, task, ticket, request_content):
        """执行任务（带重试机制，最多重试 max_retry 次）"""
        from provider.core import get_provider
        from cmdb.models import Resource

        while task.retry_count <= task.max_retry:
            # 更新任务状态为运行中
            task.status = 'running'
            task.started_at = task.started_at or timezone.now()
            task.save()
            ticket.status = 'running'
            ticket.save()

            try:
                provider = get_provider(task.provider_type)
                handle = self._dispatch_operation(provider, ticket, request_content)

                # 执行成功 → 回写 CMDB
                task.status = 'success'
                task.finished_at = timezone.now()
                task.exec_log += f'\n[尝试{task.retry_count + 1}] 执行成功: task_id={handle.task_id}'
                task.save()

                ticket.status = 'success'
                ticket.finished_at = timezone.now()
                ticket.result_content = {
                    'task_id': handle.task_id,
                    'provider_type': task.provider_type,
                    'retry_count': task.retry_count,
                }
                ticket.save()

                # 回写 CMDB + 变更记录
                self._writeback_cmdb(ticket, request_content, handle)
                return  # 成功，退出重试循环

            except Exception as e:
                task.retry_count += 1
                task.exec_log += f'\n[尝试{task.retry_count}] 执行失败: {str(e)}'
                logger.warning(f'工单 {ticket.ticket_no} 任务执行失败(第{task.retry_count}次): {e}')

                if task.retry_count > task.max_retry:
                    # 重试次数耗尽 → 终态失败
                    task.status = 'failed'
                    task.finished_at = timezone.now()
                    task.save()

                    ticket.status = 'failed'
                    ticket.fail_reason = f'重试{task.max_retry}次后仍失败: {str(e)}'
                    ticket.finished_at = timezone.now()
                    ticket.save()
                    return
                else:
                    # 还有重试次数，继续循环
                    task.status = 'pending'
                    task.save()

    def _dispatch_operation(self, provider, ticket, request_content):
        """根据工单类型分发云操作"""
        if ticket.ticket_type == 'create_instance':
            return provider.create_instance(request_content)
        elif ticket.ticket_type == 'start':
            return provider.start_instance(ticket.resource_id)
        elif ticket.ticket_type == 'stop':
            return provider.stop_instance(ticket.resource_id)
        elif ticket.ticket_type == 'resize':
            new_spec = request_content.get('spec', '')
            return provider.resize_instance(ticket.resource_id, new_spec)
        elif ticket.ticket_type == 'release':
            return provider.release_instance(ticket.resource_id)
        else:
            raise ValueError(f'未知工单类型: {ticket.ticket_type}')

    def _writeback_cmdb(self, ticket, request_content, handle):
        """执行成功后回写 CMDB"""
        from cmdb.models import Resource

        if ticket.ticket_type == 'create_instance':
            resource = Resource.objects.create(
                account_id=request_content.get('account_id', 1),
                provider_type=ticket.provider_type or 'mock',
                resource_type='instance',
                resource_name=request_content.get('name', 'unnamed'),
                cloud_resource_id=handle.result.get('instance_id', f'i-{uuid.uuid4().hex[:12]}'),
                region=request_content.get('region', 'cn-hangzhou'),
                zone=request_content.get('zone', ''),
                status='running',
                spec=request_content.get('spec', ''),
                metadata=request_content,
                source=1,
            )
            write_resource_change(resource, 'create', ticket.applicant,
                                 ticket.ticket_no, after=request_content)

        elif ticket.ticket_type in ('start', 'stop', 'resize', 'release'):
            try:
                resource = Resource.objects.get(cloud_resource_id=ticket.resource_id)
                before = {'status': resource.status, 'spec': resource.spec}
                status_map = {'start': 'running', 'stop': 'stopped', 'release': 'released'}
                if ticket.ticket_type in status_map:
                    resource.status = status_map[ticket.ticket_type]
                elif ticket.ticket_type == 'resize':
                    resource.spec = request_content.get('spec', resource.spec)
                resource.save()
                write_resource_change(resource, ticket.ticket_type, ticket.applicant,
                                     ticket.ticket_no, before=before,
                                     after={'status': resource.status, 'spec': resource.spec})
            except Resource.DoesNotExist:
                logger.warning(f'CMDB中未找到资源 {ticket.resource_id}')

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的工单"""
        ticket = self.get_object()
        if ticket.status != 'failed':
            return Response({'error': '只有失败状态的工单可以重试'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 创建新的重试任务
        request_content = ticket.request_content or {}
        task = TicketTask.objects.create(
            ticket=ticket,
            task_type=ticket.ticket_type,
            provider_type=ticket.provider_type or 'mock',
            request_id=str(uuid.uuid4()),  # 新的幂等 ID
        )
        ticket.status = 'executing'
        ticket.fail_reason = ''
        ticket.finished_at = None
        ticket.save()

        self._execute_task_with_retry(task, ticket, request_content)

        write_audit_log(request.user, 'ticket', 'retry', ticket.ticket_no)
        return Response({'message': '重试已触发', 'status': ticket.status})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消工单"""
        ticket = self.get_object()
        if ticket.status in ('success', 'failed', 'rejected', 'cancelled'):
            return Response({'error': f'当前状态「{ticket.get_status_display()}」不允许取消'},
                            status=status.HTTP_400_BAD_REQUEST)
        ticket.status = 'cancelled'
        ticket.finished_at = timezone.now()
        ticket.save()
        write_audit_log(request.user, 'ticket', 'cancel', ticket.ticket_no)
        return Response({'message': '工单已取消'})

    @action(detail=True, methods=['get'])
    def approvals(self, request, pk=None):
        """获取审批记录"""
        ticket = self.get_object()
        approvals = TicketApproval.objects.filter(ticket=ticket)
        serializer = TicketApprovalSerializer(approvals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """获取执行任务"""
        ticket = self.get_object()
        tasks = TicketTask.objects.filter(ticket=ticket)
        serializer = TicketTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TicketApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    """审批记录"""
    queryset = TicketApproval.objects.select_related('ticket').all()
    serializer_class = TicketApprovalSerializer
    filterset_fields = ['approver', 'action']


class TicketTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """执行任务"""
    queryset = TicketTask.objects.select_related('ticket').all()
    serializer_class = TicketTaskSerializer
    filterset_fields = ['status', 'provider_type', 'task_type']


def _compute_impact(resource_id, application_id=None, environment_id=None):
    """提单时计算影响面，写入工单 request_content['impact_analysis']"""
    from cmdb.graph import impact_analysis
    from cmdb.models import Resource

    resource = None
    if resource_id:
        resource = Resource.objects.filter(cloud_resource_id=str(resource_id),
                                           is_deleted=False).first()
        if not resource and str(resource_id).isdigit():
            resource = Resource.objects.filter(id=int(resource_id), is_deleted=False).first()
    if not resource and application_id:
        from cmdb.models import ServiceInstance
        svc_qs = ServiceInstance.objects.filter(application_id=application_id,
                                                resource__isnull=False)
        if environment_id:
            svc_qs = svc_qs.filter(environment_id=environment_id)
        svc = svc_qs.first()
        resource = svc.resource if svc else None
    if not resource:
        return None

    result = impact_analysis(resource.id)
    return {
        'root': result['root'],
        'summary': result['summary'],
        'nodes': result['nodes'][:20],
    }
