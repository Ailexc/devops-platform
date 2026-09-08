from rest_framework import serializers
from .models import TicketOrder, TicketApproval, TicketTask


class TicketOrderSerializer(serializers.ModelSerializer):
    """工单序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)

    class Meta:
        model = TicketOrder
        fields = [
            'id', 'ticket_no', 'ticket_type', 'ticket_type_display', 'title',
            'status', 'status_display', 'applicant', 'applicant_id', 'approver',
            'resource_id', 'resource_name', 'provider_type',
            'scenario_id', 'scenario_code',
            'request_content', 'result_content', 'fail_reason',
            'created_at', 'updated_at', 'finished_at'
        ]
        read_only_fields = [
            'ticket_no', 'applicant', 'applicant_id', 'scenario_id', 'scenario_code',
            'created_at', 'updated_at', 'finished_at',
        ]


class TicketOrderListSerializer(serializers.ModelSerializer):
    """工单列表简化序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)

    class Meta:
        model = TicketOrder
        fields = [
            'id', 'ticket_no', 'ticket_type', 'ticket_type_display', 'title',
            'status', 'status_display', 'applicant', 'resource_name',
            'provider_type', 'scenario_code', 'created_at', 'finished_at'
        ]


class TicketApprovalSerializer(serializers.ModelSerializer):
    """审批记录序列化器"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = TicketApproval
        fields = [
            'id', 'ticket', 'approver', 'approver_id', 'action',
            'action_display', 'comment', 'approved_at'
        ]
        read_only_fields = ['approved_at']


class TicketTaskSerializer(serializers.ModelSerializer):
    """执行任务序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TicketTask
        fields = [
            'id', 'ticket', 'task_type', 'provider_type', 'status',
            'status_display', 'retry_count', 'max_retry', 'request_id',
            'exec_log', 'started_at', 'finished_at'
        ]
