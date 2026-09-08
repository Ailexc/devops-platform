from rest_framework import serializers

from .models import Scenario, ScenarioStep


class ScenarioStepSerializer(serializers.ModelSerializer):
    """场景步骤序列化器"""
    class Meta:
        model = ScenarioStep
        fields = ['id', 'step_no', 'name', 'action_type', 'action_params_template',
                  'depends_on', 'need_approval', 'retry_max', 'skip_if_missing',
                  'rollback_action_type', 'enabled']


class ScenarioSerializer(serializers.ModelSerializer):
    """场景定义序列化器（含步骤）"""
    steps = ScenarioStepSerializer(many=True, read_only=True)
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = Scenario
        fields = ['id', 'code', 'name', 'description', 'icon', 'need_approval',
                  'enabled', 'version', 'steps', 'step_count', 'created_at', 'updated_at']

    def get_step_count(self, obj):
        return obj.steps.filter(enabled=True).count()
