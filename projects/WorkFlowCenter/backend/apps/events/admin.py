from django.contrib import admin
from .models import EventLog, WebhookSubscription, WebhookDelivery

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'instance', 'task', 'ticket', 'created_at']
    list_filter = ['type']

@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'created_at']
    list_filter = ['is_active']

@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription', 'event', 'status', 'attempt', 'last_attempt_at']
    list_filter = ['status']
