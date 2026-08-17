"""
ABAC-Lite 权限鉴权引擎

分层架构:
    PAP — Policy Administration Point: 声明式策略定义
    PIP — Policy Information Point:    原子检查器
    PDP — Policy Decision Point:       决策引擎
    PEP — Policy Enforcement Point:    守卫装饰器

对外暴露的便利函数:
    check_user_can(user, type, id, action) → bool
    check_user_can_batch(user, checks) → dict
    get_available_actions(user, type, id) → list
    get_user_org_scope(user) → dict
    annotate_org_tree(user, tree_nodes) → list
    require_permission(type, action) → decorator
"""

# 导入策略定义以触发注册（必须在 PDP 初始化之前）
from apps.authz.access_control import pap  # noqa: F401
from apps.authz.access_control.pap import policies  # noqa: F401

from apps.authz.access_control.pdp.engine import PolicyDecisionPoint
from apps.authz.access_control.pep.decorators import require_permission

# 全局 PDP 单例
_pdp = PolicyDecisionPoint()


def check_user_can(user, resource_type: str, resource_id: int, action: str) -> bool:
    """统一鉴权入口: user + resource + action → allow/deny"""
    return _pdp.evaluate(user, resource_type, resource_id, action)


def check_user_can_batch(user, checks: list) -> dict:
    """批量鉴权入口"""
    return _pdp.evaluate_batch(user, checks)


def get_available_actions(user, resource_type: str, resource_id: int) -> list:
    """获取用户在某个资源上所有可用的操作列表"""
    return _pdp.get_available_actions(user, resource_type, resource_id)


def get_user_org_scope(user) -> dict:
    """获取用户组织可见/可管理范围"""
    from .utils import get_user_org_scope as _scope
    return _scope(user)


def annotate_org_tree(user, tree_nodes: list) -> list:
    """注解组织树（全量展示，附加 accessible + available_actions）"""
    from .utils import annotate_org_tree as _annotate
    return _annotate(user, tree_nodes)
