"""
PAP — 声明式策略定义

每个策略是一个 Policy 子类，在类体中用 Rule 声明规则链。
规则按定义顺序评估，命中即返回（不继续评估后续规则）。

设计原则:
- "发起" ≠ "生效": share/apply/revoke 走审批流，普通成员也可发起
- 审计管理员: 全量 accessible，但所有 manage 操作 deny
- 默认拒绝: 无规则命中时返回 default_effect
"""

from .base import Policy, Rule
from apps.authz.access_control.pip import checkers as PIP


class GroupManagePolicy(Policy):
    """
    组管理权限 — 增删改成员、调整权限、修改配置等
    
    谁可以管理一个组的成员和配置？
    - 审计管理员: ❌ 不可操作
    - 组负责人:   ✅ 可管理本组
    - 业务线负责人: ✅ 可管理下属所有组
    - 其他人:     ❌ 默认拒绝
    """
    id = "group_manage"
    resource_type = "group"
    action = "manage"
    title = "组管理"
    description = "谁能管理一个组的成员和配置"
    default_effect = "deny"

    deny_admin    = Rule("deny",  PIP.IsAuditAdmin(),      "审计管理员不可操作")
    allow_leader  = Rule("allow", PIP.IsResourceLeader(),  "组负责人可管理本组")
    allow_bl      = Rule("allow", PIP.IsBlUnderLeader(),   "业务线负责人可管理下属组")


class GroupViewPolicy(Policy):
    """
    组查看权限 — 查看组详情、成员列表、权限信息
    
    谁可以查看某个组的详情？
    - 审计管理员: ✅ 全量可见
    - 组负责人:   ✅ 可见
    - 业务线负责人: ✅ 可见
    - 组成员:     ✅ 可见
    - 其他人:     ❌ 默认拒绝
    """
    id = "group_view"
    resource_type = "group"
    action = "view"
    title = "组查看"
    description = "谁能查看组的详情信息"
    default_effect = "deny"

    allow_admin  = Rule("allow", PIP.IsAuditAdmin(),      "审计管理员全量可见")
    allow_leader = Rule("allow", PIP.IsResourceLeader(),  "组负责人可见")
    allow_bl     = Rule("allow", PIP.IsBlUnderLeader(),   "业务线负责人可见")
    allow_member = Rule("allow", PIP.IsGroupMember(),     "组成员可见")


class GroupSharePolicy(Policy):
    """
    分享协作应用 — 将本组负责的应用分享给其他组（走审批流）

    谁可以发起分享？
    - 审计管理员: ❌ 不可操作
    - 组成员:     ✅ 可发起（走审批流）
    - 组负责人:   ✅ 可发起
    - 业务线负责人: ✅ 可代下属组发起
    """
    id = "group_share"
    resource_type = "group"
    action = "share"
    title = "分享协作"
    description = "将本组负责的应用分享给其他组（发起审批）"
    default_effect = "deny"

    deny_admin   = Rule("deny",  PIP.IsAuditAdmin(),      "审计管理员不可操作")
    allow_member = Rule("allow", PIP.IsGroupMember(),      "组成员可发起协作申请")
    allow_leader = Rule("allow", PIP.IsResourceLeader(),   "组负责人可发起分享")
    allow_bl     = Rule("allow", PIP.IsBlUnderLeader(),    "业务线负责人可代下属组发起")


class GroupApplyPolicy(Policy):
    """
    申请权限 — 发起权限申请（走审批流）
    
    谁可以发起权限申请？
    - 所有已认证用户: ✅ 可申请
    """
    id = "group_apply"
    resource_type = "group"
    action = "apply"
    title = "权限申请"
    description = "发起权限申请（走审批流）"
    default_effect = "deny"

    allow_any    = Rule("allow", PIP.IsAuthenticated(), "已认证用户可申请")


class GroupRevokePolicy(Policy):
    """
    回收协作权限 — 回收分享出去的协作权限

    谁可以回收？
    - 审计管理员: ❌ 不可操作
    - 组成员:     ✅ 可发起回收
    - 组负责人:   ✅ 可直接回收
    - 业务线负责人: ✅ 可回收下属组的协作
    """
    id = "group_revoke"
    resource_type = "group"
    action = "revoke"
    title = "回收协作"
    description = "回收分享出去的协作权限"
    default_effect = "deny"

    deny_admin   = Rule("deny",  PIP.IsAuditAdmin(),      "审计管理员不可操作")
    allow_member = Rule("allow", PIP.IsGroupMember(),      "组成员可发起回收")
    allow_leader = Rule("allow", PIP.IsResourceLeader(),   "组负责人可直接回收")
    allow_bl     = Rule("allow", PIP.IsBlUnderLeader(),    "业务线负责人可回收下属组协作")



# ── BusinessLine 级别策略 ───────────────────────────────────

class BusinessLineManagePolicy(Policy):
    """
    业务线管理权限

    谁可以管理一个业务线？
    - 审计管理员: ❌ 不可操作
    - 业务线负责人: ✅ 可管理
    """
    id = "bl_manage"
    resource_type = "business_line"
    action = "manage"
    title = "业务线管理"
    description = "谁能管理业务线配置"
    default_effect = "deny"

    deny_admin    = Rule("deny",  PIP.IsAuditAdmin(),      "审计管理员不可操作")
    allow_leader  = Rule("allow", PIP.IsResourceLeader(),  "业务线负责人可管理")


class BusinessLineViewPolicy(Policy):
    """
    业务线查看权限

    谁可以查看业务线详情？
    - 审计管理员: ✅ 全量可见
    - 业务线负责人: ✅ 可见
    """
    id = "bl_view"
    resource_type = "business_line"
    action = "view"
    title = "业务线查看"
    description = "谁能查看业务线详情"
    default_effect = "deny"

    allow_admin  = Rule("allow", PIP.IsAuditAdmin(),      "审计管理员全量可见")
    allow_leader = Rule("allow", PIP.IsResourceLeader(),  "业务线负责人可见")
