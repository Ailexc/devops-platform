"""
PIP — 具体检查器实现

每个检查器继承 BaseChecker，实现:
- id: str          — 唯一标识符
- description: str — 人类可读描述
- check(user, resource) → bool

这些检查器在 pap/policies.py 中被 Rule 引用。
"""

from .base import BaseChecker
from apps.authz.models import SubjectMembership
from apps.organizations.models import BusinessLine, Group


class IsAuditAdmin(BaseChecker):
    """用户是审计管理员 — 全量 visible，但所有 manage 操作拒绝"""

    id = "is_audit_admin"
    description = "用户是审计管理员"

    def check(self, user, resource) -> bool:
        return getattr(user, 'is_audit_admin', False)


class IsResourceLeader(BaseChecker):
    """
    用户是 resource 的负责人（通用）
    
    适用于 Group 和 BusinessLine（均有 leader FK 字段）。
    resource.leader_id == user.id 即为负责人。
    """

    id = "is_resource_leader"
    description = "用户是此资源的负责人"

    def check(self, user, resource) -> bool:
        return resource.leader_id == user.id


class IsGroupMember(BaseChecker):
    """用户是该 resource（Group）的组成员"""

    id = "is_group_member"
    description = "用户是组成员"

    def check(self, user, resource) -> bool:
        return SubjectMembership.objects.filter(
            user=user,
            group=resource,
        ).exists()


class IsBlUnderLeader(BaseChecker):
    """
    用户是 Group 所属业务线的负责人
    
    注意: resource 必须是 Group 实例。
    判断: 该 Group 所属的 BusinessLine.leader == user
    """

    id = "is_bl_under_leader"
    description = "用户是所属业务线的负责人"

    def check(self, user, resource) -> bool:
        return BusinessLine.objects.filter(
            leader=user,
            groups=resource,
        ).exists()


class IsAuthenticated(BaseChecker):
    """用户已通过认证（最低门槛）"""

    id = "is_authenticated"
    description = "用户已通过认证"

    def check(self, user, resource) -> bool:
        return user.is_authenticated
