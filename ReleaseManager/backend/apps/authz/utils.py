"""
权限计算核心模块

数据权限规则匹配：
  一条规则 = 一个应用 + 一个环境类型 + 该类型下的授权范围

优先级：
  User Deny > User Allow > Group Deny > Group Allow > Default Deny
"""
from django.db import transaction
from django.utils import timezone
from apps.authz.models import (
    Role, RoleDataRule, SubjectMembership, EffectivePermissionCache,
)
from apps.accounts.models import User
from apps.infrastructures.models import Environment, CLOUD_PROVIDERS

ENV_TYPE_LABELS = {
    'dev': '开发',
    'test': '测试',
    'staging': '预发',
    'prod': '生产',
}


# ─── 规则匹配 ───────────────────────────────────────────────

def rule_matches_target(rule: RoleDataRule, target_app_id: int, target_env_id: int,
                        target_env_type: str, now=None) -> tuple:
    """
    检查单条 RoleDataRule 是否匹配目标环境。

    返回: ('allow', rule) | ('deny', rule) | None
    """
    if now is None:
        now = timezone.now()

    # 1. 应用必须匹配
    if rule.app_id != target_app_id:
        return None

    # 2. 环境类型必须匹配
    if rule.env_type != target_env_type:
        return None

    # 3. 时间范围检查
    if rule.valid_from and now < rule.valid_from:
        return None
    if rule.valid_to and now > rule.valid_to:
        return None

    # 4. deny 优先
    if target_env_id in (rule.deny_env_ids or []):
        return ('deny', rule)

    # 5. 全环境授权
    if rule.is_all_envs:
        return ('allow', rule)

    # 6. 精确环境授权
    if target_env_id in (rule.allow_env_ids or []):
        return ('allow', rule)

    return None


# ─── 用户数据权限判定 ────────────────────────────────────────

# ─── 用户可访问应用/环境查询 ──────────────────────────────────


def get_user_accessible_app_ids(user: User) -> list:
    """
    从 EffectivePermissionCache 获取用户有权限访问的应用 ID 列表。
    审计管理员返回全部应用。
    """
    if getattr(user, 'is_audit_admin', False):
        from apps.applications.models import Application
        return list(Application.objects.values_list('id', flat=True))

    app_ids = list(
        EffectivePermissionCache.objects.filter(
            user_id=user.id, effect='allow'
        ).values_list('app_id', flat=True).distinct()
    )
    return app_ids


def get_user_accessible_env_ids_for_app(user: User, app_id: int) -> list:
    """
    从 EffectivePermissionCache 获取用户在某个应用下可访问的环境 ID 列表。
    """
    env_ids = list(
        EffectivePermissionCache.objects.filter(
            user_id=user.id, app_id=app_id, effect='allow'
        ).values_list('env_id', flat=True).distinct()
    )
    return env_ids


def has_data_permission(user: User, target_app_id: int, target_env_id: int,
                        target_env_type: str) -> bool:
    """
    判断用户是否有目标应用环境的操作权限。

    优先级: User Deny > User Allow > Group Deny > Group Allow > Default Deny
    """
    now = timezone.now()

    # 1. 加载 User Role 规则
    user_rules = []
    if user.role:
        user_rules = list(RoleDataRule.objects.filter(role=user.role))

    # 2. 加载 Group Role 规则
    group_rules = []
    memberships = SubjectMembership.objects.filter(user=user).select_related('group__role')
    for m in memberships:
        if m.group.role:
            group_rules.extend(list(RoleDataRule.objects.filter(role=m.group.role)))

    # 3. 按优先级检查
    for rule in user_rules:
        result = rule_matches_target(rule, target_app_id, target_env_id, target_env_type, now)
        if result == ('deny', rule):
            return False
        if result == ('allow', rule):
            return True

    for rule in group_rules:
        result = rule_matches_target(rule, target_app_id, target_env_id, target_env_type, now)
        if result == ('deny', rule):
            return False
        if result == ('allow', rule):
            return True

    return False


