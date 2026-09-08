from rest_framework import serializers
from .models import Capability, TaskJob


class CapabilitySerializer(serializers.ModelSerializer):
    """能力序列化器"""
    class Meta:
        model = Capability
        fields = [
            'id', 'code', 'name', 'description',
            'input_schema', 'output_schema',
            'execute_mode', 'endpoint', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskJobSerializer(serializers.ModelSerializer):
    """任务执行序列化器"""
    capability_name = serializers.CharField(source='capability.name', read_only=True)
    capability_code = serializers.CharField(source='capability.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TaskJob
        fields = [
            'id', 'instance', 'task',
            'capability', 'capability_name', 'capability_code',
            'job_id', 'status', 'status_display',
            'node_key', 'action_key', 'action_name',
            'logs',
            'input_data', 'output_data', 'sync',
            'error_message',
            'started_at', 'completed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['job_id', 'created_at', 'updated_at']
