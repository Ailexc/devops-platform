from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import ConfigTemplate, ConfigVariable, ConfigVariableValue, ConfigRelease
from apps.infrastructures.models import Environment


class ConfigTemplateSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    app_name = serializers.CharField(source='application.name', read_only=True)  # 兼容前端
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)

    class Meta:
        model = ConfigTemplate
        fields = '__all__'


class ConfigVariableSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    # 兼容前端：template_id 可读可写（映射到 template 外键），默认 template 字段隐藏
    template_id = serializers.PrimaryKeyRelatedField(
        source='template', queryset=ConfigTemplate.objects.all()
    )

    class Meta:
        model = ConfigVariable
        fields = '__all__'
        extra_kwargs = {'template': {'required': False, 'write_only': True}}
        validators = [
            UniqueTogetherValidator(
                queryset=ConfigVariable.objects.all(),
                fields=['template_id', 'key'],
            )
        ]


class ConfigVariableValueSerializer(serializers.ModelSerializer):
    variable_key = serializers.CharField(source='variable.key', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    # 兼容前端：variable_id / environment_id 可读可写
    variable_id = serializers.PrimaryKeyRelatedField(
        source='variable', queryset=ConfigVariable.objects.all()
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        source='environment', queryset=Environment.objects.all()
    )

    class Meta:
        model = ConfigVariableValue
        fields = '__all__'
        extra_kwargs = {
            'variable': {'required': False, 'write_only': True},
            'environment': {'required': False, 'write_only': True},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=ConfigVariableValue.objects.all(),
                fields=['variable_id', 'environment_id'],
            )
        ]


class ConfigReleaseSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    # 兼容前端：template_id / environment_id 可读可写
    template_id = serializers.PrimaryKeyRelatedField(
        source='template', queryset=ConfigTemplate.objects.all()
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        source='environment', queryset=Environment.objects.all()
    )

    class Meta:
        model = ConfigRelease
        fields = '__all__'
        extra_kwargs = {
            'template': {'required': False, 'write_only': True},
            'environment': {'required': False, 'write_only': True},
        }