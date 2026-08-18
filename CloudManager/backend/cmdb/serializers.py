from rest_framework import serializers
from .models import (
    CloudAccount, Resource, ResourceRelation, ResourceChange, Application,
    ServiceInstance, ServiceEndpoint, SecurityRule, SyncJob, Environment,
)


class CloudAccountSerializer(serializers.ModelSerializer):
    """云账号序列化器"""
    provider_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CloudAccount
        fields = [
            'id', 'account_name', 'provider_type', 'provider_display',
            'regions', 'status', 'status_display', 'sync_status',
            'last_sync_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_sync_time', 'created_at', 'updated_at']


class ResourceSerializer(serializers.ModelSerializer):
    """资源序列化器"""
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True, default='')
    managed_by_display = serializers.CharField(source='get_managed_by_display', read_only=True, default='')

    class Meta:
        model = Resource
        fields = [
            'id', 'account', 'account_name', 'provider_type', 'resource_type',
            'resource_type_display', 'resource_name', 'cloud_resource_id',
            'region', 'zone', 'status', 'spec', 'department', 'application', 'environment',
            'environment_name',
            'metadata', 'source', 'managed_by', 'managed_by_display',
            'source_system', 'sync_mode', 'external_id',
            'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ResourceListSerializer(serializers.ModelSerializer):
    """资源列表简化序列化器"""
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    managed_by_display = serializers.CharField(source='get_managed_by_display', read_only=True, default='')

    class Meta:
        model = Resource
        fields = [
            'id', 'account', 'account_name', 'provider_type', 'resource_type',
            'resource_name', 'cloud_resource_id', 'region', 'status', 'spec',
            'metadata', 'managed_by', 'managed_by_display', 'created_at'
        ]


class ResourceRelationSerializer(serializers.ModelSerializer):
    """资源关系序列化器"""
    source_name = serializers.CharField(source='source.resource_name', read_only=True)
    target_name = serializers.CharField(source='target.resource_name', read_only=True)

    class Meta:
        model = ResourceRelation
        fields = ['id', 'source', 'source_name', 'target', 'target_name',
                  'relation_type', 'relation_type_display', 'strength', 'relation_source',
                  'metadata', 'created_at']

    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)


class ResourceChangeSerializer(serializers.ModelSerializer):
    """资源变更序列化器"""
    resource_name = serializers.CharField(source='resource.resource_name', read_only=True)

    class Meta:
        model = ResourceChange
        fields = ['id', 'resource', 'resource_name', 'action', 'before_data',
                  'after_data', 'operator', 'source', 'ticket_id', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    """应用序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    app_category_display = serializers.CharField(source='get_app_category_display', read_only=True, default='')
    app_type_display = serializers.CharField(source='get_app_type_display', read_only=True, default='')
    deploy_type_display = serializers.CharField(source='get_deploy_type_display', read_only=True, default='')
    importance_level_display = serializers.CharField(source='get_importance_level_display', read_only=True, default='')
    change_policy_display = serializers.CharField(source='get_change_policy_display', read_only=True, default='')

    class Meta:
        model = Application
        fields = [
            'id', 'name', 'department', 'department_name', 'owner', 'description',
            # 标识与归属
            'app_code', 'app_name_en', 'cmdb_ci_id', 'business_line',
            'app_category', 'app_category_display',
            # 负责人与协作
            'dev_owner', 'ops_owner', 'alert_group', 'creator',
            # 技术元数据
            'language', 'framework', 'app_type', 'app_type_display',
            'git_repo', 'default_branch', 'artifact_repo', 'ci_pipeline',
            'deploy_type', 'deploy_type_display', 'default_cluster',
            # 治理与合规
            'importance_level', 'importance_level_display', 'sla', 'dr_level',
            'change_policy', 'change_policy_display', 'domain', 'tags', 'doc_url',
            'created_at', 'updated_at',
        ]


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    env_type_display = serializers.CharField(source='get_env_type_display', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True, default='')
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = Environment
        fields = ['id', 'application', 'application_name', 'name', 'env_type',
                  'env_type_display', 'account', 'account_name', 'region',
                  'description', 'enabled', 'services_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_services_count(self, obj):
        return obj.services.count()


class ServiceInstanceSerializer(serializers.ModelSerializer):
    """服务实例序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    deploy_type_display = serializers.CharField(source='get_deploy_type_display', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True, default='')
    env_type_display = serializers.CharField(source='environment.get_env_type_display', read_only=True, default='')
    resource_name = serializers.CharField(source='resource.resource_name', read_only=True, default='')
    resource_spec = serializers.CharField(source='resource.spec', read_only=True, default='')
    resources_count = serializers.SerializerMethodField()

    def get_resources_count(self, obj):
        """返回服务关联的资源实例数"""
        if hasattr(obj, 'resources'):
            return obj.resources.count()
        return 1 if obj.resource else 0

    class Meta:
        model = ServiceInstance
        fields = [
            'id', 'application', 'application_name', 'environment', 'environment_name',
            'env_type_display', 'name', 'service_type',
            'service_type_display', 'deploy_type', 'deploy_type_display',
            'region', 'status', 'owner', 'description',
            'resource_name', 'resource_spec', 'resources_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceEndpointSerializer(serializers.ModelSerializer):
    """服务端点序列化器"""
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = ServiceEndpoint
        fields = ['id', 'service', 'service_name', 'protocol', 'port', 'domain',
                  'certificate', 'is_public', 'metadata', 'created_at']


class SecurityRuleSerializer(serializers.ModelSerializer):
    """安全组规则序列化器"""
    security_group_name = serializers.CharField(source='security_group.resource_name', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = SecurityRule
        fields = ['id', 'security_group', 'security_group_name', 'direction',
                  'direction_display', 'protocol', 'port_range', 'source', 'target',
                  'priority', 'action', 'action_display', 'enabled', 'created_at']


class SyncJobSerializer(serializers.ModelSerializer):
    """同步任务序列化器"""
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SyncJob
        fields = ['id', 'job_type', 'job_type_display', 'status', 'status_display',
                  'source_system', 'total_count', 'message', 'created_at', 'finished_at']
