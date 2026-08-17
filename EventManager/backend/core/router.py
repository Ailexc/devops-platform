import fnmatch
import logging
from typing import Type

from core.handler import BaseEventHandler
from core.exceptions import HandlerNotFound

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """事件 Handler 注册表 - 基于模式匹配路由"""

    def __init__(self):
        self._handlers: dict[str, Type[BaseEventHandler]] = {}

    def register(self, pattern: str, handler_cls: Type[BaseEventHandler]) -> None:
        """注册 Handler"""
        self._handlers[pattern] = handler_cls
        logger.debug("Registered handler %s for pattern %s", handler_cls.__name__, pattern)

    def resolve(self, event_type: str) -> Type[BaseEventHandler]:
        """根据事件类型匹配 Handler"""
        # 精确匹配
        if event_type in self._handlers:
            return self._handlers[event_type]
        # 通配符匹配
        for pattern, handler_cls in self._handlers.items():
            if fnmatch.fnmatch(event_type, pattern):
                return handler_cls
        raise HandlerNotFound(event_type)

    def get_all(self) -> dict[str, str]:
        """返回所有注册信息"""
        return {p: cls.__name__ for p, cls in self._handlers.items()}


# 全局单例
registry = EventHandlerRegistry()
