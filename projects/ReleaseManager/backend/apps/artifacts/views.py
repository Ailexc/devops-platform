from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ArtifactRepository, Artifact, ArtifactPromotion
from .serializers import (
    ArtifactRepositorySerializer, ArtifactListSerializer,
    ArtifactDetailSerializer, ArtifactPromotionSerializer,
)
from django.utils import timezone


@api_view(['GET', 'POST'])
def repository_list(request):
    if request.method == 'GET':
        queryset = ArtifactRepository.objects.all()
        serializer = ArtifactRepositorySerializer(queryset, many=True)
        return Response(serializer.data)

    serializer = ArtifactRepositorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def artifact_list(request):
    """制品列表 - 支持按应用和环境筛选"""
    queryset = Artifact.objects.select_related(
        'application', 'repository', 'created_by'
    ).all()

    app_id = request.query_params.get('app_id')
    if app_id is not None:
        queryset = queryset.filter(application_id=app_id)

    env_type = request.query_params.get('env_type')
    if env_type:
        queryset = queryset.filter(current_env=env_type)

    version = request.query_params.get('version')
    if version:
        queryset = queryset.filter(version__icontains=version)

    serializer = ArtifactListSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['GET'])
def artifact_detail(request, artifact_id):
    """制品详情 - 包含完整晋级历史"""
    try:
        artifact = Artifact.objects.select_related(
            'application', 'repository', 'created_by'
        ).get(id=artifact_id)
    except Artifact.DoesNotExist:
        return Response({'detail': '制品不存在'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ArtifactDetailSerializer(artifact)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['GET'])
def artifacts_by_app(request, app_id):
    queryset = Artifact.objects.filter(application_id=app_id).select_related(
        'application', 'repository', 'created_by'
    )
    serializer = ArtifactListSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['GET'])
def artifact_promotions(request, artifact_id):
    try:
        artifact = Artifact.objects.get(id=artifact_id)
    except Artifact.DoesNotExist:
        return Response({'detail': '制品不存在'}, status=status.HTTP_404_NOT_FOUND)

    queryset = artifact.promotions.select_related(
        'from_env', 'to_env', 'promoted_by'
    ).order_by('created_at')
    serializer = ArtifactPromotionSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['POST'])
def promote_artifact(request, artifact_id):
    try:
        artifact = Artifact.objects.get(id=artifact_id)
    except Artifact.DoesNotExist:
        return Response({'detail': '制品不存在'}, status=status.HTTP_404_NOT_FOUND)

    from_env_id = request.data.get('from_env')
    to_env_id = request.data.get('to_env')
    comment = request.data.get('comment', '')

    if not from_env_id or not to_env_id:
        return Response({'detail': '请提供来源环境和目标环境'}, status=status.HTTP_400_BAD_REQUEST)

    promotion = ArtifactPromotion.objects.create(
        artifact=artifact,
        from_env_id=from_env_id,
        to_env_id=to_env_id,
        status='promoted',
        promoted_by=request.user,
        promoted_at=timezone.now(),
        comment=comment,
    )

    artifact.current_env = promotion.to_env.code
    artifact.save(update_fields=['current_env'])

    serializer = ArtifactPromotionSerializer(promotion)
    return Response(serializer.data, status=status.HTTP_201_CREATED)