from rest_framework import serializers
from .models import ServiceCategory, ServiceItem, Quota


class ServiceCategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'icon', 'sort_order', 'items_count', 'created_at']

    def get_items_count(self, obj):
        return obj.items.filter(status='active').count()


class ServiceItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ServiceItem
        fields = ['id', 'name', 'category', 'category_name', 'description', 'icon',
                  'spec_options', 'region_options', 'status', 'created_at']


class QuotaSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    service_item_name = serializers.CharField(source='service_item.name', read_only=True)
    available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Quota
        fields = ['id', 'department', 'department_name', 'service_item',
                  'service_item_name', 'quota_limit', 'used', 'available', 'updated_at']
