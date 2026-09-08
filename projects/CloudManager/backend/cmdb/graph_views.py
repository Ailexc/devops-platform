"""图谱 API：应用全景 / 邻居展开 / 影响面 / 路径 / 连通性"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import graph
from .models import Application, Resource


@api_view(['GET'])
def applications(request):
    """应用列表（含服务/资源/关系统计）"""
    return Response(graph.list_applications())


@api_view(['GET'])
def organization(request):
    """组织架构树：部门 -> 应用 -> 环境"""
    return Response(graph.organization_tree())


@api_view(['GET'])
def application_detail(request, app_id):
    """应用全景图"""
    try:
        Application.objects.get(id=app_id)
    except Application.DoesNotExist:
        return Response({'error': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)
    env_id = request.query_params.get('environment')
    if env_id:
        env_id = int(env_id)
    return Response(graph.application_graph(app_id, environment_id=env_id))


@api_view(['GET'])
def environment_detail(request, env_id):
    """环境详情图"""
    from .models import Environment
    if not Environment.objects.filter(id=env_id).exists():
        return Response({'error': '环境不存在'}, status=status.HTTP_404_NOT_FOUND)
    return Response(graph.environment_graph(env_id))


@api_view(['GET'])
def resource_neighbors(request, resource_id):
    """资源邻居展开"""
    if not Resource.objects.filter(id=resource_id).exists():
        return Response({'error': '资源不存在'}, status=status.HTTP_404_NOT_FOUND)
    depth = int(request.query_params.get('depth', 1))
    return Response(graph.resource_neighbors(resource_id, depth=depth))


@api_view(['GET'])
def resource_impact(request, resource_id):
    """影响面分析"""
    if not Resource.objects.filter(id=resource_id).exists():
        return Response({'error': '资源不存在'}, status=status.HTTP_404_NOT_FOUND)
    return Response(graph.impact_analysis(resource_id))


@api_view(['GET'])
def resource_path(request, source_id):
    """两资源间路径"""
    target_id = request.query_params.get('target')
    if not target_id or not Resource.objects.filter(id=source_id, is_deleted=False).exists() \
            or not Resource.objects.filter(id=target_id, is_deleted=False).exists():
        return Response({'error': '参数不合法'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(graph.path_between(source_id, int(target_id)))


@api_view(['GET'])
def resource_connectivity(request, source_id):
    """网络连通性推导"""
    target_id = request.query_params.get('target')
    if not target_id:
        return Response({'error': '缺少 target 参数'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(graph.connectivity(source_id, int(target_id)))


@api_view(['POST'])
def relation_changes(request):
    """图谱编辑 -> 生成关系变更工单（审批后落库）"""
    from rest_framework import status
    from ticket.models import TicketOrder
    from ticket.views import _compute_impact, write_audit_log
    from scenario.views import _next_ticket_no

    changes = request.data.get('changes')
    if not isinstance(changes, list) or not changes:
        return Response({'error': 'changes 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    request_content = {
        'changes': changes,
        'application_id': request.data.get('application_id'),
        'environment_id': request.data.get('environment_id'),
    }
    impact = _compute_impact(
        changes[0].get('source_id'),
        request.data.get('application_id'),
        request.data.get('environment_id'),
    )
    if impact:
        request_content['impact_analysis'] = impact

    ticket = TicketOrder.objects.create(
        ticket_no=_next_ticket_no('RC'),
        ticket_type='relation_change',
        title=request.data.get('title', '依赖关系变更'),
        status='pending',
        applicant=user.display_name or user.username,
        applicant_id=user.id,
        provider_type='mock',
        request_content=request_content,
    )
    write_audit_log(user, 'ticket', 'relation_change_apply', ticket.ticket_no,
                    {'changes': len(changes), 'title': ticket.title})
    return Response({'message': '关系变更工单已提交', 'ticket_id': ticket.id,
                     'ticket_no': ticket.ticket_no})


@api_view(['GET'])
def pending_changes(request):
    """待生效的关系变更（审批中/待执行），供前端渲染"虚边"状态"""
    from ticket.models import TicketOrder

    env_id = request.query_params.get('environment_id')
    qs = TicketOrder.objects.filter(
        ticket_type='relation_change',
        status__in=['pending', 'approving', 'executing', 'running'],
    ).order_by('-created_at')
    if env_id:
        qs = qs.filter(request_content__environment_id=int(env_id))
    result = []
    for t in qs[:50]:
        content = t.request_content or {}
        result.append({
            'ticket_id': t.id,
            'ticket_no': t.ticket_no,
            'status': t.status,
            'environment_id': content.get('environment_id'),
            'changes': content.get('changes') or [],
        })
    return Response(result)
