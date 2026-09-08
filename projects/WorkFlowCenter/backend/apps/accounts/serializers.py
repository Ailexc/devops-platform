from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Department

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True, default='')
    children_count = serializers.IntegerField(source='children.count', read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'parent', 'manager', 'manager_name',
            'children_count', 'members_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    role_ids = serializers.PrimaryKeyRelatedField(source='groups', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'department', 'department_name',
            'role_ids',
            'is_staff', 'is_active',
            'date_joined',
        ]
        read_only_fields = ['date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'department',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RoleSerializer(serializers.Serializer):
    """角色序列化器（简单实现，基于 Django Group）"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)
    permissions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
    )
