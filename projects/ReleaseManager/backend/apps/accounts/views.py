import os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import redirect

from .models import User
from .serializers import UserSerializer, UserListSerializer
from .oidc_client import (
    build_authorize_url,
    exchange_code,
    generate_pkce,
    generate_state,
    verify_id_token,
)
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
@permission_classes([AllowAny])
def oidc_login(request):
    """统一认证登录（OIDC 授权码）：302 跳转统一认证中心。"""
    verifier, challenge = generate_pkce()
    state = generate_state()
    request.session['oidc_verifier'] = verifier
    request.session['oidc_state'] = state
    return redirect(build_authorize_url(state, challenge))


@api_view(['GET'])
@permission_classes([AllowAny])
def oidc_callback(request):
    """OIDC 回调：换令牌 → 验签 id_token → 映射本地用户 → 签发本地 JWT。"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    if not code or state != request.session.get('oidc_state'):
        return Response({'code': 400, 'message': 'OIDC 回调校验失败（code/state 不合法）'},
                        status=status.HTTP_400_BAD_REQUEST)
    verifier = request.session.pop('oidc_verifier', None)
    try:
        tokens = exchange_code(code, verifier)
        id_token = tokens.get('id_token')
        if not id_token:
            return Response({'code': 400, 'message': '令牌响应缺少 id_token'}, status=400)
        claims = verify_id_token(id_token)
    except Exception as e:
        return Response({'code': 400, 'message': f'OIDC 登录失败：{e}'}, status=400)

    username = claims.get('uid') or claims.get('preferred_username') or claims.get('sub')
    if not username:
        return Response({'code': 400, 'message': 'id_token 缺少用户名'}, status=400)
    # 账号作用域收口：release_ 前缀账号 → 剥前缀映射本地（release_zhangsan→zhangsan）；
    # admin 为全局超管；本地未开通/不存在的账号 → 明确拒绝（授权由发布系统本地自治）
    local = 'admin' if username == 'admin' else (
        username[len('release_'):] if username.startswith('release_') else None
    )
    if local is None:
        return Response({'code': 403, 'message': f'该账号（{username}）未在发布系统开通'},
                        status=403)
    user = User.objects.filter(username=local, is_active=True).first()
    if user is None:
        return Response({'code': 403, 'message': f'该账号（{username}）未在发布系统开通'},
                        status=403)
    refresh = RefreshToken.for_user(user)
    # 标准 OIDC 授权码闭环：成功后 302 回前端 /login?token=<本地JWT>（SPA 读取后清理 URL，随后拉用户/权限）
    base = os.environ.get("APP_URL_RELEASE_MANAGER", "http://release.devops.orb.local").rstrip("/")
    return redirect(f"{base}/login?token={str(refresh.access_token)}")


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