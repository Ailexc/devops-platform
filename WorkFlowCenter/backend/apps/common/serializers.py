from rest_framework import serializers

from .models import AIConfig


class AIConfigSerializer(serializers.ModelSerializer):
    """AI 配置序列化器"""
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    has_key = serializers.BooleanField(source='has_api_key', read_only=True, help_text='环境变量中是否已配置 API Key')
    key_env = serializers.CharField(source='api_key_env_name', read_only=True, help_text='API Key 对应的环境变量名')

    class Meta:
        model = AIConfig
        fields = [
            'id', 'provider', 'provider_display', 'model_id',
            'api_base', 'is_active', 'has_key', 'key_env',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class GenerateFormSerializer(serializers.Serializer):
    """AI 表单生成请求体"""
    prompt = serializers.CharField(help_text='自然语言指令')
    provider = serializers.ChoiceField(
        choices=AIConfig.Provider.choices,
        required=False,
        help_text='AI 提供商',
    )
    config_id = serializers.IntegerField(required=False, help_text='AI 配置 ID')


class TestConnectionSerializer(serializers.Serializer):
    """AI 连接测试请求体"""
    config_id = serializers.IntegerField(required=False, help_text='AI 配置 ID')
    provider = serializers.ChoiceField(
        choices=AIConfig.Provider.choices,
        required=False,
        help_text='AI 提供商',
    )


class GenerateFlowSerializer(serializers.Serializer):
    """AI 流程生成请求体"""
    prompt = serializers.CharField(help_text='自然语言指令')
    provider = serializers.ChoiceField(
        choices=AIConfig.Provider.choices,
        required=False,
        help_text='AI 提供商',
    )
    config_id = serializers.IntegerField(required=False, help_text='AI 配置 ID')
    current_form = serializers.DictField(required=False, help_text='当前表单 schema')
