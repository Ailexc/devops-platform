"""
事件总线服务

负责发布事件、触发 Webhook 投递。
"""
import hashlib
import hmac
import json
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线：发布事件并触发异步 Webhook 投递。

    使用方式:
        EventBus.publish(
            event_type='process.started',
            instance=instance,
            payload={'instance_no': instance.instance_no},
        )
    """

    @staticmethod
    def publish(event_type: str, instance=None, task=None, ticket=None, payload: dict = None):
        """
        发布事件。
        1. 写入 EventLog
        2. 异步触发 Webhook 投递
        """
        from apps.events.models import EventLog, WebhookSubscription, WebhookDelivery

        event = EventLog.objects.create(
            instance=instance,
            task=task,
            ticket=ticket,
            type=event_type,
            payload=payload or {},
        )

        # 查找匹配的 Webhook 订阅（仅「推送上报」类参与投递；「接收订阅」类不投递）
        subscriptions = WebhookSubscription.objects.filter(
            is_active=True,
            direction=WebhookSubscription.Direction.PUSH,
        )
        for sub in subscriptions:
            if event_type in sub.events or '*' in sub.events:
                WebhookDelivery.objects.create(
                    subscription=sub,
                    event=event,
                )

        logger.info(f'事件发布: {event_type}, event_id={event.id}')

        # 异步触发所有 pending 的投递
        _deliver_pending_webhooks.delay()

        return event


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def _deliver_pending_webhooks(self):
    """
    投递所有 pending 的 Webhook。
    """
    import requests as http_requests
    from apps.events.models import WebhookDelivery

    deliveries = WebhookDelivery.objects.filter(
        status=WebhookDelivery.Status.PENDING,
    ).select_related('subscription', 'event')[:20]

    for delivery in deliveries:
        sub = delivery.subscription
        event = delivery.event

        payload = {
            'event_type': event.type,
            'event_id': event.id,
            'payload': event.payload,
            'timestamp': event.created_at.isoformat() if event.created_at else '',
        }

        # 构建签名
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(payload, ensure_ascii=False, default=str)
        if sub.secret:
            signature = hmac.new(
                sub.secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'

        # Demo：示例域名（*.example.com / localhost）模拟投递成功，不发真实请求
        if any(host in sub.url for host in ('example.com', 'localhost', '127.0.0.1')):
            delivery.attempt += 1
            delivery.last_attempt_at = timezone.now()
            delivery.last_response = '200 OK（模拟投递）'
            delivery.status = WebhookDelivery.Status.DELIVERED
            delivery.save(update_fields=[
                'attempt', 'last_response', 'last_attempt_at', 'status', 'updated_at',
            ])
            continue

        delivery.attempt += 1
        delivery.last_attempt_at = timezone.now()

        try:
            response = http_requests.post(
                sub.url,
                data=body,
                headers=headers,
                timeout=10,
            )
            delivery.last_response = f'{response.status_code} {response.text[:500]}'
            if response.status_code < 400:
                delivery.status = WebhookDelivery.Status.DELIVERED
            else:
                delivery.status = WebhookDelivery.Status.FAILED
        except Exception as e:
            delivery.last_response = str(e)[:500]
            delivery.status = WebhookDelivery.Status.FAILED

        delivery.save(update_fields=[
            'attempt', 'last_response', 'last_attempt_at', 'status', 'updated_at',
        ])
