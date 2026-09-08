from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import DeployHistory, PodInstance, RollbackRecord
from .serializers import DeployHistorySerializer, PodInstanceSerializer, RollbackRecordSerializer
from apps.audit.models import AuditLog


@api_view(['GET'])
def deploy_history_list(request):
    """部署历史列表"""
    qs = DeployHistory.objects.select_related(
        'release', 'application', 'environment', 'created_by'
    ).order_by('-created_at')

    app_id = request.query_params.get('app_id')
    if app_id:
        qs = qs.filter(application_id=app_id)

    return Response({'code': 200, 'data': DeployHistorySerializer(qs, many=True).data})


@api_view(['GET'])
def deploy_history_detail(request, history_id):
    """部署历史详情"""
    instance = get_object_or_404(
        DeployHistory.objects.select_related(
            'release', 'application', 'environment', 'created_by'
        ),
        id=history_id,
    )
    return Response({'code': 200, 'data': DeployHistorySerializer(instance).data})


@api_view(['GET'])
def deploy_pods(request, history_id):
    """部署 Pod 列表"""
    deploy = get_object_or_404(DeployHistory, id=history_id)
    pods = PodInstance.objects.filter(deploy_history=deploy)
    return Response({'code': 200, 'data': PodInstanceSerializer(pods, many=True).data})


@api_view(['POST'])
def deploy_rollback(request, history_id):
    """回滚到指定部署记录"""
    old_deploy = get_object_or_404(
        DeployHistory.objects.select_related('release', 'application', 'environment', 'created_by'),
        id=history_id,
    )

    # 创建回滚记录
    RollbackRecord.objects.create(
        release=old_deploy.release,
        deploy_history=old_deploy,
        from_version=old_deploy.version,
        to_version=old_deploy.release.version,
        reason=request.data.get('reason', ''),
        operator=request.user,
    )

    # 创建新的回滚部署记录
    new_deploy = DeployHistory.objects.create(
        release=old_deploy.release,
        application=old_deploy.application,
        environment=old_deploy.environment,
        version=old_deploy.release.version,
        image_tag=old_deploy.image_tag,
        action='rollback',
        strategy=old_deploy.strategy,
        canary_percent=old_deploy.canary_percent,
        created_by=request.user,
    )

    AuditLog.objects.create(
        user=request.user,
        action='rollback',
        resource_type='deploy',
        resource_id=new_deploy.id,
        detail={
            'from_deploy_id': old_deploy.id,
            'from_version': old_deploy.version,
            'to_version': old_deploy.release.version,
            'reason': request.data.get('reason', ''),
        },
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({
        'code': 200,
        'message': '回滚成功',
        'data': DeployHistorySerializer(new_deploy).data,
    })