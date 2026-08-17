from rest_framework import serializers
from .models import Release, ReleaseTask, TaskLog, ReleaseVerification


class ReleaseSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    environment_code = serializers.CharField(source='environment.code', read_only=True)
    creator_name = serializers.CharField(source='creator.display_name', read_only=True)
    approvals = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    ci_status = serializers.SerializerMethodField()
    cd_status = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = '__all__'
        read_only_fields = ['release_no', 'creator', 'status', 'current_stage', 'deploy_mode']

    def get_approvals(self, obj):
        from apps.approvals.serializers import ApprovalSerializer
        approvals = obj.approvals.filter(approval_type='release').select_related('approver').order_by('step_order')
        return ApprovalSerializer(approvals, many=True).data

    def get_tasks(self, obj):
        tasks = obj.tasks.all().order_by('id')
        return [{'id': t.id, 'stage': t.stage, 'status': t.status, 'message': t.message or ''} for t in tasks]

    def get_ci_status(self, obj):
        """返回 CI 阶段状态"""
        try:
            return obj.tasks.filter(stage='ci').first().status
        except Exception:
            return None

    def get_cd_status(self, obj):
        """返回 CD 阶段状态"""
        try:
            return obj.tasks.filter(stage='cd').first().status
        except Exception:
            return None

    def create(self, validated_data):
        """自动从 application + environment 推导 env_config"""
        if not validated_data.get('env_config'):
            app = validated_data.get('application')
            env = validated_data.get('environment')
            if app and env:
                try:
                    from apps.applications.models import AppEnvConfig
                    validated_data['env_config'] = AppEnvConfig.objects.get(application=app, environment=env)
                except AppEnvConfig.DoesNotExist:
                    pass
        return super().create(validated_data)


class ReleaseTaskSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    operator_name = serializers.CharField(source='operator.display_name', read_only=True)

    class Meta:
        model = ReleaseTask
        fields = '__all__'


class TaskLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLog
        fields = '__all__'


class ReleaseVerificationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)

    class Meta:
        model = ReleaseVerification
        fields = '__all__'