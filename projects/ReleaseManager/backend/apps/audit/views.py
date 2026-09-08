from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import AuditLog
from .serializers import AuditLogSerializer


@api_view(['GET'])
def audit_log_list(request):
    """审计日志列表"""
    qs = AuditLog.objects.select_related('user').order_by('-created_at')

    resource_type = request.query_params.get('resource_type')
    action = request.query_params.get('action')

    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    if action:
        qs = qs.filter(action=action)

    return Response({'code': 200, 'data': AuditLogSerializer(qs, many=True).data})


@api_view(['GET'])
def audit_log_detail(request, log_id):
    """审计日志详情"""
    instance = get_object_or_404(AuditLog.objects.select_related('user'), id=log_id)
    return Response({'code': 200, 'data': AuditLogSerializer(instance).data})