def can(user: User, env_id: int) -> bool:
    """
    高频鉴权入口：判断用户是否有权操作某个环境。

    安全原则：
      - 不信任前端传入的 app_id；
      - 后端根据 env_id 查询真实应用、环境类型；
      - 默认拒绝。
    """
    try:
        env = Environment.objects.get(id=env_id)
    except Environment.DoesNotExist:
        return False

    # 通过 AppEnvConfig 找到环境对应的应用
    from apps.applications.models import AppEnvConfig
    config = AppEnvConfig.objects.filter(environment_id=env_id).select_related('application').first()
    if not config:
        return False

    return has_data_permission(user, config.application_id, env_id, env.env_type)


# ─── 有效权限缓存 ────────────────────────────────────────────

def rebuild_user_cache(user: User):
    """
    重算单个用户的有效权限缓存。

    以规则为驱动，逐条规则展开其覆盖的环境，按优先级合并到缓存中。
    事务保证原子性：DELETE + INSERT 在同一个事务中完成。
    """
    from apps.applications.models import AppEnvConfig

    now = timezone.now()

    with transaction.atomic():
        # 清除旧缓存
        EffectivePermissionCache.objects.filter(user_id=user.id).delete()

        # 收集 User Role 规则
        user_rules = []
        if user.role:
            user_rules = list(RoleDataRule.objects.filter(role=user.role))

        # 收集 Group Role 规则
        group_rules = []
        memberships = SubjectMembership.objects.filter(user=user).select_related('group__role')
        for m in memberships:
            if m.group.role:
                group_rules.extend(list(RoleDataRule.objects.filter(role=m.group.role)))

        # 以 (app_id, env_id) 为键逐条规则展开，优先级: User > Group
        # 使用 dict 去重，后写入的 Group 规则不会覆盖已写入的 User 规则
        cache_map = {}  # key: (app_id, env_id) → EffectivePermissionCache

        def expand_rules(rules, is_user_rules):
            for rule in rules:
                # 收集该规则覆盖的所有环境
                env_ids_to_check = set()
                if rule.allow_env_ids:
                    env_ids_to_check.update(rule.allow_env_ids)
                if rule.deny_env_ids:
                    env_ids_to_check.update(rule.deny_env_ids)
                if rule.is_all_envs:
                    configs = AppEnvConfig.objects.filter(
                        application_id=rule.app_id,
                        environment__env_type=rule.env_type,
                    ).values_list('environment_id', flat=True)
                    env_ids_to_check.update(configs)

                for env_id in env_ids_to_check:
                    result = rule_matches_target(rule, rule.app_id, env_id, rule.env_type, now)
                    if not result:
                        continue
                    effect, _ = result
                    key = (rule.app_id, env_id)
                    if key not in cache_map or is_user_rules:
                        cache_map[key] = EffectivePermissionCache(
                            user_id=user.id,
                            app_id=rule.app_id,
                            env_id=env_id,
                            effect=effect,
                            source_role_id=rule.role_id,
                            source_rule_id=rule.id,
                            valid_to=rule.valid_to,
                        )

        # 先展开 Group 规则，再展开 User 规则（User 会覆盖 Group 对同一 key 的结果）
        expand_rules(group_rules, is_user_rules=False)
        expand_rules(user_rules, is_user_rules=True)

        if cache_map:
            EffectivePermissionCache.objects.bulk_create(cache_map.values())


def rebuild_group_cache(group):
    """重算组下所有成员的有效权限缓存"""
    member_ids = SubjectMembership.objects.filter(
        group=group
    ).values_list('user_id', flat=True)
    for uid in member_ids:
        try:
            user = User.objects.get(id=uid)
            rebuild_user_cache(user)
        except User.DoesNotExist:
            pass


def check_permission_from_cache(user_id: int, app_id: int, env_id: int) -> bool:
    """
    从缓存中快速鉴权（高频调用路径）。

    返回: True 表示允许，False 表示拒绝。
    """
    # 先查 deny
    if EffectivePermissionCache.objects.filter(
        user_id=user_id, app_id=app_id, env_id=env_id, effect='deny',
    ).exists():
        return False

    # 再查 allow
    if EffectivePermissionCache.objects.filter(
        user_id=user_id, app_id=app_id, env_id=env_id, effect='allow',
    ).exists():
        return True

    return False


