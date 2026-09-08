from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import difflib

from .models import ConfigTemplate, ConfigVariable, ConfigVariableValue, ConfigRelease
from .serializers import (
    ConfigTemplateSerializer,
    ConfigVariableSerializer,
    ConfigVariableValueSerializer,
    ConfigReleaseSerializer,
)


def render_template(template, environment, system_vars=None):
    """使用 Jinja2-like 简单变量替换渲染模板内容

    system_vars：可选的系统级变量（发布上下文，如版本号/发布单号），
    优先于模板静态变量替换，占位符被替换后模板变量不会再覆盖。
    """
    content = template.template_content
    if system_vars:
        for key, value in system_vars.items():
            content = content.replace('{{ ' + key + ' }}', str(value))
            content = content.replace('{{' + key + '}}', str(value))
    variables = ConfigVariable.objects.filter(template=template)
    for var in variables:
        # 查找环境特定值
        val = ConfigVariableValue.objects.filter(variable=var, environment=environment).first()
        value = val.value if val else var.default_value
        if value is None:
            value = ""
        content = content.replace('{{ ' + var.key + ' }}', value)
        content = content.replace('{{' + var.key + '}}', value)
    return content


# ==================== Config Templates ====================


@api_view(['GET', 'POST'])
def template_list(request):
    if request.method == 'GET':
        queryset = ConfigTemplate.objects.select_related('application', 'created_by').all()
        app_id = request.query_params.get('app_id')
        if app_id:
            queryset = queryset.filter(application_id=app_id)
        serializer = ConfigTemplateSerializer(queryset, many=True)
        return Response({'code': 200, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ConfigTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def template_detail(request, template_id):
    template = get_object_or_404(ConfigTemplate, id=template_id)

    if request.method == 'GET':
        serializer = ConfigTemplateSerializer(template)
        return Response({'code': 200, 'data': serializer.data})

    if request.method == 'PUT':
        serializer = ConfigTemplateSerializer(template, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data})
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def template_render(request, template_id):
    template = get_object_or_404(ConfigTemplate, id=template_id)
    environment_id = request.data.get('environment_id')
    if not environment_id:
        return Response(
            {'code': 400, 'message': 'environment_id is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from apps.infrastructures.models import Environment
    environment = get_object_or_404(Environment, id=environment_id)

    rendered_content = render_template(template, environment)
    return Response({'code': 200, 'data': {'rendered_content': rendered_content}})


# ==================== Config Variables ====================


@api_view(['GET', 'POST'])
def variable_list(request):
    if request.method == 'GET':
        queryset = ConfigVariable.objects.select_related('template').all()
        template_id = request.query_params.get('template_id')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        serializer = ConfigVariableSerializer(queryset, many=True)
        return Response({'code': 200, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ConfigVariableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def variable_detail(request, var_id):
    variable = get_object_or_404(ConfigVariable, id=var_id)
    serializer = ConfigVariableSerializer(variable, data=request.data, partial=False)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ==================== Config Variable Values ====================


@api_view(['GET'])
def variable_value_list(request):
    queryset = ConfigVariableValue.objects.select_related('variable', 'environment').all()
    variable_id = request.query_params.get('variable_id')
    environment_id = request.query_params.get('environment_id')
    if variable_id:
        queryset = queryset.filter(variable_id=variable_id)
    if environment_id:
        queryset = queryset.filter(environment_id=environment_id)
    serializer = ConfigVariableValueSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['PUT'])
def variable_value_detail(request, value_id):
    value = get_object_or_404(ConfigVariableValue, id=value_id)
    serializer = ConfigVariableValueSerializer(value, data=request.data, partial=False)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def variable_value_batch(request):
    """批量创建或更新变量值"""
    items = request.data
    if not isinstance(items, list):
        return Response(
            {'code': 400, 'message': 'Expected a list of items'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = []
    errors = []
    for idx, item in enumerate(items):
        variable_id = item.get('variable_id')
        environment_id = item.get('environment_id')
        value = item.get('value', '')

        if not variable_id or not environment_id:
            errors.append({'index': idx, 'error': 'variable_id and environment_id are required'})
            continue

        # 尝试查找现有记录，存在则更新，不存在则创建
        existing = ConfigVariableValue.objects.filter(
            variable_id=variable_id,
            environment_id=environment_id,
        ).first()

        if existing:
            serializer = ConfigVariableValueSerializer(
                existing, data=item, partial=False
            )
        else:
            serializer = ConfigVariableValueSerializer(data=item)

        if serializer.is_valid():
            serializer.save()
            results.append(serializer.data)
        else:
            errors.append({'index': idx, 'errors': serializer.errors})

    response_data = {'results': results}
    if errors:
        response_data['errors'] = errors
        return Response({'code': 207, 'data': response_data}, status=status.HTTP_207_MULTI_STATUS)
    return Response({'code': 200, 'data': response_data}, status=status.HTTP_200_OK)


# ==================== Config Releases ====================


@api_view(['GET', 'POST'])
def release_list(request):
    if request.method == 'GET':
        queryset = ConfigRelease.objects.select_related(
            'template', 'environment', 'created_by'
        ).all()
        serializer = ConfigReleaseSerializer(queryset, many=True)
        return Response({'code': 200, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ConfigReleaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response({'code': 200, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def release_configs_by_release(request, release_id):
    """按发布单查询本次发布的配置版本列表（配置随发布走 · 可追溯）"""
    from apps.releases.models import Release
    get_object_or_404(Release, id=release_id)
    queryset = ConfigRelease.objects.filter(release_id=release_id).select_related(
        'template', 'environment', 'created_by'
    )
    serializer = ConfigReleaseSerializer(queryset, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['GET'])
def release_diff(request, release_id):
    """对比当前发布与上一次发布（同一模板+环境）的渲染内容差异"""
    release = get_object_or_404(
        ConfigRelease.objects.select_related('template', 'environment'),
        id=release_id,
    )

    # 查找同模板同环境的上一次发布
    previous_release = ConfigRelease.objects.filter(
        template=release.template,
        environment=release.environment,
        created_at__lt=release.created_at,
    ).order_by('-created_at').first()

    current_lines = release.rendered_content.splitlines(keepends=True)

    if previous_release:
        previous_lines = previous_release.rendered_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            previous_lines,
            current_lines,
            fromfile=f'v{previous_release.version}',
            tofile=f'v{release.version}',
            lineterm='',
        ))
    else:
        # 没有上一次发布，所有行均为新增
        diff = list(difflib.unified_diff(
            [],
            current_lines,
            fromfile='',
            tofile=f'v{release.version}',
            lineterm='',
        ))

    return Response({'code': 200, 'data': {
        'release_id': release.id,
        'template_id': release.template_id,
        'template_name': release.template.name,
        'environment_id': release.environment_id,
        'environment_name': release.environment.name,
        'current_version': release.version,
        'previous_version': previous_release.version if previous_release else None,
        'diff': diff,
    }})