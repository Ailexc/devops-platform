from rest_framework import serializers
from .models import Environment, Cluster, K8sNamespace


class EnvironmentSerializer(serializers.ModelSerializer):
    deploy_type_display = serializers.CharField(source='get_deploy_type_display', read_only=True)

    class Meta:
        model = Environment
        fields = '__all__'


class ClusterSerializer(serializers.ModelSerializer):
    environment_name = serializers.CharField(source='environment.name', read_only=True)

    class Meta:
        model = Cluster
        fields = '__all__'


class K8sNamespaceSerializer(serializers.ModelSerializer):
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)

    class Meta:
        model = K8sNamespace
        fields = '__all__'