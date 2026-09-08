from django.test import TestCase
from .models import EventLog, WebhookSubscription, WebhookDelivery
from .services.event_bus import EventBus


class EventBusTest(TestCase):
    """事件总线测试"""

    def test_publish_event(self):
        event = EventBus.publish(
            event_type='process.started',
            payload={'instance_no': 'WI-20260804-001'},
        )
        self.assertEqual(event.type, 'process.started')
        self.assertEqual(event.payload['instance_no'], 'WI-20260804-001')

    def test_publish_triggers_webhook(self):
        sub = WebhookSubscription.objects.create(
            url='https://example.com/webhook',
            name='Test Hook',
            events=['process.started'],
        )
        EventBus.publish(
            event_type='process.started',
            payload={'test': True},
        )
        self.assertEqual(WebhookDelivery.objects.count(), 1)
        delivery = WebhookDelivery.objects.first()
        self.assertEqual(delivery.subscription, sub)

    def test_publish_wildcard_subscription(self):
        WebhookSubscription.objects.create(
            url='https://example.com/hook',
            name='Wildcard',
            events=['*'],
        )
        EventBus.publish(event_type='task.completed', payload={})
        self.assertEqual(WebhookDelivery.objects.count(), 1)
