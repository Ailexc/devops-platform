class EventError(Exception):
    """事件处理基础异常"""

    def __init__(self, message: str, retryable: bool = True):
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class TransientError(EventError):
    """临时故障，可重试（网络超时、限流等）"""

    def __init__(self, message: str = "Temporary processing failure"):
        super().__init__(message, retryable=True)


class PermanentError(EventError):
    """永久故障，不应重试（数据无效、Schema 不匹配等）"""

    def __init__(self, message: str = "Permanent processing failure"):
        super().__init__(message, retryable=False)


class HandlerNotFound(EventError):
    """未找到匹配的 Handler"""

    def __init__(self, event_type: str):
        super().__init__(f"No handler found for event type: {event_type}", retryable=False)
