from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import EventLog, WebhookSubscription, WebhookDelivery
from .serializers import (
    EventLogSerializer,
    WebhookSubscriptionSerializer,
    WebhookDeliverySerializer,
)
from .services.event_bus import _deliver_pending_webhooks


class WebhookStatsView(APIView):
    """集成健康度：投递汇总 + 各订阅状态 + 最近失败"""

    def get(self, request):
        summary = {
            'total': WebhookDelivery.objects.count(),
            'delivered': WebhookDelivery.objects.filter(status=WebhookDelivery.Status.DELIVERED).count(),
            'failed': WebhookDelivery.objects.filter(status=WebhookDelivery.Status.FAILED).count(),
            'pending': WebhookDelivery.objects.filter(status=WebhookDelivery.Status.PENDING).count(),
        }
        subs = []
        for sub in WebhookSubscription.objects.filter(is_active=True):
            last = WebhookDelivery.objects.filter(subscription=sub).order_by('-created_at').first()
            subs.append({
                'id': sub.id,
                'name': sub.name,
                'url': sub.url,
                'events': sub.events or [],
                'total': WebhookDelivery.objects.filter(subscription=sub).count(),
                'failed': WebhookDelivery.objects.filter(subscription=sub, status=WebhookDelivery.Status.FAILED).count(),
                'last_status': last.status if last else None,
                'last_status_display': last.get_status_display() if last else None,
                'last_time': last.last_attempt_at or last.created_at if last else None,
                'last_response': last.last_response if last else None,
            })
        recent_failed = [
            {
                'id': d.id,
                'subscription_name': d.subscription.name,
                'event_type': d.event.type,
                'last_response': d.last_response,
                'last_attempt_at': d.last_attempt_at,
            }
            for d in WebhookDelivery.objects.filter(status=WebhookDelivery.Status.FAILED)
            .select_related('subscription', 'event').order_by('-created_at')[:10]
        ]
        return Response({'summary': summary, 'subscriptions': subs, 'recent_failed': recent_failed})


class WebhookDeliveryRetryView(APIView):
    """重放投递（仅失败 / 待投递）"""

    def post(self, request, pk):
        delivery = get_object_or_404(WebhookDelivery, pk=pk)
        if delivery.status not in (WebhookDelivery.Status.FAILED, WebhookDelivery.Status.PENDING):
            return Response({'detail': '仅失败 / 待投递的投递记录可重放'}, status=400)
        delivery.status = WebhookDelivery.Status.PENDING
        delivery.attempt = 0
        delivery.save(update_fields=['status', 'attempt', 'updated_at'])
        _deliver_pending_webhooks.delay()
        return Response({'detail': '已重新投递', 'id': delivery.id})


class EventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """事件日志视图集"""
    queryset = EventLog.objects.select_related('instance', 'task', 'ticket').all()
    serializer_class = EventLogSerializer
    filterset_fields = ['type', 'instance', 'task', 'ticket']
    search_fields = ['type']


class WebhookSubscriptionViewSet(viewsets.ModelViewSet):
    """Webhook 订阅视图集"""
    queryset = WebhookSubscription.objects.all()
    serializer_class = WebhookSubscriptionSerializer
    filterset_fields = ['is_active']


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """Webhook 投递视图集"""
    queryset = WebhookDelivery.objects.select_related('subscription', 'event').all()
    serializer_class = WebhookDeliverySerializer
    filterset_fields = ['status', 'subscription']
