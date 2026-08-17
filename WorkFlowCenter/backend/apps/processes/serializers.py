from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    ProcessDefinition,
    ProcessInstance,
    NodeTask,
    TaskInstance,
    ApprovalRecord,
    InitiatorApp,
)

User = get_user_model()


class ProcessDefinitionSerializer(serializers.ModelSerializer):
    """流程定义序列化器"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    submit_scope_display = serializers.CharField(source='get_submit_scope_display', read_only=True)
    timeout_action_display = serializers.CharField(source='get_timeout_action_display', read_only=True)
    initiator_app_names = serializers.SerializerMethodField(read_only=True)

    def get_initiator_app_names(self, obj):
        ids = obj.initiator_app_ids or []
        if not ids:
            return []
        name_map = {app.id: app.name for app in InitiatorApp.objects.filter(id__in=ids)}
        return [name_map.get(i, f'#{i}') for i in ids]

    class Meta:
        model = ProcessDefinition
        fields = [
            'id', 'key', 'name', 'version', 'status',
            'definition_json', 'form_schema', 'rules_json',
            'category', 'category_display',
            'icon', 'submit_scope', 'submit_scope_display',
            'submit_scope_ids', 'admin_ids', 'group_id',
            'allow_withdraw', 'allow_transfer',
            'timeout_hours', 'timeout_action', 'timeout_action_display',
            'allow_program_initiate', 'initiator_app_ids', 'initiator_app_names',
            'launch_status', 'allow_self_approve',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class InitiatorAppSerializer(serializers.ModelSerializer):
    """发起程序序列化器（不返回 API Key 明文）"""
    has_key = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InitiatorApp
        fields = ['id', 'name', 'code', 'is_active', 'has_key', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_has_key(self, obj):
        return bool(obj.api_key_hash)


class ProcessInstanceSerializer(serializers.ModelSerializer):
    """流程实例序列化器"""
    definition_name = serializers.CharField(source='definition.name', read_only=True)
    started_by_name = serializers.CharField(source='started_by.get_full_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProcessInstance
        fields = [
            'id', 'definition', 'definition_name',
            'instance_no', 'status', 'status_display',
            'current_node_key', 'variables', 'business_key',
            'started_by', 'started_by_name',
            'started_at', 'ended_at', 'updated_at',
        ]
        read_only_fields = ['instance_no', 'started_at', 'ended_at', 'updated_at']


class NodeTaskSerializer(serializers.ModelSerializer):
    """节点任务序列化器"""
    assignee_name = serializers.CharField(source='assignee.get_full_name', read_only=True, default='')
    instance_no = serializers.CharField(source='instance.instance_no', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_config_mode = serializers.SerializerMethodField(read_only=True)

    def get_task_config_mode(self, obj):
        """办理节点任务配置模式：manual / confirm / auto（供前端判断确认任务）"""
        from .services.definition_convert import normalized_definition
        try:
            nodes = normalized_definition(obj.instance.definition.definition_json)['nodes']
        except Exception:
            return None
        node = next((n for n in nodes if n.get('key') == obj.node_key), None)
        if not node:
            return None
        return (node.get('taskConfig') or {}).get('mode', 'manual')

    class Meta:
        model = NodeTask
        fields = [
            'id', 'instance', 'instance_no',
            'node_key', 'node_name', 'node_type', 'approval_type',
            'assignee', 'assignee_name', 'candidate_users',
            'task_config_mode',
            'status', 'status_display', 'result', 'opinion',
            'due_at', 'countersign',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskInstanceSerializer(serializers.ModelSerializer):
    """任务实例序列化器"""
    assignee_name = serializers.CharField(source='assignee.get_full_name', read_only=True, default='')
    node_key = serializers.CharField(source='task.node_key', read_only=True)
    node_name = serializers.CharField(source='task.node_name', read_only=True)

    class Meta:
        model = TaskInstance
        fields = [
            'id', 'task', 'node_key', 'node_name',
            'assignee', 'assignee_name',
            'status', 'result', 'opinion',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """审批记录序列化器"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    initiator_source_display = serializers.SerializerMethodField(read_only=True)

    def get_initiator_source_display(self, obj):
        """发起来源展示：人员发起 / 程序发起（程序名称）"""
        if not obj.initiator_source:
            return '人员发起'
        app = InitiatorApp.objects.filter(code=obj.initiator_source).first()
        name = app.name if app else obj.initiator_source
        return f'程序发起（{name}）'

    class Meta:
        model = ApprovalRecord
        fields = [
            'id', 'instance', 'task', 'user', 'user_name',
            'initiator_source', 'initiator_source_display',
            'action', 'action_display', 'opinion',
            'created_at',
        ]
        read_only_fields = ['created_at']


class CheckDefinitionSerializer(serializers.Serializer):
    """流程检查请求体"""
    name = serializers.CharField(required=False, allow_blank=True, default='', help_text='流程名称')
    key = serializers.CharField(required=False, allow_blank=True, default='', help_text='唯一标识')
    submit_scope = serializers.CharField(required=False, allow_blank=True, default='', help_text='提交范围')
    submit_scope_ids = serializers.ListField(required=False, default=list, help_text='提交范围 ID 列表')
    admin_ids = serializers.ListField(required=False, default=list, help_text='流程管理员 ID 列表')
    allow_program_initiate = serializers.BooleanField(required=False, default=False, help_text='是否允许程序发起')
    initiator_app_ids = serializers.ListField(required=False, default=list, help_text='可发起程序 ID 列表')
    launch_status = serializers.CharField(required=False, allow_blank=True, default='', help_text='上线状态')
    allow_self_approve = serializers.BooleanField(required=False, default=True, help_text='允许发起人自己审批')
    definition_json = serializers.DictField(default=dict, help_text='流程定义（Beeflow JSON）')
    form_schema = serializers.DictField(default=dict, help_text='表单 Schema')
    rules_json = serializers.ListField(required=False, default=list, help_text='业务规则（结构化 AST）')


class StartProcessSerializer(serializers.Serializer):
    """启动流程的请求体"""
    definition_id = serializers.IntegerField(help_text='流程定义 ID')
    form_data = serializers.DictField(default=dict, help_text='表单数据 / 流程变量')
    business_key = serializers.CharField(required=False, default='', help_text='业务主键（程序发起必填，用于幂等）')
    initiator_user_id = serializers.IntegerField(
        required=False, allow_null=True, default=None,
        help_text='程序发起时的提单人用户 ID（人员发起无需传）',
    )


class CompleteTaskSerializer(serializers.Serializer):
    """完成任务的请求体"""
    result = serializers.ChoiceField(
        choices=['approve', 'reject'],
        default='approve',
        help_text='审批结果',
    )
    opinion = serializers.CharField(required=False, default='', help_text='审批意见')


class DelegateTaskSerializer(serializers.Serializer):
    """转办任务的请求体"""
    to_user_id = serializers.IntegerField(help_text='目标用户 ID')
