"""
Mock 数据 API 视图
提供对 Mock 数据的 RESTful 访问
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse

from .service import MockService


def get_mock_service():
    """获取 MockService 实例"""
    return MockService()


# ==================== 部门 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def department_list(request):
    """获取部门列表"""
    try:
        with get_mock_service() as service:
            departments = service.get_departments()
            return Response({'results': departments})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def department_tree(request):
    """获取部门树结构"""
    try:
        with get_mock_service() as service:
            tree = service.get_department_tree()
            return Response({'results': tree})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 应用 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def application_list(request):
    """获取应用列表"""
    try:
        with get_mock_service() as service:
            department_id = request.query_params.get('department_id')
            if department_id:
                department_id = int(department_id)
            applications = service.get_applications(department_id)
            return Response({'results': applications})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def application_detail(request, app_id):
    """获取应用详情"""
    try:
        with get_mock_service() as service:
            app = service.get_application_detail(app_id)
            if app:
                return Response(app)
            return Response({'error': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 环境 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def environment_list(request):
    """获取环境列表"""
    try:
        with get_mock_service() as service:
            application_id = request.query_params.get('application_id')
            if application_id:
                application_id = int(application_id)
            environments = service.get_environments(application_id)
            return Response({'results': environments})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def environment_detail(request, env_id):
    """获取环境详情"""
    try:
        with get_mock_service() as service:
            env = service.get_environment_detail(env_id)
            if env:
                return Response(env)
            return Response({'error': '环境不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 服务 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def service_list(request):
    """获取服务列表"""
    try:
        with get_mock_service() as service:
            environment_id = request.query_params.get('environment_id')
            if environment_id:
                environment_id = int(environment_id)
            services = service.get_services(environment_id)
            return Response({'results': services})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_detail(request, service_id):
    """获取服务详情"""
    try:
        with get_mock_service() as service:
            svc = service.get_service_detail(service_id)
            if svc:
                return Response(svc)
            return Response({'error': '服务不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_dependencies(request, service_id):
    """获取服务依赖关系"""
    try:
        with get_mock_service() as service:
            dependencies = service.get_service_dependencies(service_id)
            return Response({'results': dependencies})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 关系 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def relation_list(request):
    """获取所有关系"""
    try:
        with get_mock_service() as service:
            environment_id = request.query_params.get('environment_id')
            if environment_id:
                environment_id = int(environment_id)
            relations = service.get_relations(environment_id)
            return Response({'results': relations})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def relation_detail(request, relation_id):
    """获取关系详情"""
    try:
        with get_mock_service() as service:
            relation = service.get_relation_detail(relation_id)
            if relation:
                return Response(relation)
            return Response({'error': '关系不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def relation_create(request):
    """创建关系"""
    try:
        with get_mock_service() as service:
            data = request.data
            required_fields = ['source_service_id', 'target_service_id']
            for field in required_fields:
                if field not in data:
                    return Response({'error': f'缺少必填字段: {field}'}, status=status.HTTP_400_BAD_REQUEST)
            
            relation_id = service.create_relation(data)
            return Response({'id': relation_id, 'message': '创建成功'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])
def relation_update(request, relation_id):
    """更新关系"""
    try:
        with get_mock_service() as service:
            data = request.data
            success = service.update_relation(relation_id, data)
            if success:
                return Response({'message': '更新成功'})
            return Response({'error': '更新失败'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def relation_delete(request, relation_id):
    """删除关系"""
    try:
        with get_mock_service() as service:
            success = service.delete_relation(relation_id)
            if success:
                return Response({'message': '删除成功'})
            return Response({'error': '删除失败'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 图谱 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def graph_environment(request, env_id):
    """获取环境图谱"""
    try:
        with get_mock_service() as service:
            graph = service.get_environment_graph(env_id)
            return Response(graph)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def graph_application(request, app_id):
    """获取应用图谱"""
    try:
        with get_mock_service() as service:
            environment_id = request.query_params.get('environment_id')
            if environment_id:
                environment_id = int(environment_id)
            graph = service.get_application_graph(app_id, environment_id)
            return Response(graph)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 资源 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def resource_list(request):
    """获取资源列表"""
    try:
        with get_mock_service() as service:
            environment_id = request.query_params.get('environment_id')
            resource_type = request.query_params.get('resource_type')
            if environment_id:
                environment_id = int(environment_id)
            resources = service.get_resources(environment_id, resource_type)
            return Response({'results': resources})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 部署单元 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def deployment_unit_list(request):
    """获取部署单元"""
    try:
        with get_mock_service() as service:
            environment_id = request.query_params.get('environment_id')
            if environment_id:
                environment_id = int(environment_id)
            units = service.get_deployment_units(environment_id)
            return Response({'results': units})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 变更记录 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def change_record_list(request):
    """获取变更记录"""
    try:
        with get_mock_service() as service:
            ticket_no = request.query_params.get('ticket_no')
            records = service.get_change_records(ticket_no)
            return Response({'results': records})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def change_record_create(request):
    """创建变更记录"""
    try:
        with get_mock_service() as service:
            data = request.data
            record_id = service.create_change_record(data)
            return Response({'id': record_id, 'message': '创建成功'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 统计 API ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def statistics(request):
    """获取统计信息"""
    try:
        with get_mock_service() as service:
            stats = service.get_statistics()
            return Response(stats)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 初始化 API ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def initialize_data(request):
    """初始化 Mock 数据"""
    try:
        from .seed import MockDataSeeder
        seeder = MockDataSeeder()
        seeder.run()
        return Response({'message': 'Mock 数据初始化成功'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)