# ─── 权限展示工具 ────────────────────────────────────────────

def get_user_permission_summary(user: User) -> dict:
    """
    获取用户权限摘要（用于"我的权限"页面展示）。

    返回结构:
    {
        user_id, user_name,
        groups: [{group_id, group_name, membership_type}],
        own_group_apps: [AppPermissionDetail],   # 归属组负责的应用
        cross_group_apps: [AppPermissionDetail], # 非归属组负责的应用（协作/借调）
    }

    区分逻辑:
    - 归属组：用户 membership_type='primary' 的组
    - 组内权限：应用 owner_group_id 属于归属组的应用
    - 协作权限：应用 owner_group_id 不属于归属组的应用
    - 权限属性：
        * group: 仅由组规则授权
        * personal: 存在用户个人规则覆盖/补充
        * cross: 协作权限
    """
    from apps.applications.models import Application
    from apps.organizations.models import BusinessLine, Group as OrgGroup

    now = timezone.now()

    # 1. 组成员关系
    memberships = SubjectMembership.objects.filter(user=user).select_related('group')
    primary_group_ids = set(m.group_id for m in memberships if m.membership_type == 'primary')
    groups = [
        {
            'group_id': m.group_id,
            'group_name': m.group.name,
            'membership_type': m.membership_type,
        }
        for m in memberships
    ]

    # 2. 收集所有规则（带来源标记），过滤已过期规则
    # 结构: [(rule, source, group_id), ...]
    # source: 'group' | 'user'
    all_rules = []

    def _is_rule_active(rule):
        return rule.valid_to is None or rule.valid_to > now

    # 组规则
    for m in memberships.select_related('group__role'):
        if m.group.role:
            for rule in RoleDataRule.objects.filter(role=m.group.role):
                if _is_rule_active(rule):
                    all_rules.append((rule, 'group', m.group_id))

    # 用户规则
    if user.role:
        for rule in RoleDataRule.objects.filter(role=user.role):
            if _is_rule_active(rule):
                all_rules.append((rule, 'user', None))

    # 3. 预加载应用、环境元数据
    app_ids = list(set(r.app_id for r, _, _ in all_rules))
    apps = Application.objects.in_bulk(app_ids)
    business_lines = BusinessLine.objects.in_bulk(set(a.business_line_id for a in apps.values()))
    owner_groups = OrgGroup.objects.in_bulk(set(a.owner_id for a in apps.values() if hasattr(a, 'owner_id') and a.owner_id))

    # 4. 按应用分组计算权限
    app_rule_map = {}  # app_id -> [(rule, source, group_id), ...]
    for rule, source, group_id in all_rules:
        app_rule_map.setdefault(rule.app_id, []).append((rule, source, group_id))

    own_group_apps = []
    cross_group_apps = []

    for app_id, rules in app_rule_map.items():
        app = apps.get(app_id)
        if not app:
            continue

        # 判断是组内还是协作
        # 从规则中推断应用的承接组 owner_group_id
        owner_group_id = None
        for r, _, _ in rules:
            if r.owner_group_id:
                owner_group_id = r.owner_group_id
                break

        is_own_group = owner_group_id and owner_group_id in primary_group_ids

        app_detail = {
            'app_id': app_id,
            'app_name': app.name,
            'app_code': app.code,
            'business_line_id': app.business_line_id,
            'business_line_name': business_lines.get(app.business_line_id, BusinessLine(name='未知')).name,
            'owner_group_id': owner_group_id,
            'owner_group_name': owner_groups.get(owner_group_id, OrgGroup(name='未知')).name if owner_group_id else '未知',
            'env_permissions': _build_env_permissions(app_id, rules, is_own_group, now),
        }

        if is_own_group:
            own_group_apps.append(app_detail)
        else:
            cross_group_apps.append(app_detail)

    return {
        'user_id': user.id,
        'user_name': user.display_name,
        'groups': groups,
        'own_group_apps': own_group_apps,
        'cross_group_apps': cross_group_apps,
    }


