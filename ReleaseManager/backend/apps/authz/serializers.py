from rest_framework import serializers
from .models import Role, RoleDataRule, SubjectMembership, EffectivePermissionCache, PermissionRequest, EnvironmentApprovalConfig, ApprovalFlowTemplate, AppChangeApprovalConfig, ReleaseApprovalConfig
from apps.accounts.models import User
from apps.organizations.models import Group


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class RoleDataRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = RoleDataRule
        fields = '__all__'


class SubjectMembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = SubjectMembership
        fields = '__all__'


class EffectivePermissionCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = EffectivePermissionCache
        fields = '__all__'


class PermissionRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    app_name = serializers.SerializerMethodField(read_only=True)
    env_type_label = serializers.SerializerMethodField(read_only=True)
    approval_progress = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PermissionRequest
        fields = '__all__'

    def get_app_name(self, obj):
        try:
            from apps.applications.models import Application
            return Application.objects.get(id=obj.app_id).name
        except Exception:
            return None

    def get_env_type_label(self, obj):
        labels = {'dev': '开发', 'test': '测试', 'staging': '预发', 'prod': '生产'}
        return labels.get(obj.env_type, obj.env_type)

    def get_approval_progress(self, obj):
        from apps.approvals.models import Approval
        approvals = Approval.objects.filter(permission_request=obj).order_by('step_order', 'id')
        if not approvals.exists():
            return None
        total = approvals.count()
        approved = approvals.filter(action='approved').count()
        rejected = approvals.filter(action='rejected').count()
        pending = approvals.filter(action='pending').count()
        steps = []
        for a in approvals:
            steps.append({
                'step_order': a.step_order,
                'step_name': a.step_name,
                'action': a.action,
                'approver_name': a.approver.display_name if a.approver else None,
                'comment': a.comment,
                'updated_at': a.updated_at,
            })
        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'steps': steps,
        }


class EnvironmentApprovalConfigSerializer(serializers.ModelSerializer):
    flow_template_name = serializers.CharField(source='flow_template.name', read_only=True, allow_null=True)

    class Meta:
        model = EnvironmentApprovalConfig
        fields = '__all__'


class ApprovalFlowTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalFlowTemplate
        fields = '__all__'


# ─── 权限展示用 Serializer ───────────────────────────────

class DataRuleDetailSerializer(serializers.Serializer):
    """单条数据规则详情（前端展示用）"""
    id = serializers.IntegerField()
    app_id = serializers.IntegerField()
    app_name = serializers.CharField()
    env_type = serializers.CharField()
    env_type_label = serializers.CharField()
    is_all_envs = serializers.BooleanField()
    allow_env_ids = serializers.ListField(child=serializers.IntegerField())
    deny_env_ids = serializers.ListField(child=serializers.IntegerField())
    grant_scope = serializers.CharField()
    grant_scope_label = serializers.CharField()
    valid_from = serializers.DateTimeField(allow_null=True)
    valid_to = serializers.DateTimeField(allow_null=True)
    business_line_id = serializers.IntegerField()
    owner_group_id = serializers.IntegerField()


class GroupPermissionSummarySerializer(serializers.Serializer):
    """组权限摘要"""
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    own_rules = serializers.ListField(child=DataRuleDetailSerializer())
    member_count = serializers.IntegerField()


class UserPermissionSummarySerializer(serializers.Serializer):
    """用户权限摘要"""
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    groups = serializers.ListField(child=serializers.DictField())
    group_rules = serializers.ListField(child=DataRuleDetailSerializer())
    user_rules = serializers.ListField(child=DataRuleDetailSerializer())


class AppChangeApprovalConfigSerializer(serializers.ModelSerializer):
    flow_template_name = serializers.CharField(source='flow_template.name', read_only=True)

    class Meta:
        model = AppChangeApprovalConfig
        fields = '__all__'


class ReleaseApprovalConfigSerializer(serializers.ModelSerializer):
    flow_template_name = serializers.CharField(source='flow_template.name', read_only=True)

    class Meta:
        model = ReleaseApprovalConfig
        fields = '__all__'