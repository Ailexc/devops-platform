from django.contrib import admin
from .models import Capability, TaskJob

@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'execute_mode', 'is_active']
    list_filter = ['execute_mode', 'is_active']

@admin.register(TaskJob)
class TaskJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'capability', 'instance', 'status', 'sync', 'created_at']
    list_filter = ['status', 'sync']
