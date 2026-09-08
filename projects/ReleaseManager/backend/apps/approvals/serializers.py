from rest_framework import serializers
from .models import Approval


class ApprovalReleaseSerializer(serializers.Serializer):
    """发布审批中 release 的简要信息"""
    id = serializers.IntegerField()
    release_no = serializers.CharField()
    title = serializers.CharField()
    version = serializers.CharField()
    environment_name = serializers.SerializerMethodField()
    environment_code = serializers.SerializerMethodField()
    application_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()

    def get_environment_name(self, obj):
        env = getattr(obj, 'environment', None)
        return env.name if env else '-'

    def get_environment_code(self, obj):
        env = getattr(obj, 'environment', None)
        return env.code if env else ''

    def get_application_name(self, obj):
        app = getattr(obj, 'application', None)
        return app.name if app else '-'

    def get_creator_name(self, obj):
        c = getattr(obj, 'creator', None)
        if c:
            return getattr(c, 'display_name', None) or getattr(c, 'username', '-')
        return '-'


class ApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.display_name', read_only=True)
    release_title = serializers.CharField(source='release.title', read_only=True)
    release_no = serializers.CharField(source='release.release_no', read_only=True)
    release_detail = serializers.SerializerMethodField()
    applicant_name = serializers.SerializerMethodField()
    app_name = serializers.SerializerMethodField()
    env_type = serializers.SerializerMethodField()
    grant_scope = serializers.SerializerMethodField()
    request_type = serializers.SerializerMethodField()
    request_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = '__all__'

    def get_release_detail(self, obj):
        if obj.release:
            return ApprovalReleaseSerializer(obj.release).data
        return None

    def get_request_type(self, obj):
        if obj.permission_request:
            return obj.permission_request.request_type
        return None

    def get_request_type_label(self, obj):
        if obj.permission_request:
            return dict(obj.permission_request.REQUEST_TYPES).get(obj.permission_request.request_type, '')
        return None

    def get_applicant_name(self, obj):
        if obj.permission_request:
            return obj.permission_request.user.display_name
        return None

    def get_app_name(self, obj):
        if obj.approval_type == 'scale' and obj.extra_data:
            return obj.extra_data.get('app_name')
        if obj.permission_request:
            from apps.applications.models import Application
            app = Application.objects.filter(id=obj.permission_request.app_id).first()
            return app.name if app else None
        return None

    def get_env_type(self, obj):
        if obj.approval_type == 'scale' and obj.extra_data:
            return obj.extra_data.get('env_code')
        if obj.permission_request:
            return obj.permission_request.env_type
        return None

    def get_grant_scope(self, obj):
        if obj.permission_request:
            return obj.permission_request.grant_scope
        return None