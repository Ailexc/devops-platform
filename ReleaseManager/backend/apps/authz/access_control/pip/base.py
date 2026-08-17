"""
PIP — Policy Information Point

BaseChecker 基类 + 组合检查器（_OrChecker / _AndChecker / _NotChecker）

设计说明:
- 每个检查器是一个独立的类，继承 BaseChecker
- 只需实现 id / description / check(user, resource) 三个接口
- 支持 | & ~ 操作符组合，像搭积木一样构建复杂条件
"""


class BaseChecker:
    """原子检查器基类"""

    id: str = ""
    description: str = ""

    def check(self, user, resource) -> bool:
        """执行检查逻辑，子类必须实现"""
        raise NotImplementedError

    def __or__(self, other):
        return _OrChecker(self, other)

    def __and__(self, other):
        return _AndChecker(self, other)

    def __invert__(self):
        return _NotChecker(self)


class _OrChecker(BaseChecker):
    """组合检查器: A OR B"""

    def __init__(self, a: BaseChecker, b: BaseChecker):
        self._a = a
        self._b = b
        self.id = f"({a.id} OR {b.id})"
        self.description = f"{a.description} 或 {b.description}"

    def check(self, user, resource) -> bool:
        return self._a.check(user, resource) or self._b.check(user, resource)


class _AndChecker(BaseChecker):
    """组合检查器: A AND B"""

    def __init__(self, a: BaseChecker, b: BaseChecker):
        self._a = a
        self._b = b
        self.id = f"({a.id} AND {b.id})"
        self.description = f"{a.description} 且 {b.description}"

    def check(self, user, resource) -> bool:
        return self._a.check(user, resource) and self._b.check(user, resource)


class _NotChecker(BaseChecker):
    """组合检查器: NOT A"""

    def __init__(self, inner: BaseChecker):
        self._inner = inner
        self.id = f"(NOT {inner.id})"
        self.description = f"非({inner.description})"

    def check(self, user, resource) -> bool:
        return not self._inner.check(user, resource)
