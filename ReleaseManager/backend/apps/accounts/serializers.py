from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'email', 'avatar_url',
                  'is_active', 'is_group_leader', 'is_audit_admin']


class UserListSerializer(serializers.ModelSerializer):
    """用户列表（登录选择用）"""
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'email']