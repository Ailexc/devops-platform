from rest_framework import serializers
from .models import Application, AppEnvConfig, ImageRegistry


class ApplicationSerializer(serializers.ModelSerializer):
    business_line_name = serializers.CharField(source='business_line.name', read_only=True)
    owner_name = serializers.CharField(source='owner.display_name', read_only=True)
    owner_names = serializers.SerializerMethodField(read_only=True)
    owner_group_name = serializers.CharField(source='owner_group.name', read_only=True)
    product_owner_name = serializers.CharField(source='product_owner.display_name', read_only=True)
    qa_owner_name = serializers.CharField(source='qa_owner.display_name', read_only=True)
    ops_owner_name = serializers.CharField(source='ops_owner.display_name', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'

    def get_owner_names(self, obj):
        """解析 owner_ids 为显示名称列表"""
        from apps.accounts.models import User
        ids = obj.owner_ids or []
        if not ids:
            if obj.owner_id:
                return [obj.owner.display_name]
            return []
        users = User.objects.filter(id__in=ids)
        name_map = {u.id: u.display_name for u in users}
        return [name_map.get(uid, f'用户{uid}') for uid in ids]


class AppEnvConfigSerializer(serializers.ModelSerializer):
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    environment_code = serializers.CharField(source='environment.code', read_only=True)
    environment_deploy_type = serializers.CharField(source='environment.deploy_type', read_only=True)
    environment_deploy_type_display = serializers.CharField(source='environment.get_deploy_type_display', read_only=True)
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)

    class Meta:
        model = AppEnvConfig
        fields = [
            'id', 'application', 'environment', 'cluster', 'namespace',
            'environment_name', 'environment_code', 'environment_deploy_type', 'environment_deploy_type_display',
            'cluster_name', 'namespace_name',
            'deploy_strategy', 'replicas', 'canary_percent',
            'image_repo', 'container_port', 'health_check_path',
            'cpu_limit', 'memory_limit', 'auto_rollback', 'health_check_timeout',
            'created_at', 'updated_at',
        ]


class ImageRegistrySerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(source='get_language_display', read_only=True)

    class Meta:
        model = ImageRegistry
        fields = '__all__'