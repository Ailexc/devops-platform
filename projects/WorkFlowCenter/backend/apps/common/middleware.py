"""
公共中间件
"""
from django.http import JsonResponse


class IdempotencyMiddleware:
    """
    幂等性中间件：检查请求头中的 Idempotency-Key。
    同一个 Key 在 TTL 内的重复请求将返回缓存的响应。
    Demo 阶段仅做校验，不存储。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')
        if idempotency_key and request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # Demo 阶段：仅标记 header，不做缓存
            request._idempotency_key = idempotency_key
        return self.get_response(request)
