from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import TicketType, Ticket, Comment, Notification

User = get_user_model()


class TicketTypeSerializer(serializers.ModelSerializer):
    """工单类型序列化器"""
    class Meta:
        model = TicketType
        fields = [
            'id', 'code', 'name', 'description',
            'priority_matrix', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TicketListSerializer(serializers.ModelSerializer):
    """工单列表序列化器（精简）"""
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    started_by_name = serializers.CharField(source='started_by.get_full_name', read_only=True, default='')
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_type', 'ticket_type_name',
            'status', 'status_display',
            'priority', 'priority_display',
            'title', 'description',
            'started_by', 'started_by_name',
            'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    """工单详情序列化器（完整）"""
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    started_by_name = serializers.CharField(source='started_by.get_full_name', read_only=True, default='')
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    instance_no = serializers.CharField(source='instance.instance_no', read_only=True, default='')
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_type', 'ticket_type_name',
            'instance', 'instance_no',
            'form_data',
            'status', 'status_display',
            'priority', 'priority_display',
            'title', 'description',
            'started_by', 'started_by_name',
            'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'comments_count',
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, default='')

    class Meta:
        model = Comment
        fields = [
            'id', 'ticket', 'user', 'user_name',
            'content', 'visibility',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'type', 'type_display',
            'title', 'content', 'is_read',
            'created_at',
        ]
        read_only_fields = ['created_at']