def _build_env_permissions(app_id: int, rules: list, is_own_group: bool, now) -> list:
    """
    构建某个应用下的环境类型维度权限详情。

    rules: [(RoleDataRule, source, group_id), ...]
    source: 'group' | 'user'
    """
    from apps.applications.models import Application, AppEnvConfig
    from apps.infrastructures.models import Environment

    # 获取该应用下所有环境
    app_env_configs = AppEnvConfig.objects.filter(
        application_id=app_id
    ).select_related('environment')

    # 按环境类型分组
    envs_by_type = {}
    for cfg in app_env_configs:
        env = cfg.environment
        envs_by_type.setdefault(env.env_type, []).append({
            'id': env.id,
            'name': env.name,
            'code': env.code,
            'cloud_provider': env.cloud_provider or '',
            'cloud_provider_label': dict(CLOUD_PROVIDERS).get(env.cloud_provider, env.cloud_provider or ''),
            'account_id': env.account_id or '',
            'region': env.region or '',
            'zone': env.zone or '',
            'network_type': env.network_type or '',
        })

    # 按环境类型聚合规则
    rules_by_env_type = {}
    for rule, source, group_id in rules:
        rules_by_env_type.setdefault(rule.env_type, []).append((rule, source, group_id))

    result = []
    all_env_types = set(list(envs_by_type.keys()) + list(rules_by_env_type.keys()))

    for env_type in sorted(all_env_types, key=lambda x: ['dev', 'test', 'staging', 'prod'].index(x) if x in ['dev', 'test', 'staging', 'prod'] else 99):
        envs = envs_by_type.get(env_type, [])
        env_rules = rules_by_env_type.get(env_type, [])

        allowed_env_ids = set()
        denied_env_ids = set()
        # 记录每个被允许环境的最终权限来源: 'group' | 'user'
        env_source_map = {}

        # 按优先级计算每个环境的最终权限
        # 规则优先级: user deny > user allow > group deny > group allow
        for env in envs:
            env_id = env['id']
            user_deny = False
            user_allow = False
            group_deny = False
            group_allow = False

            for rule, source, group_id in env_rules:
                # 时间检查
                if rule.valid_from and now < rule.valid_from:
                    continue
                if rule.valid_to and now > rule.valid_to:
                    continue

                if source == 'user':
                    if env_id in (rule.deny_env_ids or []):
                        user_deny = True
                    elif rule.is_all_envs or env_id in (rule.allow_env_ids or []):
                        user_allow = True
                else:
                    if env_id in (rule.deny_env_ids or []):
                        group_deny = True
                    elif rule.is_all_envs or env_id in (rule.allow_env_ids or []):
                        group_allow = True

            if user_deny:
                denied_env_ids.add(env_id)
            elif user_allow:
                allowed_env_ids.add(env_id)
                env_source_map[env_id] = 'user'
            elif group_deny:
                denied_env_ids.add(env_id)
            elif group_allow:
                allowed_env_ids.add(env_id)
                env_source_map[env_id] = 'group'

        # 确定权限属性
        if is_own_group:
            if not allowed_env_ids:
                permission_source = 'group'
            else:
                sources = {env_source_map.get(eid) for eid in allowed_env_ids}
                if sources == {'group'}:
                    permission_source = 'group'
                elif sources == {'user'}:
                    permission_source = 'personal'
                else:
                    permission_source = 'mixed'
        else:
            permission_source = 'cross'

        # 授权范围
        all_env_ids = set(e['id'] for e in envs)
        if not envs:
            scope = 'none'
        elif allowed_env_ids >= all_env_ids and not denied_env_ids:
            scope = 'all'
        elif allowed_env_ids:
            scope = 'partial'
        else:
            scope = 'none'

        env_name_map = {e['id']: e for e in envs}
        allowed_envs = sorted([env_name_map[eid] for eid in allowed_env_ids], key=lambda x: x['id'])
        unauthorized_envs = sorted([env_name_map[eid] for eid in (all_env_ids - allowed_env_ids)], key=lambda x: x['id'])
        denied_envs = sorted([env_name_map[eid] for eid in denied_env_ids], key=lambda x: x['id'])

        result.append({
            'env_type': env_type,
            'env_type_label': ENV_TYPE_LABELS.get(env_type, env_type),
            'scope': scope,
            'allowed_envs': allowed_envs,
            'unauthorized_envs': unauthorized_envs,
            'denied_envs': denied_envs,
            'permission_source': permission_source,
            'permission_source_label': {
                'group': '团队权限（完全继承）',
                'personal': '个人权限',
                'mixed': '混合权限',
                'cross': '协作权限',
            }.get(permission_source, permission_source),
            'has_envs': len(envs) > 0,
        })

    return result


