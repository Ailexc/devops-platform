from django.contrib import admin
from .models import TicketType, Ticket, Comment, Notification

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'ticket_type', 'status', 'priority', 'started_by', 'created_at']
    list_filter = ['status', 'priority']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'visibility', 'created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
