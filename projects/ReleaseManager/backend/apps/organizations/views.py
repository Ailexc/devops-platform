from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BusinessLine, Group
from .serializers import BusinessLineSerializer, GroupSerializer
from apps.authz.models import SubjectMembership
from apps.authz.serializers import SubjectMembershipSerializer
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


# ─── 组织树 ───────────────────────────────────────────────────

@api_view(['GET'])
def org_tree(request):
    """
    获取组织树（业务线→组→用户）
    
    全量展示不过滤，每个节点附加:
    - accessible: bool — 当前用户是否有权查看详情
    - available_actions: list — 当前用户可执行的操作列表
    """
    tree = []
    for bl in BusinessLine.objects.filter(status='active').select_related('leader').order_by('sort_order'):
        bl_node = {
            'id': bl.id,
            'type': 'business_line',
            'name': bl.name,
            'code': bl.code,
            'leader_id': bl.leader_id,
            'leader_name': bl.leader.display_name if bl.leader else None,
            'children': [],
        }
        for group in Group.objects.filter(business_line=bl, status='active').select_related('leader'):
            group_node = {
                'id': group.id,
                'type': 'group',
                'name': group.name,
                'code': group.code,
                'leader_id': group.leader_id,
                'leader_name': group.leader.display_name if group.leader else None,
                'children': [],
            }
            memberships = SubjectMembership.objects.filter(
                group=group
            ).select_related('user')
            for m in memberships:
                is_leader = (group.leader_id == m.user.id)
                group_node['children'].append({
                    'id': m.user.id,
                    'type': 'user',
                    'name': m.user.display_name,
                    'code': m.user.username,
                    'membership_type': m.membership_type,
                    'membership_id': m.id,
                    'is_leader': is_leader,
                })
            bl_node['children'].append(group_node)
        tree.append(bl_node)

    # 使用 ABAC-Lite 注解组织树（全量展示，附加 accessible + available_actions）
    from apps.authz.access_control import annotate_org_tree
    annotated = annotate_org_tree(request.user, tree)
    return Response({'code': 200, 'data': annotated})


# ─── 业务线 ───────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def business_line_list(request):
    if request.method == 'GET':
        qs = BusinessLine.objects.all().order_by('sort_order')
        return Response({'code': 200, 'data': BusinessLineSerializer(qs, many=True).data})
    serializer = BusinessLineSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def business_line_detail(request, bl_id):
    from apps.authz.access_control import check_user_can
    if not check_user_can(request.user, 'business_line', bl_id, 'manage'):
        return Response({'code': 403, 'message': '您没有权限管理此业务线'}, status=status.HTTP_403_FORBIDDEN)

    try:
        bl = BusinessLine.objects.get(id=bl_id)
    except BusinessLine.DoesNotExist:
        return Response({'code': 404, 'message': '业务线不存在'}, status=status.HTTP_404_NOT_FOUND)
    serializer = BusinessLineSerializer(bl, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ─── 组 ───────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def group_list(request):
    if request.method == 'GET':
        qs = Group.objects.select_related('business_line').all()
        return Response({'code': 200, 'data': GroupSerializer(qs, many=True).data})
    serializer = GroupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def group_detail(request, group_id):
    # ── PEP 守卫 ──
    if not _can_manage_group(request.user, group_id):
        return Response({'code': 403, 'message': '您没有权限管理此组'}, status=status.HTTP_403_FORBIDDEN)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({'code': 404, 'message': '组不存在'}, status=status.HTTP_404_NOT_FOUND)
    serializer = GroupSerializer(group, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ─── 组成员管理 ───────────────────────────────────────────────

@api_view(['POST'])
def add_member(request, group_id):
    """添加成员"""
    # ── PEP 守卫 ──
    if not _can_manage_group(request.user, group_id):
        return Response({'code': 403, 'message': '您没有权限管理此组'}, status=status.HTTP_403_FORBIDDEN)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({'code': 404, 'message': '组不存在'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.data.get('user_id')
    membership_type = request.data.get('membership_type', 'primary')
    resource_scope = request.data.get('resource_scope')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'code': 404, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    membership, created = SubjectMembership.objects.get_or_create(
        user=user, group=group,
        defaults={
            'membership_type': membership_type,
            'resource_scope': resource_scope,
            'created_by': request.user,
        }
    )
    if not created:
        membership.membership_type = membership_type
        membership.resource_scope = resource_scope
        membership.save()

    return Response({
        'code': 200,
        'data': SubjectMembershipSerializer(membership).data
    })


@api_view(['DELETE', 'PATCH'])
def member_detail(request, group_id, user_id):
    """成员详情操作：DELETE 移除，PATCH 修改"""
    # ── PEP 守卫 ──
    if not _can_manage_group(request.user, group_id):
        return Response({'code': 403, 'message': '您没有权限管理此组'}, status=status.HTTP_403_FORBIDDEN)

    try:
        membership = SubjectMembership.objects.get(group_id=group_id, user_id=user_id)
    except SubjectMembership.DoesNotExist:
        return Response({'code': 404, 'message': '成员关系不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        membership.delete()
        return Response({'code': 200, 'message': '已移除成员'})

    # PATCH
    membership_type = request.data.get('membership_type')
    resource_scope = request.data.get('resource_scope')
    if membership_type:
        membership.membership_type = membership_type
    if resource_scope is not None:
        membership.resource_scope = resource_scope
    membership.save()

    return Response({
        'code': 200,
        'data': SubjectMembershipSerializer(membership).data
    })


# ── 辅助函数 ──────────────────────────────────────────────────

def _can_manage_group(user, group_id):
    """用户是否有权管理指定组（PEP 守卫辅助）"""
    from apps.authz.access_control import check_user_can
    return check_user_can(user, 'group', group_id, 'manage')