def get_group_permission_summary(group) -> dict:
    """
    获取组权限摘要（用于"组织权限"页面展示）。

    own_rules 包含两部分：
    1. 组角色拥有的规则（本组自身权限 + 其他组分享给本组的协作权限）
    2. 本组作为 owner_group_id 分享出去的 cross_group 规则（用于在本组应用权限中回收协作权限）

    仅返回未过期的规则（valid_to 为空或大于当前时间）。
    """
    now = timezone.now()

    def _valid_qs(qs):
        from django.db.models import Q
        return qs.filter(Q(valid_to__isnull=True) | Q(valid_to__gt=now))

    rules = []
    if group.role:
        rules = _format_rules(list(_valid_qs(RoleDataRule.objects.filter(role=group.role))))

    # 本组分享出去的协作规则也加入 own_rules，用于前端"回收协作权限"功能
    shared_rules = _format_rules(list(_valid_qs(RoleDataRule.objects.filter(
        owner_group_id=group.id,
        grant_scope='cross_group',
    ).exclude(role=group.role))))

    return {
        'group_id': group.id,
        'group_name': group.name,
        'group_role_id': group.role_id if group.role else None,
        'own_rules': rules + shared_rules,
        'member_count': group.memberships.count(),
    }


def _load_rules_with_details(user: User, from_group: bool) -> list:
    """加载规则并附带应用名称等详细信息"""
    if from_group:
        memberships = SubjectMembership.objects.filter(user=user).select_related('group__role')
        rules = []
        for m in memberships:
            if m.group.role:
                rules.extend(list(RoleDataRule.objects.filter(role=m.group.role)))
    else:
        if user.role:
            rules = list(RoleDataRule.objects.filter(role=user.role))
        else:
            rules = []

    return _format_rules(rules)


def _format_rules(rules: list) -> list:
    """格式化规则列表，附加应用名称等信息"""
    from apps.applications.models import Application

    app_ids = list(set(r.app_id for r in rules))
    apps = Application.objects.in_bulk(app_ids)

    result = []
    for rule in rules:
        app = apps.get(rule.app_id)
        result.append({
            'id': rule.id,
            'role_id': rule.role_id,
            'app_id': rule.app_id,
            'app_name': app.name if app else f'App-{rule.app_id}',
            'env_type': rule.env_type,
            'env_type_label': ENV_TYPE_LABELS.get(rule.env_type, rule.env_type),
            'is_all_envs': rule.is_all_envs,
            'allow_env_ids': rule.allow_env_ids or [],
            'deny_env_ids': rule.deny_env_ids or [],
            'grant_scope': rule.grant_scope,
            'grant_scope_label': dict(RoleDataRule.GRANT_SCOPES).get(rule.grant_scope, rule.grant_scope),
            'valid_from': rule.valid_from,
            'valid_to': rule.valid_to,
            'business_line_id': rule.business_line_id,
            'owner_group_id': rule.owner_group_id,
        })
    return result


# ─── 兼容旧接口 ──────────────────────────────────────────────

