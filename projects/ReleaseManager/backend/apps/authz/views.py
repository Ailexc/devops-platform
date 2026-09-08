from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Role, RoleDataRule, SubjectMembership,
    EffectivePermissionCache, PermissionRequest, EnvironmentApprovalConfig,
    ApprovalFlowTemplate, AppChangeApprovalConfig, ReleaseApprovalConfig,
)
from .serializers import (
    RoleSerializer, RoleDataRuleSerializer,
    SubjectMembershipSerializer, PermissionRequestSerializer,
    EnvironmentApprovalConfigSerializer, ApprovalFlowTemplateSerializer,
    AppChangeApprovalConfigSerializer, ReleaseApprovalConfigSerializer,
)
from .utils import (
    get_user_permission_summary, get_group_permission_summary,
    check_permission_from_cache, rebuild_user_cache,
    resolve_approvers, find_business_line_leader,
)
from apps.accounts.models import User
from apps.organizations.models import Group, BusinessLine
from apps.approvals.models import Approval


# ═══════════════════════════════════════════════════════════════
# 角色管理
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def role_list(request):
    if request.method == 'GET':
        roles = Role.objects.all()
        return Response({'code': 200, 'data': RoleSerializer(roles, many=True).data})
    serializer = RoleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
def role_detail(request, role_id):
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return Response({'code': 404, 'message': '角色不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data})
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    if role.is_system:
        return Response({'code': 400, 'message': '系统内置角色不可删除'}, status=status.HTTP_400_BAD_REQUEST)
    role.delete()
    return Response({'code': 200, 'message': '已删除'})


# ═══════════════════════════════════════════════════════════════
# 数据权限规则
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def data_rule_list(request):
    if request.method == 'GET':
        qs = RoleDataRule.objects.select_related('role').all()
        return Response({'code': 200, 'data': RoleDataRuleSerializer(qs, many=True).data})
    serializer = RoleDataRuleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
def data_rule_detail(request, rule_id):
    try:
        rule = RoleDataRule.objects.get(id=rule_id)
    except RoleDataRule.DoesNotExist:
        return Response({'code': 404, 'message': '规则不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = RoleDataRuleSerializer(rule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data})
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    rule.delete()
    return Response({'code': 200, 'message': '已删除'})


# ═══════════════════════════════════════════════════════════════
# 用户权限
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
def my_permissions(request):
    """我的权限页面 - 展示用户的数据权限详情"""
    summary = get_user_permission_summary(request.user)
    return Response({'code': 200, 'data': summary})


@api_view(['GET'])
def user_permissions_detail(request, user_id):
    """查看指定用户的权限详情

    注意: 可见性已在树层面通过 accessible 控制，
    此处仅做基本的用户存在性检查，不做额外权限守卫。
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'code': 404, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    summary = get_user_permission_summary(user)
    return Response({'code': 200, 'data': summary})


# ═══════════════════════════════════════════════════════════════
# 组权限
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
def group_permissions_detail(request, group_id):
    """查看指定组的权限详情"""
    # ── PEP 守卫 ──
    from apps.authz.access_control import check_user_can
    if not check_user_can(request.user, 'group', group_id, 'view'):
        return Response({'code': 403, 'message': '您没有权限查看此组'}, status=status.HTTP_403_FORBIDDEN)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({'code': 404, 'message': '组不存在'}, status=status.HTTP_404_NOT_FOUND)

    summary = get_group_permission_summary(group)
    return Response({'code': 200, 'data': summary})


# ═══════════════════════════════════════════════════════════════
# 权限申请
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def permission_request_list(request):
    if request.method == 'GET':
        qs = PermissionRequest.objects.select_related('user').all().order_by('-created_at')
        return Response({'code': 200, 'data': PermissionRequestSerializer(qs, many=True).data})

    # POST: 创建权限申请
    data = request.data.copy()
    data['user'] = request.user.id
    serializer = PermissionRequestSerializer(data=data)
    if serializer.is_valid():
        perm_req = serializer.save()

        # 自动计算并填充受益人
        _fill_beneficiaries(perm_req)

        # 自动创建审批记录（按审批流步骤）
        _create_approvals_for_permission_request(perm_req)

        return Response({'code': 200, 'data': PermissionRequestSerializer(perm_req).data, 'message': '申请已提交'})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def my_perm_requests(request):
    """我的权限申请列表"""
    qs = PermissionRequest.objects.filter(user=request.user).order_by('-created_at')
    return Response({'code': 200, 'data': PermissionRequestSerializer(qs, many=True).data})


@api_view(['GET'])
def related_perm_requests(request):
    """与我相关的权限申请（我是受益人）"""
    user = request.user
    user_group_ids = set(user.memberships.values_list('group_id', flat=True))
    # SQLite 不支持 JSONField 的 __contains 查询，使用 Python 内存过滤
    all_requests = PermissionRequest.objects.all().order_by('-created_at')
    filtered = []
    for req in all_requests:
        beneficiary_user_ids = req.beneficiary_user_ids or []
        beneficiary_group_ids = req.beneficiary_group_ids or []
        if user.id in beneficiary_user_ids or user_group_ids & set(beneficiary_group_ids):
            filtered.append(req)
    return Response({'code': 200, 'data': PermissionRequestSerializer(filtered, many=True).data})


@api_view(['POST'])
def approve_permission_request(request, request_id):
    """审批权限申请 - 兼容旧接口，实际由审批中心步骤级审批处理"""
    try:
        perm_req = PermissionRequest.objects.get(id=request_id)
    except PermissionRequest.DoesNotExist:
        return Response({'code': 404, 'message': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')
    if action == 'approve':
        # 统一调用 apply_permission_request 处理分享/申请/回收/解除等全部类型
        apply_permission_request(perm_req)

        # 更新所有关联的审批记录
        Approval.objects.filter(permission_request=perm_req).update(action='approved')

        return Response({'code': 200, 'message': '审批通过，权限已生效'})

    elif action == 'reject':
        perm_req.status = 'rejected'
        perm_req.save()
        Approval.objects.filter(permission_request=perm_req).update(action='rejected')
        return Response({'code': 200, 'message': '已拒绝'})

    return Response({'code': 400, 'message': '请指定 action: approve / reject'}, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════
# 审批流模板
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def flow_template_list(request):
    if request.method == 'GET':
        qs = ApprovalFlowTemplate.objects.all().order_by('id')
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return Response({'code': 200, 'data': ApprovalFlowTemplateSerializer(qs, many=True).data})

    # POST 拒绝：审批流模板为系统基线，不可动态创建
    return Response({
        'code': 403,
        'message': '审批流模板为系统基线配置，不可动态创建。如需修改请通过代码部署更新。',
        'error_code': 'SYSTEM_BASELINE',
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'PUT', 'DELETE'])
def flow_template_detail(request, template_id):
    try:
        template = ApprovalFlowTemplate.objects.get(id=template_id)
    except ApprovalFlowTemplate.DoesNotExist:
        return Response({'code': 404, 'message': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({'code': 200, 'data': ApprovalFlowTemplateSerializer(template).data})

    # PUT/DELETE 拒绝：系统基线，不可编辑/删除
    return Response({
        'code': 403,
        'message': '审批流模板为系统基线配置，不可修改或删除。如需修改请通过代码部署更新。',
        'error_code': 'SYSTEM_BASELINE',
    }, status=status.HTTP_403_FORBIDDEN)


# ═══════════════════════════════════════════════════════════════
# 审批配置
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def approval_config_list(request):
    if request.method == 'GET':
        qs = EnvironmentApprovalConfig.objects.select_related('flow_template').all()
        return Response({'code': 200, 'data': EnvironmentApprovalConfigSerializer(qs, many=True).data})

    # POST 拒绝：审批策略为系统基线，不可动态创建
    return Response({
        'code': 403,
        'message': '审批策略为系统基线配置，不可动态创建。如需修改请通过代码部署更新。',
        'error_code': 'SYSTEM_BASELINE',
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['PUT'])
def approval_config_detail(request, config_id):
    # PUT 拒绝：审批策略为系统基线，不可编辑
    return Response({
        'code': 403,
        'message': '审批策略为系统基线配置，不可修改。如需修改请通过代码部署更新。',
        'error_code': 'SYSTEM_BASELINE',
    }, status=status.HTTP_403_FORBIDDEN)


# ═══════════════════════════════════════════════════════════════
# 审批流计算
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
def calculate_approval_flow(request):
    """
    根据应用、环境类型、授权范围，动态计算审批流。
    请求: { app_id, env_type, grant_scope }
    响应: { requires_approval, steps, flow_template_name }
    """
    app_id = request.data.get('app_id')
    env_type = request.data.get('env_type')
    grant_scope = request.data.get('grant_scope', 'own_group')

    if not app_id or not env_type:
        return Response({'code': 400, 'message': '请提供 app_id 和 env_type'}, status=status.HTTP_400_BAD_REQUEST)

    # 查找审批策略
    config = EnvironmentApprovalConfig.objects.filter(
        env_type=env_type, grant_scope=grant_scope, is_active=True,
    ).select_related('flow_template').first()

    if not config or not config.requires_approval or not config.flow_template:
        return Response({'code': 200, 'data': {
            'requires_approval': False,
            'steps': [],
            'flow_template_name': None,
            'message': '该环境类型不需要审批',
        }})

    template = config.flow_template
    steps = []
    total_approvers = 0

    for step_def in template.steps:
        approver_names = resolve_approvers(
            request.user, app_id, step_def.get('approver_resolver', ''),
            step_def.get('resolver_config', {}),
        )
        steps.append({
            'order': step_def.get('order', 0),
            'name': step_def.get('name', ''),
            'dimension': step_def.get('dimension', ''),
            'approver_resolver': step_def.get('approver_resolver', ''),
            'approvers': [{'id': u.id, 'name': u.display_name} for u in approver_names],
            'required_count': step_def.get('required_count', 1),
            'timeout_hours': step_def.get('timeout_hours', 24),
        })
        total_approvers += len(approver_names)

    # 估算耗时
    estimated_days = sum(s.get('timeout_hours', 24) for s in template.steps) / 24

    return Response({'code': 200, 'data': {
        'requires_approval': True,
        'flow_template_id': template.id,
        'flow_template_name': template.name,
        'steps': steps,
        'total_approvers': total_approvers,
        'total_steps': len(steps),
        'estimated_time': f'{estimated_days:.1f} 个工作日',
    }})


# ═══════════════════════════════════════════════════════════════
# 业务线负责人查询
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
def business_line_leader(request):
    """查询当前用户的业务线负责人"""
    leader = find_business_line_leader(request.user)
    from apps.organizations.serializers import BusinessLineSerializer

    # 获取用户所在业务线
    primary_membership = request.user.memberships.filter(membership_type='primary').first()
    business_line = None
    if primary_membership:
        business_line = primary_membership.group.business_line

    return Response({'code': 200, 'data': {
        'leader': {'id': leader.id, 'name': leader.display_name} if leader else None,
        'business_line': BusinessLineSerializer(business_line).data if business_line else None,
        'all_business_lines': BusinessLineSerializer(
            BusinessLine.objects.filter(status='active'), many=True
        ).data,
    }})


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _create_approvals_for_permission_request(perm_req):
    """根据审批策略为权限申请创建审批记录"""
    config = EnvironmentApprovalConfig.objects.filter(
        env_type=perm_req.env_type,
        grant_scope=perm_req.grant_scope,
        is_active=True,
    ).select_related('flow_template').first()

    if not config or not config.requires_approval or not config.flow_template:
        return

    template = config.flow_template
    total_steps = len(template.steps)

    for step_def in template.steps:
        approver_names = resolve_approvers(
            perm_req.user, perm_req.app_id,
            step_def.get('approver_resolver', ''),
            step_def.get('resolver_config', {}),
        )
        for approver in approver_names:
            Approval.objects.create(
                approval_type='permission',
                permission_request=perm_req,
                approver=approver,
                action='pending',
                step_order=step_def.get('order', 1),
                step_name=step_def.get('name', ''),
                total_steps=total_steps,
            )


def _fill_beneficiaries(perm_req):
    """根据申请类型和扩展数据计算受益人"""
    extra = perm_req.extra_data or {}
    request_type = perm_req.request_type

    user_ids = []
    group_ids = []

    if request_type in ('apply', 'share'):
        target_group_id = extra.get('target_group_id')
        target_user_ids = extra.get('target_user_ids', [])

        if target_group_id:
            group_ids.append(target_group_id)
            user_ids.extend(
                SubjectMembership.objects.filter(
                    group_id=target_group_id, membership_type='primary'
                ).values_list('user_id', flat=True)
            )
        if target_user_ids:
            user_ids.extend(target_user_ids)

        # 默认：申请人/分享人自己受益
        if not group_ids and not user_ids:
            user_ids.append(perm_req.user_id)

    elif request_type in ('revoke', 'release'):
        rule_ids = extra.get('rule_ids', [])
        if rule_ids:
            rules = RoleDataRule.objects.filter(id__in=rule_ids).select_related('role')
            for rule in rules:
                if rule.role.owner_type == 'user':
                    user = User.objects.filter(role_id=rule.role_id).first()
                    if user:
                        user_ids.append(user.id)
                else:
                    group = Group.objects.filter(role_id=rule.role_id).first()
                    if group:
                        group_ids.append(group.id)
                        user_ids.extend(
                            SubjectMembership.objects.filter(
                                group_id=group.id, membership_type='primary'
                            ).values_list('user_id', flat=True)
                        )

    perm_req.beneficiary_user_ids = list(set(user_ids))
    perm_req.beneficiary_group_ids = list(set(group_ids))
    perm_req.save(update_fields=['beneficiary_user_ids', 'beneficiary_group_ids'])


# ═══════════════════════════════════════════════════════════════
# 鉴权检查
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
def check_permission(request):
    """鉴权检查接口（供前端调用）"""
    app_id = request.data.get('app_id')
    env_id = request.data.get('env_id')

    if not app_id or not env_id:
        return Response({'code': 400, 'message': '请提供 app_id 和 env_id'}, status=status.HTTP_400_BAD_REQUEST)

    allowed = check_permission_from_cache(request.user.id, app_id, env_id)
    return Response({'code': 200, 'data': {'allowed': allowed}})


# ═══════════════════════════════════════════════════════════════
# ABAC-Lite 鉴权查询
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
def access_check(request):
    """
    ABAC-Lite 单次鉴权查询

    请求:
    {
        "type": "group",
        "id": 3,
        "action": "manage"
    }

    响应:
    {
        "code": 200,
        "data": { "allowed": true }
    }
    """
    from apps.authz.access_control import check_user_can

    resource_type = request.data.get('type')
    resource_id = request.data.get('id')
    action = request.data.get('action')

    if not all([resource_type, resource_id, action]):
        return Response({
            'code': 400, 'message': '请提供 type, id, action'
        }, status=status.HTTP_400_BAD_REQUEST)

    allowed = check_user_can(request.user, resource_type, resource_id, action)
    return Response({'code': 200, 'data': {'allowed': allowed}})


@api_view(['POST'])
def access_check_batch(request):
    """
    ABAC-Lite 批量鉴权查询

    请求:
    {
        "checks": [
            {"type": "group", "id": 3, "action": "manage"},
            {"type": "group", "id": 3, "action": "share"}
        ]
    }

    响应:
    {
        "code": 200,
        "data": {
            "group:3:manage": true,
            "group:3:share": true
        }
    }
    """
    from apps.authz.access_control import check_user_can_batch

    checks = request.data.get('checks', [])
    if not checks:
        return Response({
            'code': 400, 'message': '请提供 checks 列表'
        }, status=status.HTTP_400_BAD_REQUEST)

    results = check_user_can_batch(request.user, checks)
    return Response({'code': 200, 'data': results})


# ═══════════════════════════════════════════════════════════════
# 权限调整详情
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
def permission_adjust_detail(request, group_id):
    """
    获取指定组在指定应用+环境类型下的权限调整详情。

    Query params: app_id, env_type
    返回：
    - 该环境类型的所有环境列表
    - 组内成员及其权限（每个成员允许的环境）
    - 组外个人权限（非本组成员通过个人申请获得的权限）
    - 协作组权限（已分享给其他组的权限）
    """
    # ── PEP 守卫 ──
    from apps.authz.access_control import check_user_can
    if not check_user_can(request.user, 'group', group_id, 'manage'):
        return Response({'code': 403, 'message': '您没有权限调整此组'}, status=status.HTTP_403_FORBIDDEN)
    from django.utils import timezone
    from apps.applications.models import Application
    from apps.organizations.models import Group as OrgGroup, BusinessLine
    from apps.infrastructures.models import Environment

    try:
        group = OrgGroup.objects.get(id=group_id)
    except OrgGroup.DoesNotExist:
        return Response({'code': 404, 'message': '组不存在'}, status=status.HTTP_404_NOT_FOUND)

    app_id = request.query_params.get('app_id')
    env_type = request.query_params.get('env_type')

    if not app_id or not env_type:
        return Response({'code': 400, 'message': '请提供 app_id 和 env_type'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        app_id = int(app_id)
    except (ValueError, TypeError):
        return Response({'code': 400, 'message': 'app_id 无效'}, status=status.HTTP_400_BAD_REQUEST)

    app = Application.objects.filter(id=app_id).first()
    if not app:
        return Response({'code': 404, 'message': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    env_type_labels = {'dev': '开发', 'test': '测试', 'staging': '预发', 'prod': '生产'}

    # 该环境类型的所有环境
    all_envs = list(Environment.objects.filter(env_type=env_type).values(
        'id', 'name', 'code', 'env_type', 'cloud_provider', 'account_id', 'region', 'zone'
    ))

    def _valid_rules(rules_qs):
        """过滤未过期的规则"""
        from django.db.models import Q
        return rules_qs.filter(Q(valid_to__isnull=True) | Q(valid_to__gt=now))

    def _get_env_ids_for_app(rules_qs):
        """从规则集合中提取该应用+环境类型允许的环境ID集合"""
        env_ids = set()
        for r in _valid_rules(rules_qs.filter(app_id=app_id, env_type=env_type)):
            if r.is_all_envs:
                env_ids.update(e['id'] for e in all_envs)
            env_ids.update(r.allow_env_ids or [])
        return env_ids

    # ─── 1. 组内成员权限 ───
    memberships = SubjectMembership.objects.filter(
        group=group
    ).select_related('user', 'user__role')

    members = []
    for m in memberships:
        user = m.user
        allowed_env_ids = set()

        # 团队规则权限
        if group.role:
            allowed_env_ids = _get_env_ids_for_app(
                RoleDataRule.objects.filter(role=group.role, grant_scope='own_group')
            )

        # 个人规则权限（叠加）
        if user.role:
            personal_ids = _get_env_ids_for_app(
                RoleDataRule.objects.filter(role=user.role)
            )
            allowed_env_ids.update(personal_ids)

        permission_source = 'team'
        if user.role:
            has_personal = _valid_rules(
                RoleDataRule.objects.filter(role=user.role, app_id=app_id, env_type=env_type)
            ).exists()
            if has_personal and allowed_env_ids != _get_env_ids_for_app(
                RoleDataRule.objects.filter(role=group.role, grant_scope='own_group')
            ) if group.role else True:
                permission_source = 'mixed'
            elif has_personal:
                permission_source = 'personal'

        allowed_list = sorted(allowed_env_ids)
        members.append({
            'user_id': user.id,
            'user_name': user.display_name,
            'username': user.username,
            'membership_type': m.membership_type,
            'is_leader': user.is_group_leader,
            'role_name': '组长' if user.is_group_leader else ('协作者' if m.membership_type == 'collaborator' else '开发者'),
            'allowed_env_ids': allowed_list,
            'allowed_env_names': [e['name'] for e in all_envs if e['id'] in allowed_list],
            'permission_source': permission_source,
        })

    # ─── 2. 组外个人权限 ───
    member_user_ids = set(m['user_id'] for m in members)
    external_users = []

    # 查找所有在 app_id+env_type 上有 cross_group 规则的用户
    cross_rules = _valid_rules(
        RoleDataRule.objects.filter(
            app_id=app_id, env_type=env_type, grant_scope='cross_group'
        )
    )

    seen_user_ids = set()
    for rule in cross_rules:
        if not rule.role:
            continue
        # 找到拥有该角色的用户
        users_with_role = User.objects.filter(role=rule.role).exclude(id__in=member_user_ids)
        for u in users_with_role:
            if u.id in seen_user_ids:
                continue
            seen_user_ids.add(u.id)

            allowed_ids = _get_env_ids_for_app(
                RoleDataRule.objects.filter(role=u.role)
            )

            # 找到用户所属组
            user_groups = u.memberships.select_related('group').all()
            source_group_name = user_groups[0].group.name if user_groups else '无归属组'

            allowed_list = sorted(allowed_ids)
            external_users.append({
                'user_id': u.id,
                'user_name': u.display_name,
                'username': u.username,
                'source_group_name': source_group_name,
                'allowed_env_ids': allowed_list,
                'allowed_env_names': [e['name'] for e in all_envs if e['id'] in allowed_list],
                'created_at': rule.created_at.strftime('%Y-%m-%d') if rule.created_at else '',
            })

    # ─── 3. 协作组权限 ───
    collab_rules = _valid_rules(
        RoleDataRule.objects.filter(
            app_id=app_id, env_type=env_type, grant_scope='cross_group',
            owner_group_id=group.id
        ).exclude(role=group.role)
    )

    collab_groups = []
    seen_group_ids = set()
    for rule in collab_rules:
        if not rule.role:
            continue
        # 找到拥有该角色的组
        groups_with_role = OrgGroup.objects.filter(role=rule.role)
        for g in groups_with_role:
            if g.id in seen_group_ids or g.id == group.id:
                continue
            seen_group_ids.add(g.id)

            allowed_ids = set()
            if rule.is_all_envs:
                allowed_ids.update(e['id'] for e in all_envs)
            allowed_ids.update(rule.allow_env_ids or [])

            allowed_list = sorted(allowed_ids)
            collab_groups.append({
                'group_id': g.id,
                'group_name': g.name,
                'group_code': g.code,
                'sharer_name': '组管理员',
                'allowed_env_ids': allowed_list,
                'allowed_env_names': [e['name'] for e in all_envs if e['id'] in allowed_list],
                'is_all_envs': rule.is_all_envs,
                'created_at': rule.created_at.strftime('%Y-%m-%d') if rule.created_at else '',
            })

    return Response({
        'code': 200,
        'data': {
            'app_id': app.id,
            'app_name': app.name,
            'app_code': app.code,
            'env_type': env_type,
            'env_type_label': env_type_labels.get(env_type, env_type),
            'all_envs': all_envs,
            'members': members,
            'external_users': external_users,
            'collab_groups': collab_groups,
        }
    })


@api_view(['POST'])
def permission_adjust_submit(request, group_id):
    """
    提交权限调整申请。

    请求体:
    {
        app_id: int,
        env_type: str,
        reason: str,
        adjustments: {
            member_changes: [ ... ],
            external_changes: [ ... ],
            collab_changes: [ ... ]
        }
    }
    """
    # ── PEP 守卫 ──
    from apps.authz.access_control import check_user_can
    if not check_user_can(request.user, 'group', group_id, 'manage'):
        return Response({'code': 403, 'message': '您没有权限调整此组'}, status=status.HTTP_403_FORBIDDEN)

    from django.utils import timezone
    from apps.applications.models import Application
    from apps.organizations.models import Group as OrgGroup
    from apps.infrastructures.models import Environment

    try:
        group = OrgGroup.objects.get(id=group_id)
    except OrgGroup.DoesNotExist:
        return Response({'code': 404, 'message': '组不存在'}, status=status.HTTP_404_NOT_FOUND)

    app_id = request.data.get('app_id')
    env_type = request.data.get('env_type')
    reason = request.data.get('reason', '')
    adjustments = request.data.get('adjustments', {})

    if not app_id or not env_type:
        return Response({'code': 400, 'message': '请提供 app_id 和 env_type'}, status=status.HTTP_400_BAD_REQUEST)

    app = Application.objects.filter(id=app_id).first()
    if not app:
        return Response({'code': 404, 'message': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)

    member_changes = adjustments.get('member_changes', [])
    external_changes = adjustments.get('external_changes', [])
    collab_changes = adjustments.get('collab_changes', [])

    all_changes = member_changes + external_changes + collab_changes
    if not all_changes:
        return Response({'code': 400, 'message': '没有变更内容'}, status=status.HTTP_400_BAD_REQUEST)

    # 检查是否有实际变更
    has_change = False
    for c in all_changes:
        if c.get('add_env_ids') or c.get('remove_env_ids'):
            has_change = True
            break
    if not has_change:
        return Response({'code': 400, 'message': '没有实际的权限变更'}, status=status.HTTP_400_BAD_REQUEST)

    all_env_ids = set()
    for c in all_changes:
        all_env_ids.update(c.get('add_env_ids', []))
        all_env_ids.update(c.get('remove_env_ids', []))

    # 创建权限申请
    perm_req = PermissionRequest.objects.create(
        user=request.user,
        request_type='apply',
        app_id=app_id,
        env_type=env_type,
        is_all_envs=False,
        env_ids=list(all_env_ids),
        grant_scope='own_group',
        reason=reason,
        status='pending',
        extra_data={
            'group_id': group_id,
            'adjustments': adjustments,
            'member_changes': member_changes,
            'external_changes': external_changes,
            'collab_changes': collab_changes,
        },
    )

    _fill_beneficiaries(perm_req)
    _create_approvals_for_permission_request(perm_req)

    return Response({
        'code': 200,
        'data': PermissionRequestSerializer(perm_req).data,
        'message': '权限调整申请已提交',
    })


# ═══════════════════════════════════════════════════════════════
# 应用变更审批配置
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def app_change_approval_config_list(request):
    if request.method == 'GET':
        qs = AppChangeApprovalConfig.objects.select_related('flow_template').all()
        return Response({'code': 200, 'data': AppChangeApprovalConfigSerializer(qs, many=True).data})
    serializer = AppChangeApprovalConfigSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def app_change_approval_config_detail(request, config_id):
    try:
        config = AppChangeApprovalConfig.objects.get(id=config_id)
    except AppChangeApprovalConfig.DoesNotExist:
        return Response({'code': 404, 'message': '配置不存在'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        return Response({'code': 200, 'data': AppChangeApprovalConfigSerializer(config).data})
    if request.method == 'PUT':
        serializer = AppChangeApprovalConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data})
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    config.delete()
    return Response({'code': 200, 'message': '已删除'})


# ═══════════════════════════════════════════════════════════════
# 发布策略
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
def release_approval_config_list(request):
    if request.method == 'GET':
        qs = ReleaseApprovalConfig.objects.select_related('flow_template').all()
        return Response({'code': 200, 'data': ReleaseApprovalConfigSerializer(qs, many=True).data})
    serializer = ReleaseApprovalConfigSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 200, 'data': serializer.data})
    return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def release_approval_config_detail(request, config_id):
    try:
        config = ReleaseApprovalConfig.objects.get(id=config_id)
    except ReleaseApprovalConfig.DoesNotExist:
        return Response({'code': 404, 'message': '策略不存在'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        return Response({'code': 200, 'data': ReleaseApprovalConfigSerializer(config).data})
    if request.method == 'PUT':
        serializer = ReleaseApprovalConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'data': serializer.data})
        return Response({'code': 400, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    config.delete()
    return Response({'code': 200, 'message': '已删除'})