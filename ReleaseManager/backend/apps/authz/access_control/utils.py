"""
工具函数 — get_user_org_scope() + annotate_org_tree()

这些函数是 PDP 的上层封装，专门为"组织权限管理"页面服务。
"""

from apps.authz.access_control.pdp.engine import PolicyDecisionPoint


def get_user_org_scope(user):
    """
    获取用户组织可见/可管理范围。

    返回:
    {
        'is_audit_admin': bool,
        'accessible_bl_ids': set | "all",    # 可查看详情的业务线
        'accessible_group_ids': set | "all", # 可查看详情的组
        'manageable_group_ids': set | "all", # 可管理的组
        'is_business_line_leader': bool,
        'is_group_leader': bool,
    }

    审计管理员: 全部 accessible, manageable 为空
    """
    if getattr(user, 'is_audit_admin', False):
        return {
            "is_audit_admin": True,
            "accessible_bl_ids": "all",
            "accessible_group_ids": "all",
            "manageable_group_ids": set(),
            "is_business_line_leader": False,
            "is_group_leader": False,
        }

    # 延迟导入避免循环依赖
    from apps.organizations.models import BusinessLine, Group
    from apps.authz.models import SubjectMembership

    accessible_bl_ids = set()
    accessible_group_ids = set()
    manageable_group_ids = set()

    # 业务线负责人 → 该业务线下全部 accessible + manageable
    for bl in BusinessLine.objects.filter(leader=user):
        accessible_bl_ids.add(bl.id)
        group_ids = list(
            Group.objects.filter(business_line=bl).values_list("id", flat=True)
        )
        accessible_group_ids.update(group_ids)
        manageable_group_ids.update(group_ids)

    # 组负责人 → 本组 accessible + manageable
    for g in Group.objects.filter(leader=user):
        accessible_group_ids.add(g.id)
        manageable_group_ids.add(g.id)
        accessible_bl_ids.add(g.business_line_id)

    # 普通成员 → 所属组 accessible（不可 manage）
    for m in (
        SubjectMembership.objects.filter(user=user)
        .select_related("group")
    ):
        accessible_group_ids.add(m.group_id)
        accessible_bl_ids.add(m.group.business_line_id)

    return {
        "is_audit_admin": False,
        "accessible_bl_ids": accessible_bl_ids,
        "accessible_group_ids": accessible_group_ids,
        "manageable_group_ids": manageable_group_ids,
        "is_business_line_leader": BusinessLine.objects.filter(leader=user).exists(),
        "is_group_leader": Group.objects.filter(leader=user).exists(),
    }


def annotate_org_tree(user, tree_nodes):
    """
    注解组织树（不过滤，全量展示）:
    1. 为每个节点附加 accessible: bool
    2. 为 accessible 的节点附加 available_actions: list

    前端据此决定:
    - accessible=false → 右侧显示"无权查看"
    - accessible=true → 正常渲染详情 + 操作按钮
    """
    scope = get_user_org_scope(user)
    pdp = PolicyDecisionPoint()

    def _is_accessible(node):
        """判断单个节点是否可访问"""
        if node["type"] == "business_line":
            if scope["accessible_bl_ids"] == "all":
                return True
            return node["id"] in scope["accessible_bl_ids"]
        elif node["type"] == "group":
            if scope["accessible_group_ids"] == "all":
                return True
            return node["id"] in scope["accessible_group_ids"]
        elif node["type"] == "user":
            # 用户节点跟随父组可见性（由外层递归保证，这里默认 True）
            return True
        return False

    def _annotate_node(node):
        """递归注解单个节点"""
        new_node = {**node}
        accessible = _is_accessible(node)
        new_node["accessible"] = accessible

        if accessible:
            new_node["available_actions"] = pdp.get_available_actions(
                user, node["type"], node["id"]
            )
        else:
            new_node["available_actions"] = []

        # 递归处理子节点
        if node.get("children"):
            new_node["children"] = [
                _annotate_node(c) for c in node["children"]
            ]

        return new_node

    return [_annotate_node(n) for n in tree_nodes]