def get_user_effective_permissions(user: User) -> dict:
    """
    兼容旧接口：返回用户权限信息（用于登录响应）。

    新模型中不再有功能权限，menu_codes 返回空列表。
    data_scope 返回用户可见的应用和环境缓存。
    """
    # 从缓存中收集用户可见的应用和环境
    caches = EffectivePermissionCache.objects.filter(
        user_id=user.id, effect='allow',
    ).values('app_id', 'env_id')

    app_ids = list(set(c['app_id'] for c in caches))
    env_ids = list(set(c['env_id'] for c in caches))

    # 业务线从应用关联
    if app_ids:
        from apps.applications.models import Application
        bl_ids = list(Application.objects.filter(
            id__in=app_ids,
        ).values_list('business_line_id', flat=True).distinct())
    else:
        bl_ids = []

    return {
        'roles': [],
        'menu_codes': [],  # 功能权限已移除，所有菜单可见
        'data_scope': {
            'business_line_ids': bl_ids,
            'app_ids': app_ids,
            'env_ids': env_ids,
        },
        'personal_permissions': [],
    }


# ─── 审批人解析 ──────────────────────────────────────────────

def find_business_line_leader(user: User):
    """从用户出发，向上查找最近的业务线负责人"""
    from apps.organizations.models import BusinessLine

    primary_membership = user.memberships.filter(membership_type='primary').first()
    if not primary_membership:
        return None
    group = primary_membership.group
    # 向上遍历找到业务线
    while group:
        if group.business_line.leader:
            return group.business_line.leader
        group = group.parent_group
    return None


def resolve_approvers(user, app_id: int, resolver_type: str, resolver_config: dict):
    """
    根据审批人解析策略，解析出审批人列表。

    支持的策略:
    - app_owner: 应用负责人
    - group_leader: 用户所在组的负责人
    - business_line_leader: 向上查找业务线负责人
    - fixed_user: 固定人员（resolver_config.user_ids）
    - fixed_role: 固定角色组（resolver_config.role 指定 group code）
    - parent_group_leader: 上级组负责人
    - security_team: 安全团队（platform-ops 组成员）
    - ops_team: 运维团队（platform-ops 组成员）
    """
    from apps.applications.models import Application
    from apps.organizations.models import Group as OrgGroup

    approvers = []
    now = timezone.now()

    if resolver_type == 'app_owner':
        try:
            app = Application.objects.select_related('owner').get(id=app_id)
            if app.owner:
                approvers.append(app.owner)
        except Application.DoesNotExist:
            pass

    elif resolver_type == 'group_leader':
        primary_membership = user.memberships.filter(membership_type='primary').select_related('group__leader').first()
        if primary_membership and primary_membership.group.leader:
            approvers.append(primary_membership.group.leader)

    elif resolver_type == 'business_line_leader':
        leader = find_business_line_leader(user)
        if leader:
            approvers.append(leader)

    elif resolver_type == 'fixed_user':
        user_ids = resolver_config.get('user_ids', [])
        if user_ids:
            approvers.extend(list(User.objects.filter(id__in=user_ids, is_active=True)))

    elif resolver_type == 'fixed_role':
        role_code = resolver_config.get('role', '')
        if role_code:
            try:
                group = OrgGroup.objects.get(code=role_code, status='active')
                member_ids = group.memberships.filter(
                    membership_type='primary',
                ).values_list('user_id', flat=True)
                approvers.extend(list(User.objects.filter(id__in=member_ids, is_active=True)))
            except OrgGroup.DoesNotExist:
                pass

    elif resolver_type == 'parent_group_leader':
        primary_membership = user.memberships.filter(membership_type='primary').select_related('group__parent_group__leader').first()
        if primary_membership:
            parent = primary_membership.group.parent_group
            if parent and parent.leader:
                approvers.append(parent.leader)

    elif resolver_type == 'security_team':
        try:
            group = OrgGroup.objects.get(code='platform-ops', status='active')
            member_ids = group.memberships.filter(
                membership_type='primary',
            ).values_list('user_id', flat=True)
            approvers.extend(list(User.objects.filter(id__in=member_ids, is_active=True)))
        except OrgGroup.DoesNotExist:
            pass

    elif resolver_type == 'ops_team':
        try:
            group = OrgGroup.objects.get(code='platform-ops', status='active')
            member_ids = group.memberships.filter(
                membership_type='primary',
            ).values_list('user_id', flat=True)
            approvers.extend(list(User.objects.filter(id__in=member_ids, is_active=True)))
        except OrgGroup.DoesNotExist:
            pass

    return approvers


