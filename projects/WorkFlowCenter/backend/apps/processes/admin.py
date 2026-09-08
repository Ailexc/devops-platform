from django.contrib import admin
from .models import ProcessDefinition, ProcessInstance, NodeTask, TaskInstance, ApprovalRecord, InitiatorApp

@admin.register(ProcessDefinition)
class ProcessDefinitionAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'version', 'status', 'created_by', 'created_at']
    list_filter = ['status']

@admin.register(ProcessInstance)
class ProcessInstanceAdmin(admin.ModelAdmin):
    list_display = ['instance_no', 'definition', 'status', 'started_by', 'started_at']
    list_filter = ['status']

@admin.register(NodeTask)
class NodeTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'instance', 'node_key', 'node_name', 'assignee', 'status', 'result']
    list_filter = ['status', 'node_type']

@admin.register(TaskInstance)
class TaskInstanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'assignee', 'status', 'result']

@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = ['instance', 'user', 'action', 'opinion', 'created_at']


@admin.register(InitiatorApp)
class InitiatorAppAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
