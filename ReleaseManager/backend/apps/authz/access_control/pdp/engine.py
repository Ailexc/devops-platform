"""
PDP — Policy Decision Point

核心鉴权引擎，面向对象封装 PolicyDecisionPoint 类。

职责:
1. evaluate()         — 单次鉴权: user + resource + action → bool
2. evaluate_batch()   — 批量鉴权
3. get_available_actions() — 获取某资源上用户可执行的操作列表

设计说明:
- 从 PolicyRegistry 加载 PAP 定义的策略
- 从 Django ORM 加载 resource 实例（PIP 数据源）
- 逐规则评估（有序，命中即返回）
- 默认拒绝（Deny by default）
"""

import logging

from apps.authz.access_control.pap.base import PolicyRegistry

logger = logging.getLogger(__name__)


class PolicyDecisionPoint:
    """
    策略决策点 — 核心鉴权引擎

    Usage:
        pdp = PolicyDecisionPoint()
        result = pdp.evaluate(request.user, 'group', 3, 'manage')
        actions = pdp.get_available_actions(request.user, 'group', 3)
    """

    # 资源类型 → Django Model 映射
    MODEL_MAP = {
        "group": None,  # 延迟导入避免循环依赖
        "business_line": None,
        "user": None,
    }

    def __init__(self, registry=None):
        self._registry = registry or PolicyRegistry
        self._load_models()

    def _load_models(self):
        """延迟加载 Django Model"""
        if self.MODEL_MAP["group"] is None:
            from apps.organizations.models import BusinessLine, Group
            from apps.accounts.models import User
            self.MODEL_MAP["group"] = Group
            self.MODEL_MAP["business_line"] = BusinessLine
            self.MODEL_MAP["user"] = User

    # ── 公开接口 ─────────────────────────────────────────────

    def evaluate(self, user, resource_type: str, resource_id: int, action: str) -> bool:
        """
        评估：用户能否对某个资源执行某个操作

        流程:
        1. 按 (resource_type, action) 查找策略定义
        2. 加载资源实例
        3. 逐条规则评估（有序，命中即返回）
        4. 无规则命中则返回 default_effect
        """
        # 1. 查找策略
        policy_cls = self._registry.get(resource_type, action)
        if policy_cls is None:
            logger.warning(
                "未找到策略定义: resource_type=%s, action=%s", resource_type, action
            )
            return False

        # 2. 加载资源
        resource = self._load_resource(resource_type, resource_id)
        if resource is None:
            logger.warning(
                "资源不存在: resource_type=%s, resource_id=%s", resource_type, resource_id
            )
            return False

        # 3. 逐规则评估
        for rule in policy_cls.get_rules():
            try:
                if rule.checker.check(user, resource):
                    result = rule.effect == "allow"
                    logger.debug(
                        "PDP评估: user=%s type=%s id=%s action=%s → %s (rule=%s)",
                        user.id, resource_type, resource_id, action,
                        "allow" if result else "deny", rule._name,
                    )
                    return result
            except Exception as e:
                logger.error(
                    "PDP规则检查异常: user=%s rule=%s error=%s",
                    user.id, rule._name, e,
                )
                # 检查器异常时跳过该规则，继续评估下一条

        # 4. 默认效果
        return policy_cls.default_effect == "allow"

    def evaluate_batch(self, user, checks: list) -> dict:
        """
        批量评估

        Args:
            checks: [
                {"type": "group", "id": 3, "action": "manage"},
                {"type": "app",  "id": 5, "action": "edit"},
            ]

        Returns:
            {"group:3:manage": True, "app:5:edit": False}
        """
        result = {}
        for check in checks:
            key = f"{check['type']}:{check['id']}:{check['action']}"
            result[key] = self.evaluate(
                user, check["type"], check["id"], check["action"]
            )
        return result

    def get_available_actions(self, user, resource_type: str, resource_id: int) -> list:
        """
        获取用户在某个资源上所有可用的操作列表

        这是前端树节点渲染的核心接口 —— 返回当前节点可显示的按钮列表。
        """
        available = []
        for policy_cls in self._registry.get_by_resource_type(resource_type):
            if self.evaluate(user, resource_type, resource_id, policy_cls.action):
                available.append(policy_cls.action)
        return available

    # ── 内部方法 ─────────────────────────────────────────────

    def _load_resource(self, resource_type: str, resource_id: int):
        """从数据库加载资源实例"""
        model = self.MODEL_MAP.get(resource_type)
        if model is None:
            return None
        try:
            return model.objects.get(id=resource_id)
        except model.DoesNotExist:
            return None
        except Exception as e:
            logger.error("加载资源失败: type=%s id=%s error=%s", resource_type, resource_id, e)
            return None
