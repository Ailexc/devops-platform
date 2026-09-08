from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ServiceCategory, ServiceItem, Quota
from .serializers import ServiceCategorySerializer, ServiceItemSerializer, QuotaSerializer


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.prefetch_related('items').all()
    serializer_class = ServiceCategorySerializer


class ServiceItemViewSet(viewsets.ModelViewSet):
    queryset = ServiceItem.objects.select_related('category').all()
    serializer_class = ServiceItemSerializer
    filterset_fields = ['category', 'status']


class QuotaViewSet(viewsets.ModelViewSet):
    queryset = Quota.objects.select_related('department', 'service_item').all()
    serializer_class = QuotaSerializer
    filterset_fields = ['department']

    @action(detail=False, methods=['get'])
    def my_quota(self, request):
        """当前用户的部门配额"""
        dept = request.user.department
        if not dept:
            return Response([])
        quotas = Quota.objects.filter(department=dept).select_related('service_item')
        serializer = QuotaSerializer(quotas, many=True)
        return Response(serializer.data)
