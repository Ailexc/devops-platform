"""JWKS 公钥发布端点。"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..security import jwks_payload

router = APIRouter(tags=["jwks"])


@router.get("/.well-known/jwks.json", summary="JWT 公钥（JWKS），供各业务系统验签")
def jwks():
    return JSONResponse(jwks_payload())
