"""
PAP — Policy Administration Point

声明式策略定义基础设施，仿 DRF Serializer 设计模式:
- PolicyMeta: 元类，在子类定义时自动收集 Rule 并注册
- Rule: 描述符，声明式定义一条规则 (effect + checker + reason)
- Policy: 基类，所有策略须继承此类
- PolicyRegistry: 全局策略注册表
"""

from apps.authz.access_control.pip.base import BaseChecker


class Rule:
    """
    声明式规则描述符 — 类似 DRF 的 Field

    用法:
        class SomePolicy(Policy):
            allow_admin = Rule("allow", IsAuditAdmin(), "审计管理员全量可见")
            deny_guest  = Rule("deny",  IsGuest(),     "访客拒绝")
    """

    def __init__(self, effect: str, checker: BaseChecker, reason: str = ""):
        """
        Args:
            effect: "allow" | "deny"
            checker: BaseChecker 实例或组合检查器
            reason: 人类可读的原因说明
        """
        self.effect = effect
        self.checker = checker
        self.reason = reason
        self._name: str = ""  # 由 PolicyMeta 自动填充

    def __repr__(self):
        return f"<Rule: {self.effect} if {self.checker.id}>"


class PolicyMeta(type):
    """
    元类: 在子类定义时自动收集 Rule 并注册到全局注册表

    工作方式（类似 DRF SerializerMetaclass）:
    1. 扫描类属性，收集所有 Rule 实例
    2. 按定义顺序存入 _rules 列表
    3. 自动注册到 PolicyRegistry
    """

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)

        # 跳过 Policy 基类本身
        if name == "Policy":
            return cls

        # 收集 Rule 实例
        rules = []
        for attr_name, attr_val in list(attrs.items()):
            if isinstance(attr_val, Rule):
                attr_val._name = attr_name
                rules.append(attr_val)

        cls._rules = rules
        cls._id = getattr(cls, "id", name)

        # 自动注册
        PolicyRegistry.register(cls)

        return cls


class Policy(metaclass=PolicyMeta):
    """
    策略基类 — 所有策略定义必须继承此类

    子类需要定义:
        id: str               — 策略唯一标识
        resource_type: str    — 资源类型 (group, business_line, user, app...)
        action: str           — 操作标识 (manage, view, share, apply, revoke...)
        title: str            — 策略标题
        description: str      — 策略说明
        default_effect: str   — 无规则命中时的默认效果 ("allow" | "deny")

    子类在类体中声明 Rule:
        class SomePolicy(Policy):
            resource_type = "group"
            action = "manage"
            ...
            allow_some = Rule("allow", SomeChecker(), "说明")
    """

    id: str = ""
    resource_type: str = ""
    action: str = ""
    title: str = ""
    description: str = ""
    default_effect: str = "deny"

    @classmethod
    def get_rules(cls):
        """获取有序规则列表"""
        return cls._rules

    @classmethod
    def get_id(cls):
        return cls._id


class PolicyRegistry:
    """全局策略注册表"""

    _registry: dict = {}

    @classmethod
    def register(cls, policy_cls):
        """注册策略类"""
        key = (policy_cls.resource_type, policy_cls.action)
        if key in cls._registry:
            # 防止重复注册（模块重载时可能发生）
            return
        cls._registry[key] = policy_cls

    @classmethod
    def get(cls, resource_type: str, action: str):
        """按 (resource_type, action) 查找策略"""
        return cls._registry.get((resource_type, action))

    @classmethod
    def get_by_resource_type(cls, resource_type: str) -> list:
        """获取某资源类型的所有策略"""
        return [p for k, p in cls._registry.items() if k[0] == resource_type]

    @classmethod
    def all(cls) -> list:
        """获取所有已注册的策略"""
        return list(cls._registry.values())