def apply_permission_request(perm_req):
    """
    权限申请全部审批通过后，根据 request_type 执行实际的权限变更。

    - apply: 给申请人的 user role 添加规则
    - share: 给目标组/目标用户的 role 添加 cross_group 规则
    - revoke/release: 将指定规则标记为过期（软删除）
    """
    from apps.applications.models import Application
    from apps.organizations.models import Group as OrgGroup

    perm_req.status = 'approved'
    perm_req.save()

    request_type = perm_req.request_type
    app = Application.objects.filter(id=perm_req.app_id).first()
    bl_id = app.business_line_id if app else 0
    owner_group_id = perm_req.extra_data.get('owner_group_id', 0) if perm_req.extra_data else 0

    if request_type == 'apply':
        target_group_id = perm_req.extra_data.get('target_group_id') if perm_req.extra_data else None
        target_user_ids = perm_req.extra_data.get('target_user_ids', []) if perm_req.extra_data else []

        # 申请给当前组：规则落到组角色上
        if target_group_id:
            group = OrgGroup.objects.filter(id=target_group_id).first()
            if group:
                if not group.role:
                    group.role = Role.objects.create(
                        name=f'{group.code}_role',
                        owner_type='group',
                        is_system=True,
                    )
                    group.save()
                RoleDataRule.objects.create(
                    role=group.role,
                    business_line_id=bl_id,
                    owner_group_id=owner_group_id,
                    app_id=perm_req.app_id,
                    env_type=perm_req.env_type,
                    is_all_envs=perm_req.is_all_envs,
                    allow_env_ids=perm_req.env_ids or [],
                    deny_env_ids=[],
                    grant_scope=perm_req.grant_scope,
                    valid_from=perm_req.valid_from,
                    valid_to=perm_req.valid_to,
                )
                rebuild_group_cache(group)

        # 申请给指定成员：规则落到用户角色上
        for uid in target_user_ids:
            user = User.objects.filter(id=uid).first()
            if user:
                if not user.role:
                    user.role = Role.objects.create(
                        name=f'{user.username}_role',
                        owner_type='user',
                        is_system=True,
                    )
                    user.save()
                RoleDataRule.objects.create(
                    role=user.role,
                    business_line_id=bl_id,
                    owner_group_id=owner_group_id,
                    app_id=perm_req.app_id,
                    env_type=perm_req.env_type,
                    is_all_envs=perm_req.is_all_envs,
                    allow_env_ids=perm_req.env_ids or [],
                    deny_env_ids=[],
                    grant_scope=perm_req.grant_scope,
                    valid_from=perm_req.valid_from,
                    valid_to=perm_req.valid_to,
                )
                rebuild_user_cache(user)

        # 兼容旧逻辑：没有指定接收方时，规则落到申请人自身
        if not target_group_id and not target_user_ids:
            user = perm_req.user
            if not user.role:
                user.role = Role.objects.create(
                    name=f'{user.username}_role',
                    owner_type='user',
                    is_system=True,
                )
                user.save()
            RoleDataRule.objects.create(
                role=user.role,
                business_line_id=bl_id,
                owner_group_id=owner_group_id,
                app_id=perm_req.app_id,
                env_type=perm_req.env_type,
                is_all_envs=perm_req.is_all_envs,
                allow_env_ids=perm_req.env_ids or [],
                deny_env_ids=[],
                grant_scope=perm_req.grant_scope,
                valid_from=perm_req.valid_from,
                valid_to=perm_req.valid_to,
            )
            rebuild_user_cache(user)

    elif request_type == 'share':
        target_group_id = perm_req.extra_data.get('target_group_id') if perm_req.extra_data else None
        target_user_ids = perm_req.extra_data.get('target_user_ids', []) if perm_req.extra_data else []

        if target_group_id:
            group = OrgGroup.objects.filter(id=target_group_id).first()
            if group:
                if not group.role:
                    group.role = Role.objects.create(
                        name=f'{group.code}_role',
                        owner_type='group',
                        is_system=True,
                    )
                    group.save()
                RoleDataRule.objects.create(
                    role=group.role,
                    business_line_id=bl_id,
                    owner_group_id=owner_group_id,
                    app_id=perm_req.app_id,
                    env_type=perm_req.env_type,
                    is_all_envs=perm_req.is_all_envs,
                    allow_env_ids=perm_req.env_ids or [],
                    deny_env_ids=[],
                    grant_scope='cross_group',
                    valid_from=perm_req.valid_from,
                    valid_to=perm_req.valid_to,
                )
                rebuild_group_cache(group)

        for uid in target_user_ids:
            user = User.objects.filter(id=uid).first()
            if user:
                if not user.role:
                    user.role = Role.objects.create(
                        name=f'{user.username}_role',
                        owner_type='user',
                        is_system=True,
                    )
                    user.save()
                RoleDataRule.objects.create(
                    role=user.role,
                    business_line_id=bl_id,
                    owner_group_id=owner_group_id,
                    app_id=perm_req.app_id,
                    env_type=perm_req.env_type,
                    is_all_envs=perm_req.is_all_envs,
                    allow_env_ids=perm_req.env_ids or [],
                    deny_env_ids=[],
                    grant_scope='cross_group',
                    valid_from=perm_req.valid_from,
                    valid_to=perm_req.valid_to,
                )
                rebuild_user_cache(user)

    elif request_type in ('revoke', 'release'):
        rule_ids = perm_req.extra_data.get('rule_ids', []) if perm_req.extra_data else []
        if rule_ids:
            rules_to_expire = list(RoleDataRule.objects.filter(id__in=rule_ids).select_related('role'))
            if rules_to_expire:
                RoleDataRule.objects.filter(id__in=rule_ids).update(valid_to=timezone.now())

                affected_user_ids = set()
                affected_group_ids = set()
                for rule in rules_to_expire:
                    if rule.role.owner_type == 'user':
                        user = User.objects.filter(role_id=rule.role_id).first()
                        if user:
                            affected_user_ids.add(user.id)
                    else:
                        group = OrgGroup.objects.filter(role_id=rule.role_id).first()
                        if group:
                            affected_group_ids.add(group.id)

                for uid in affected_user_ids:
                    try:
                        rebuild_user_cache(User.objects.get(id=uid))
                    except User.DoesNotExist:
                        pass
                for gid in affected_group_ids:
                    try:
                        rebuild_group_cache(OrgGroup.objects.get(id=gid))
                    except OrgGroup.DoesNotExist:
                        pass


