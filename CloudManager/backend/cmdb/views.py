from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    CloudAccount, Resource, ResourceRelation, ResourceChange, Application,
    ServiceInstance, ServiceEndpoint, Environment,
)
from .serializers import (
    CloudAccountSerializer, ResourceSerializer, ResourceListSerializer,
    ResourceRelationSerializer, ResourceChangeSerializer, ApplicationSerializer,
    ServiceInstanceSerializer, ServiceEndpointSerializer, EnvironmentSerializer,
)


class CloudAccountViewSet(viewsets.ModelViewSet):
    """云账号管理"""
    queryset = CloudAccount.objects.all()
    serializer_class = CloudAccountSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['account_name', 'provider_type']
    ordering_fields = ['created_at', 'account_name']

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """同步云账号资源"""
        account = self.get_object()
        from provider.core import get_provider
        try:
            provider = get_provider(account.provider_type)
            return Response({'message': '同步已触发'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResourceViewSet(viewsets.ModelViewSet):
    """资源管理"""
    queryset = Resource.objects.select_related('account').filter(is_deleted=False)
    serializer_class = ResourceSerializer
    filterset_fields = ['provider_type', 'resource_type', 'region', 'status', 'account']
    ordering_fields = ['created_at', 'resource_name', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return ResourceListSerializer
        return ResourceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        department_id = self.request.query_params.get('department_id')
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs

    @action(detail=True, methods=['get'])
    def changes(self, request, pk=None):
        """资源变更历史"""
        resource = self.get_object()
        changes = ResourceChange.objects.filter(resource=resource)
        serializer = ResourceChangeSerializer(changes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def security_rules(self, request, pk=None):
        """资源相关安全组规则（资源本身或绑定的安全组）"""
        from .models import SecurityRule
        from .serializers import SecurityRuleSerializer

        resource = self.get_object()
        if resource.resource_type == 'security_group':
            rules = SecurityRule.objects.filter(security_group=resource)
        else:
            sg_ids = ResourceRelation.objects.filter(
                source=resource, relation_type='attach_sg'
            ).values_list('target_id', flat=True)
            rules = SecurityRule.objects.filter(security_group_id__in=sg_ids)
        return Response(SecurityRuleSerializer(rules, many=True).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """资源统计"""
        from django.db.models import Count
        stats = Resource.objects.filter(is_deleted=False).values(
            'resource_type', 'status'
        ).annotate(count=Count('id'))
        return Response(list(stats))


class ResourceRelationViewSet(viewsets.ModelViewSet):
    """资源关系"""
    queryset = ResourceRelation.objects.select_related('source', 'target').all()
    serializer_class = ResourceRelationSerializer


class ResourceChangeViewSet(viewsets.ReadOnlyModelViewSet):
    """资源变更历史"""
    queryset = ResourceChange.objects.select_related('resource').all()
    serializer_class = ResourceChangeSerializer
    filterset_fields = ['resource', 'action', 'source']
    ordering_fields = ['created_at']


class ApplicationViewSet(viewsets.ModelViewSet):
    """应用管理"""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'owner']

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """应用下的服务实例"""
        app = self.get_object()
        services = ServiceInstance.objects.filter(application=app).select_related('resource')
        return Response(ServiceInstanceSerializer(services, many=True).data)

    @action(detail=True, methods=['get'])
    def endpoints(self, request, pk=None):
        """应用下的服务端点"""
        app = self.get_object()
        endpoints = ServiceEndpoint.objects.filter(service__application=app).select_related('service')
        return Response(ServiceEndpointSerializer(endpoints, many=True).data)

    @action(detail=True, methods=['get'])
    def environments(self, request, pk=None):
        """应用下的环境"""
        app = self.get_object()
        envs = Environment.objects.filter(application=app).select_related('account')
        return Response(EnvironmentSerializer(envs, many=True).data)


class EnvironmentViewSet(viewsets.ReadOnlyModelViewSet):
    """环境（只读视图）"""
    queryset = Environment.objects.select_related('application', 'account').all()
    serializer_class = EnvironmentSerializer
    filterset_fields = ['application', 'env_type']

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """环境下的服务实例"""
        env = self.get_object()
        services = ServiceInstance.objects.filter(environment=env).select_related('resource')
        return Response(ServiceInstanceSerializer(services, many=True).data)

    @action(detail=True, methods=['get'])
    def endpoints(self, request, pk=None):
        """环境下的服务端点"""
        env = self.get_object()
        endpoints = ServiceEndpoint.objects.filter(service__environment=env).select_related('service')
        return Response(ServiceEndpointSerializer(endpoints, many=True).data)


@api_view(['GET'])
def resource_topology(request):
    """资源拓扑图 API - 返回节点和边的关系数据"""
    region = request.query_params.get('region')
    resource_type = request.query_params.get('type')

    resources = Resource.objects.filter(is_deleted=False)
    if region:
        resources = resources.filter(region=region)

    # 获取有关系的资源 ID
    rel_source_ids = set(ResourceRelation.objects.values_list('source_id', flat=True))
    rel_target_ids = set(ResourceRelation.objects.values_list('target_id', flat=True))
    related_ids = rel_source_ids | rel_target_ids

    # 优先展示有关联的资源，可选过滤类型
    if resource_type:
        resources = resources.filter(resource_type=resource_type) | resources.filter(id__in=related_ids)
    else:
        resources = resources.filter(id__in=related_ids) | resources.filter(resource_type='instance')

    resources = resources.distinct()[:100]

    relations = ResourceRelation.objects.select_related('source', 'target').all()

    resource_ids = set(resources.values_list('id', flat=True))

    # 构建节点
    nodes = []
    for r in resources:
        nodes.append({
            'id': r.id,
            'label': r.resource_name,
            'type': r.resource_type,
            'status': r.status,
            'region': r.region,
            'spec': r.spec,
            'cloud_id': r.cloud_resource_id,
        })

    # 构建边
    edges = []
    for rel in relations:
        if rel.source_id in resource_ids and rel.target_id in resource_ids:
            edges.append({
                'source': rel.source_id,
                'target': rel.target_id,
                'relation': rel.relation_type,
            })

    return Response({'nodes': nodes, 'edges': edges})
