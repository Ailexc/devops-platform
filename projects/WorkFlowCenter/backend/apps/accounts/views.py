from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Department
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    DepartmentSerializer,
    RoleSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.select_related('department').all()
    filterset_fields = ['department', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        """获取/更新当前用户信息"""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门视图集"""
    queryset = Department.objects.select_related('manager', 'parent').all()
    serializer_class = DepartmentSerializer
    filterset_fields = ['parent', 'manager']
    search_fields = ['name']

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取部门成员"""
        dept = self.get_object()
        members = dept.members.all()
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)


def _role_usage_map():
    """扫描所有流程定义，返回 role_id -> [(流程名, 节点名)]（角色作为审批人/抄送/办理人使用）"""
    from apps.processes.models import ProcessDefinition
    from apps.processes.services.definition_convert import normalized_definition
    usage = {}
    for d in ProcessDefinition.objects.all():
        try:
            nodes = normalized_definition(d.definition_json).get('nodes', [])
        except Exception:
            continue
        for n in nodes:
            for assignee in (n.get('assignees') or []):
                if isinstance(assignee, dict) and assignee.get('assigneeType') == 3:
                    for rid in (assignee.get('roles') or []):
                        usage.setdefault(rid, []).append((d.name, n.get('name') or n.get('key')))
            for t in (n.get('transactors') or []):
                if isinstance(t, dict) and t.get('transactorType') == 3:
                    for rid in (t.get('roles') or []):
                        usage.setdefault(rid, []).append((d.name, n.get('name') or n.get('key')))
            for c in (n.get('ccs') or n.get('cc') or []):
                if isinstance(c, dict) and c.get('ccType') == 3:
                    for rid in (c.get('roles') or []):
                        usage.setdefault(rid, []).append((d.name, n.get('name') or n.get('key')))
    return usage


class RoleViewSet(viewsets.ViewSet):
    """角色视图集（基于 Django Group）"""

    def list(self, request):
        groups = Group.objects.all()
        usage = _role_usage_map()
        data = [
            {
                'id': g.id,
                'name': g.name,
                'permissions': list(g.permissions.values_list('codename', flat=True)),
                'member_count': g.user_set.count(),
                'members': list(g.user_set.values_list('username', flat=True))[:50],
                'used_by': usage.get(g.id, []),
            }
            for g in groups
        ]
        return Response(data)

    def retrieve(self, request, pk=None):
        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        usage = _role_usage_map()
        data = {
            'id': group.id,
            'name': group.name,
            'permissions': list(group.permissions.values_list('codename', flat=True)),
            'member_count': group.user_set.count(),
            'members': list(group.user_set.values_list('username', flat=True))[:50],
            'used_by': usage.get(group.id, []),
        }
        return Response(data)

    def create(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group, _ = Group.objects.get_or_create(name=serializer.validated_data['name'])
        return Response({'id': group.id, 'name': group.name}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            group = Group.objects.get(pk=pk)
            group.delete()
        except Group.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['get'], url_path='quick-login-list', permission_classes=[AllowAny])
    def quick_login_list(self, request):
        """获取可快速登录的用户列表"""
        users = User.objects.filter(is_active=True).select_related('department').values(
            'id', 'username', 'first_name', 'last_name', 'email',
            'department__name'
        )
        return Response(list(users))

    @action(detail=False, methods=['post'], url_path='quick-login', permission_classes=[AllowAny])
    def quick_login(self, request):
        """快速登录（使用默认密码）"""
        from django.contrib.auth import authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': '请选择用户'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 使用默认密码验证
        authenticated = authenticate(username=user.username, password='admin123')
        if not authenticated:
            # 如果密码不对，尝试重置为默认密码
            user.set_password('admin123')
            user.save()
            authenticated = authenticate(username=user.username, password='admin123')
        
        if not authenticated:
            return Response({'detail': '登录失败'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 生成 JWT token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name() or user.username,
            }
        })