def calculate_approval_flow(user, app_id: int, env_type: str, grant_scope: str = 'own_group'):
    """
    根据用户、应用、环境类型、授权范围，动态计算审批流。

    返回结构:
    {
        "requires_approval": True,
        "steps": [
            {
                "order": 1,
                "name": "应用负责人审批",
                "dimension": "app_owner",
                "approvers": [{"id": 1, "name": "张三"}],
                "required_count": 1,
                "timeout_hours": 24,
            },
        ],
    }
    """
    from apps.authz.models import EnvironmentApprovalConfig

    config = EnvironmentApprovalConfig.objects.filter(
        env_type=env_type,
        grant_scope=grant_scope,
        is_active=True,
    ).select_related('flow_template').first()

    if not config or not config.requires_approval:
        return {'requires_approval': False, 'steps': []}

    template = config.flow_template
    if not template:
        return {'requires_approval': False, 'steps': []}

    steps = []
    for step in template.steps or []:
        resolver_type = step.get('approver_resolver', '')
        resolver_config = step.get('resolver_config', {})
        approvers = resolve_approvers(user, app_id, resolver_type, resolver_config)

        steps.append({
            'order': step.get('order', 1),
            'name': step.get('name', ''),
            'dimension': step.get('dimension', ''),
            'approvers': [{'id': u.id, 'name': u.display_name} for u in approvers],
            'required_count': step.get('required_count', 1),
            'timeout_hours': step.get('timeout_hours', 24),
        })

    return {'requires_approval': True, 'steps': steps}