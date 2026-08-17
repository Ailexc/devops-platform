"""
重试策略工具
"""
import math


def calculate_exponential_backoff(
    attempt: int,
    base_delay: float = 4.0,
    max_delay: float = 300.0,
    jitter: bool = True,
) -> float:
    """计算指数退避延迟 (秒)"""
    import random

    delay = min(base_delay * (2**attempt), max_delay)
    if jitter:
        delay *= 0.5 + random.random() * 0.5  # 50-100% jitter
    return delay
