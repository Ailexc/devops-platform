from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import UserSerializer, UserListSerializer
from apps.authz.utils import get_user_effective_permissions


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """选择用户登录 - 返回 JWT Token"""
    username = request.data.get('username')
    if not username:
        return Response({'code': 400, 'message': '请提供用户名'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username)
    if not user:
        return Response({'code': 404, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    # 生成 JWT
    refresh = RefreshToken.for_user(user)
    # 获取用户权限
    perms = get_user_effective_permissions(user)

    return Response({
        'code': 200,
        'data': {
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'permissions': perms,
        }
    })


@api_view(['POST'])
def logout(request):
    return Response({'code': 200, 'message': '已退出'})


@api_view(['GET'])
def me(request):
    """获取当前用户信息及权限"""
    user = request.user
    perms = get_user_effective_permissions(user)
    return Response({
        'code': 200,
        'data': {
            'user': UserSerializer(user).data,
            'permissions': perms,
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    """用户列表（登录选择用）"""
    users = User.objects.filter(is_active=True)
    serializer = UserListSerializer(users, many=True)
    return Response({'code': 200, 'data': serializer.data})


@api_view(['GET'])
def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return Response({'code': 200, 'data': UserSerializer(user).data})
    except User.DoesNotExist:
        return Response({'code': 404, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def user_permissions(request, user_id):
    """查看某个用户的全部权限"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'code': 404, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    perms = get_user_effective_permissions(user)
    return Response({'code': 200, 'data': perms})


@api_view(['GET'])
def dashboard_stats(request):
    """仪表盘统计数据"""
    from apps.releases.models import Release
    from apps.approvals.models import Approval
    from django.utils import timezone
    from django.db.models import Count

    total = Release.objects.count()
    today = Release.objects.filter(created_at__date=timezone.now().date()).count()
    success = Release.objects.filter(status='completed').count()
    failed = Release.objects.filter(status='failed').count()
    pending = Approval.objects.filter(action='pending', approver=request.user).count()
    success_rate = round(success / total * 100, 1) if total > 0 else 0

    return Response({'code': 200, 'data': {
        'total_releases': total,
        'today_releases': today,
        'success_rate': success_rate,
        'pending_approvals': pending,
    }})


@api_view(['GET'])
def dashboard_recent_releases(request):
    """近期发布列表"""
    from apps.releases.models import Release
    from apps.releases.serializers import ReleaseSerializer
    qs = Release.objects.select_related('application', 'creator').order_by('-created_at')[:10]
    return Response({'code': 200, 'data': ReleaseSerializer(qs, many=True).data})


@api_view(['GET'])
def dashboard_pending_approvals(request):
    """我的待审批列表"""
    from apps.approvals.models import Approval
    from apps.approvals.serializers import ApprovalSerializer
    qs = Approval.objects.filter(action='pending', approver=request.user).select_related('approver', 'release')[:10]
    return Response({'code': 200, 'data': ApprovalSerializer(qs, many=True).data})