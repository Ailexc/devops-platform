from rest_framework import serializers
from .models import ExecutionRecord


class ExecutionRecordListSerializer(serializers.ModelSerializer):
    """列表页轻量摘要 — 不返回 result/lifecycle/logs（详情页才加载）。"""

    id = serializers.SerializerMethodField()
    task = serializers.CharField(source="task_name")
    start = serializers.SerializerMethodField()
    scope_label = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionRecord
        fields = [
            "id",
            "task",
            "module",
            "target",
            "trigger",
            "scope",
            "scope_label",
            "status",
            "start",
            "started_at",
            "finished_at",
            "duration",
            "detail",
            "error",
            "params",
            "has_children",
        ]

    def get_id(self, obj):
        return f"#{obj.id:05d}"

    def get_start(self, obj):
        return obj.started_at.strftime("%m-%d %H:%M") if obj.started_at else "-"

    def get_scope_label(self, obj):
        return dict(ExecutionRecord.SCOPE_CHOICES).get(obj.scope, obj.scope)

    def get_has_children(self, obj):
        return obj.children.exists()


class ExecutionRecordChildSerializer(serializers.ModelSerializer):
    """进程级子记录（详情页进程列表）。"""

    id = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionRecord
        fields = [
            "id",
            "task_name",
            "status",
            "start",
            "duration",
            "detail",
            "error",
            "result",
            "lifecycle_events",
            "started_at",
            "finished_at",
        ]

    def get_id(self, obj):
        return f"#{obj.id:05d}"

    def get_start(self, obj):
        return obj.started_at.strftime("%H:%M:%S") if obj.started_at else "-"


class ExecutionRecordDetailSerializer(serializers.ModelSerializer):
    """详情页 — 完整记录 + 进程列表（子记录）。"""

    id = serializers.SerializerMethodField()
    task = serializers.CharField(source="task_name")
    start = serializers.SerializerMethodField()
    scope_label = serializers.SerializerMethodField()
    children = ExecutionRecordChildSerializer(many=True, read_only=True)

    class Meta:
        model = ExecutionRecord
        fields = [
            "id",
            "task",
            "module",
            "target",
            "trigger",
            "scope",
            "scope_label",
            "status",
            "celery_task_id",
            "error",
            "detail",
            "duration",
            "result",
            "params",
            "lifecycle_events",
            "start",
            "started_at",
            "finished_at",
            "children",
        ]

    def get_id(self, obj):
        return f"#{obj.id:05d}"

    def get_start(self, obj):
        return obj.started_at.strftime("%m-%d %H:%M") if obj.started_at else "-"

    def get_scope_label(self, obj):
        return dict(ExecutionRecord.SCOPE_CHOICES).get(obj.scope, obj.scope)
