from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, Role, Permission, Department, OperationLog
from .serializers import (
    LoginSerializer, UserSerializer, UserCreateSerializer,
    RoleSerializer, PermissionSerializer, DepartmentSerializer,
    ChangePasswordSerializer, UserProfileSerializer, OperationLogSerializer
)


class LoginView(APIView):
    """登录接口"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class UserProfileView(APIView):
    """当前用户信息"""
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """修改密码"""
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': '密码修改成功'})


class UserViewSet(viewsets.ModelViewSet):
    """用户管理"""
    queryset = User.objects.select_related('department').all()
    serializer_class = UserSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'display_name', 'email']
    ordering_fields = ['date_joined', 'username']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """重置密码"""
        user = self.get_object()
        new_password = request.data.get('new_password', '123456')
        user.set_password(new_password)
        user.save()
        return Response({'message': '密码已重置'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """当前登录用户信息"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """权限管理（只读）"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        module = self.request.query_params.get('module')
        if module:
            qs = qs.filter(module=module)
        return qs


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['sort_order', 'created_at']


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作审计日志"""
    queryset = OperationLog.objects.select_related('user').all()
    serializer_class = OperationLogSerializer
    filterset_fields = ['module', 'action', 'username']
    search_fields = ['username', 'action', 'resource_id']
    ordering_fields = ['created_at']
