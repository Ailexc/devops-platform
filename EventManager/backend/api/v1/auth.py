"""统一认证接入（方式二）· 身份接口：返回当前用户（验证直连 JWKS 验签识别用户）。"""
from ninja import Router
from ninja.responses import Response

from api.unified_auth import UnifiedJWTAuth

router = Router(auth=UnifiedJWTAuth(), tags=["统一认证"])


@router.get("/me")
def current_user(request):
    u = request.auth
    return {
        "username": u.username,
        "is_active": u.is_active,
        "auth_source": "unified-jwks",
    }
