from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Application, AppEnvConfig, ImageRegistry
from .serializers import ApplicationSerializer, AppEnvConfigSerializer, ImageRegistrySerializer
from apps.organizations.models import BusinessLine
from apps.authz.models import SubjectMembership
from apps.authz.utils import get_user_accessible_app_ids, get_user_accessible_env_ids_for_app


@api_view(['GET', 'POST'])
def app_list(request):
    if request.method == 'GET':
        # 根据当前用户权限过滤应用列表
        allowed_app_ids = get_user_accessible_app_ids(request.user)
        queryset = Application.objects.filter(
            id__in=allowed_app_ids
        ).select_related('business_line', 'owner', 'owner_group')

        # 获取用户归属组 ID（primary 成员）
        user_primary_group_ids = set(
            SubjectMembership.objects.filter(
                user=request.user, membership_type='primary'
            ).values_list('group_id', flat=True)
        )

        serializer = ApplicationSerializer(queryset, many=True)
        data = serializer.data
        # 为每个应用标注权限来源：组内应用 / 协作应用
        for item in data:
            owner_group_id = item.get('owner_group')
            if owner_group_id and owner_group_id in user_primary_group_ids:
                item['permission_source'] = 'own_group'
            else:
                item['permission_source'] = 'cross_group'
        return Response({'code': 200, 'data': data})

    # POST
    serializer = ApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def app_detail(request, app_id):
    instance = get_object_or_404(
        Application.objects.select_related('business_line', 'owner'),
        pk=app_id,
    )

    if request.method == 'GET':
        serializer = ApplicationSerializer(instance)
        return Response({'code': 200, 'data': serializer.data})

    if request.method == 'PUT':
        serializer = ApplicationSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})

    # DELETE
    instance.delete()
    return Response({'code': 200, 'message': '已删除'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def app_env_config_list(request, app_id):
    app = get_object_or_404(Application, pk=app_id)

    if request.method == 'GET':
        # 获取用户在该应用下可访问的环境 ID
        allowed_env_ids = get_user_accessible_env_ids_for_app(request.user, app_id)
        queryset = AppEnvConfig.objects.filter(
            application=app,
            environment_id__in=allowed_env_ids,
        ).select_related('environment', 'cluster', 'namespace')
        serializer = AppEnvConfigSerializer(queryset, many=True)
        return Response({'code': 200, 'data': serializer.data})

    # POST
    serializer = AppEnvConfigSerializer(data={**request.data, 'application': app.pk})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
def app_env_config_detail(request, app_id, config_id):
    instance = get_object_or_404(AppEnvConfig, pk=config_id, application_id=app_id)
    serializer = AppEnvConfigSerializer(instance, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'code': 200, 'data': serializer.data})


# ─── 模拟 Git 分支 / Commit ─────────────────────────────────


class AppBranchesView(APIView):
    """返回应用的模拟分支列表"""

    def get(self, request, app_id):
        app = get_object_or_404(Application, pk=app_id)
        branches = [
            {'name': 'main', 'is_default': True, 'protected': True},
            {'name': 'develop', 'is_default': False, 'protected': False},
            {'name': f'release/v1.0.0', 'is_default': False, 'protected': False},
            {'name': f'feature/{app.code}-new-dashboard', 'is_default': False, 'protected': False},
            {'name': f'feature/{app.code}-bugfix-xxx', 'is_default': False, 'protected': False},
            {'name': f'hotfix/{app.code}-critical-fix', 'is_default': False, 'protected': True},
        ]
        return Response({'code': 200, 'data': branches})


class AppCommitsView(APIView):
    """返回应用的模拟 Commit 列表"""

    def get(self, request, app_id):
        app = get_object_or_404(Application, pk=app_id)
        branch = request.query_params.get('branch', 'main')

        import hashlib

        mock_commits = [
            {'message': f'feat({app.code}): 新增用户权限管理模块', 'author': '张三', 'date': '2026-07-27 10:30:00'},
            {'message': f'fix({app.code}): 修复部署流水线超时问题', 'author': '李四', 'date': '2026-07-26 15:20:00'},
            {'message': f'refactor({app.code}): 重构发布策略引擎', 'author': '王五', 'date': '2026-07-25 09:00:00'},
            {'message': f'feat({app.code}): 集成灰度发布能力', 'author': '张三', 'date': '2026-07-24 18:45:00'},
            {'message': f'chore({app.code}): 升级依赖版本', 'author': '赵六', 'date': '2026-07-23 14:10:00'},
            {'message': f'docs({app.code}): 更新 API 文档', 'author': '李四', 'date': '2026-07-22 11:30:00'},
            {'message': f'test({app.code}): 增加单元测试覆盖率', 'author': '孙八', 'date': '2026-07-21 16:55:00'},
            {'message': f'fix({app.code}): 修复数据库连接池泄漏', 'author': '王五', 'date': '2026-07-20 08:20:00'},
            {'message': f'feat({app.code}): 支持多环境配置注入', 'author': '张三', 'date': '2026-07-19 13:40:00'},
            {'message': f'ci({app.code}): 优化 CI/CD 流水线', 'author': '赵六', 'date': '2026-07-18 10:00:00'},
        ]

        data = []
        for idx, mc in enumerate(mock_commits):
            raw = f'{app_id}:{branch}:{idx}:{mc["message"]}'
            sha = hashlib.sha256(raw.encode()).hexdigest()[:12]
            data.append({
                'sha': sha,
                'short_sha': sha[:8],
                'message': mc['message'],
                'author': mc['author'],
                'date': mc['date'],
                'branch': branch,
            })

        return Response({'code': 200, 'data': data})


@api_view(['GET'])
def resource_tree(request):
    # 根据当前用户权限过滤应用
    allowed_app_ids = get_user_accessible_app_ids(request.user)
    allowed_app_id_set = set(allowed_app_ids)

    business_lines = BusinessLine.objects.filter(status='active').order_by('sort_order', 'id')
    apps = Application.objects.filter(
        id__in=allowed_app_id_set, status='active'
    ).select_related('business_line', 'owner')

    app_map = {}
    for app in apps:
        bl_id = app.business_line_id
        if bl_id not in app_map:
            app_map[bl_id] = []
        app_map[bl_id].append({
            'id': app.id,
            'name': app.name,
            'code': app.code,
            'language': app.language,
            'owner_name': app.owner.display_name if app.owner else None,
        })

    tree = []
    for bl in business_lines:
        children = app_map.get(bl.id, [])
        tree.append({
            'id': bl.id,
            'name': bl.name,
            'code': bl.code,
            'type': 'business_line',
            'children': children,
        })

    return Response({'code': 200, 'data': tree})


# ─── 镜像注册表 CRUD ──────────────────────────────────────────


@api_view(['GET', 'POST'])
def image_registry_list(request):
    if request.method == 'GET':
        qs = ImageRegistry.objects.all().order_by('language')
        return Response({'code': 200, 'data': ImageRegistrySerializer(qs, many=True).data})

    # POST
    serializer = ImageRegistrySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
def image_registry_detail(request, image_id):
    try:
        instance = ImageRegistry.objects.get(id=image_id)
    except ImageRegistry.DoesNotExist:
        return Response({'code': 404, 'message': '镜像配置不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = ImageRegistrySerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})

    # DELETE
    instance.delete()
    return Response({'code': 200, 'message': '已删除'})