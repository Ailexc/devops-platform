from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EventLogViewSet,
    WebhookSubscriptionViewSet,
    WebhookDeliveryViewSet,
    WebhookStatsView,
    WebhookDeliveryRetryView,
)

router = DefaultRouter()
router.register('events', EventLogViewSet, basename='event')
router.register('webhook-subscriptions', WebhookSubscriptionViewSet, basename='webhook-subscription')
router.register('webhook-deliveries', WebhookDeliveryViewSet, basename='webhook-delivery')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook-stats/', WebhookStatsView.as_view(), name='webhook-stats'),
    path('webhook-deliveries/<int:pk>/retry/', WebhookDeliveryRetryView.as_view(), name='webhook-delivery-retry'),
]
