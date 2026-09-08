from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role, Permission, Department, UserRole, OperationLog


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        if not user.is_active:
            raise serializers.ValidationError('用户已被禁用')
        attrs['user'] = user
        return attrs


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'sort_order', 'created_at']


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'module', 'description']


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    permissions = PermissionSerializer(many=True, read_only=True, source='role_permissions.permission')

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'is_active', 'permissions', 'created_at']


class RoleSimpleSerializer(serializers.ModelSerializer):
    """角色简化序列化器"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'code']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    roles = RoleSimpleSerializer(many=True, read_only=True, source='user_roles.role')
    department_name = serializers.CharField(source='department.name', read_only=True, default='')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'email', 'phone',
            'department', 'department_name', 'roles', 'is_active', 'date_joined'
        ]
        read_only_fields = ['date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(max_length=128, write_only=True)
    role_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'display_name', 'email', 'phone', 'department', 'role_ids']

    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', [])
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if role_ids:
            roles = Role.objects.filter(id__in=role_ids)
            for role in roles:
                UserRole.objects.create(user=user, role=role)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码错误')
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """用户个人信息序列化器"""
    roles = RoleSimpleSerializer(many=True, read_only=True, source='user_roles.role')
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'email', 'phone',
            'department', 'department_name', 'roles', 'permissions', 'is_active', 'date_joined'
        ]
        read_only_fields = ['date_joined']

    def get_permissions(self, obj):
        """获取用户所有权限编码"""
        perms = set()
        for user_role in obj.user_roles.select_related('role').all():
            for rp in user_role.role.role_permissions.select_related('permission').all():
                perms.add(rp.permission.code)
        return list(perms)


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    class Meta:
        model = OperationLog
        fields = ['id', 'user', 'username', 'module', 'action', 'resource_id',
                  'detail', 'ip', 'created_at']
        read_only_fields = fields
