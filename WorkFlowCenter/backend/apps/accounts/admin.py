from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Department, User

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'manager', 'created_at']
    list_filter = ['parent']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'department', 'is_staff', 'is_active']
    list_filter = ['department', 'is_staff', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('department',)}),
    )
