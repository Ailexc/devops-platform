from rest_framework import serializers
from .models import EventLog, WebhookSubscription, WebhookDelivery


class EventLogSerializer(serializers.ModelSerializer):
    """事件日志序列化器"""
    instance_no = serializers.CharField(source='instance.instance_no', read_only=True, default='')

    class Meta:
        model = EventLog
        fields = [
            'id', 'instance', 'instance_no', 'task', 'ticket',
            'type', 'payload', 'created_at',
        ]
        read_only_fields = ['created_at']


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    """Webhook 订阅序列化器"""
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)

    class Meta:
        model = WebhookSubscription
        fields = [
            'id', 'url', 'name', 'events', 'secret', 'direction', 'direction_display', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Webhook 投递序列化器"""
    event_type = serializers.CharField(source='event.type', read_only=True)
    subscription_name = serializers.CharField(source='subscription.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'subscription', 'subscription_name',
            'event', 'event_type',
            'attempt', 'status', 'status_display',
            'last_response', 'last_attempt_at',
            'created_at',
        ]
        read_only_fields = ['created_at']
