from rest_framework import serializers
from .models import DeployHistory, PodInstance, RollbackRecord

class DeployHistorySerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    release_no = serializers.CharField(source='release.release_no', read_only=True)

    class Meta:
        model = DeployHistory
        fields = '__all__'

class PodInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PodInstance
        fields = '__all__'

class RollbackRecordSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.display_name', read_only=True)
    class Meta:
        model = RollbackRecord
        fields = '__all__'