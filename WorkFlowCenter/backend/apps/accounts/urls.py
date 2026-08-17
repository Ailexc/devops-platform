from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .views import UserViewSet, DepartmentViewSet, RoleViewSet

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def quick_login_list(request):
    """获取可快速登录的用户列表"""
    users = User.objects.filter(is_active=True).select_related('department').values(
        'id', 'username', 'first_name', 'last_name', 'email',
        'department__name'
    )
    return Response(list(users))


@api_view(['POST'])
@permission_classes([AllowAny])
def quick_login(request):
    """快速登录（使用默认密码）"""
    from django.contrib.auth import authenticate
    
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'detail': '请选择用户'}, status=400)
    
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return Response({'detail': '用户不存在'}, status=404)
    
    # 使用默认密码验证
    authenticated = authenticate(username=user.username, password='admin123')
    if not authenticated:
        # 如果密码不对，尝试重置为默认密码
        user.set_password('admin123')
        user.save()
        authenticated = authenticate(username=user.username, password='admin123')
    
    if not authenticated:
        return Response({'detail': '登录失败'}, status=401)
    
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


router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('departments', DepartmentViewSet, basename='department')
router.register('roles', RoleViewSet, basename='role')

urlpatterns = [
    # 快速登录端点（无需认证）
    path('users/quick-login-list/', quick_login_list, name='quick-login-list'),
    path('users/quick-login/', quick_login, name='quick-login'),
    # 其他路由
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
