"""统一认证接入（方式二）· 身份接口：返回当前用户（验证直连 JWKS 验签识别用户）。"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CurrentUserView(APIView):
    """当前用户：带统一 JWT（Bearer）访问，返回识别出的本地用户。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "username": u.username,
            "is_active": u.is_active,
            "auth_source": "unified-jwks",
        })
