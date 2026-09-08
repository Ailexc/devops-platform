from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Scenario
from .serializers import ScenarioSerializer


class ScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    """场景定义"""
    queryset = Scenario.objects.prefetch_related('steps').all()
    serializer_class = ScenarioSerializer
    filterset_fields = ['enabled', 'need_approval']

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """发起场景：参数校验 -> 生成场景工单（复用 ticket 体系）"""
        scenario = self.get_object()
        if not scenario.enabled:
            return Response({'error': '场景已停用'}, status=status.HTTP_400_BAD_REQUEST)

        from ticket.models import TicketOrder

        params = request.data.get('request_content') or {}
        title = request.data.get('title') or f'{scenario.name}'
        user = request.user

        request_content = dict(params)
        request_content['scenario_code'] = scenario.code
        request_content['scenario_name'] = scenario.name
        # 提单附带影响面分析（审批人可见变更影响范围）
        from ticket.views import _compute_impact
        impact = _compute_impact(
            params.get('resource_id'),
            params.get('application_id'),
            params.get('environment_id'),
        )
        if impact:
            request_content['impact_analysis'] = impact

        ticket = TicketOrder.objects.create(
            ticket_no=_next_ticket_no('SO'),
            ticket_type='scenario',
            title=title,
            status='pending',
            applicant=user.display_name or user.username,
            applicant_id=user.id,
            provider_type='mock',
            scenario_id=scenario.id,
            scenario_code=scenario.code,
            request_content=request_content,
        )
        from ticket.views import write_audit_log
        write_audit_log(user, 'ticket', 'scenario_apply', ticket.ticket_no,
                        {'scenario': scenario.code, 'title': title})
        return Response({'message': '场景工单已提交', 'ticket_id': ticket.id,
                         'ticket_no': ticket.ticket_no})


def _next_ticket_no(prefix='SO'):
    """生成场景工单号：SO202608060001"""
    from ticket.models import TicketOrder

    today = timezone.now().strftime('%Y%m%d')
    full_prefix = f'{prefix}{today}'
    last = TicketOrder.objects.filter(
        ticket_no__startswith=full_prefix
    ).order_by('-ticket_no').first()
    seq = int(last.ticket_no[-4:]) + 1 if last else 1
    return f'{full_prefix}{seq:04d}'
