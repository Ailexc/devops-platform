"""系统接口：健康检查、身份源状态、认证日志。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.auth_providers import build_provider_chain
from ..core.deps import get_current_admin
from ..db import get_db
from ..models import AuthLog
from ..schemas import AuthLogOut, ProviderStatus, SystemHealth

router = APIRouter(prefix="/api/system", tags=["system"])
settings = get_settings()


@router.get("/health", response_model=SystemHealth, summary="健康检查")
def health(db: Session = Depends(get_db)):
    chain = build_provider_chain(db)
    providers = [
        ProviderStatus(
            name=p.name,
            order=i,
            available=p.is_available(),
            note="" if p.is_available() else "不可用（未启用或连接失败）",
        )
        for i, p in enumerate(chain.providers)
    ]
    return SystemHealth(
        status="ok", app=settings.app_name, version="0.1.0", providers=providers
    )


@router.get("/providers", response_model=list[ProviderStatus], summary="当前身份源降级链状态")
def providers(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    chain = build_provider_chain(db)
    return [
        ProviderStatus(
            name=p.name,
            order=i,
            available=p.is_available(),
            note="" if p.is_available() else "不可用（未启用或连接失败）",
        )
        for i, p in enumerate(chain.providers)
    ]


@router.get("/auth-logs", response_model=list[AuthLogOut], summary="认证日志（管理员，审计用）")
def auth_logs(limit: int = 50, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(AuthLog).order_by(AuthLog.id.desc()).limit(min(limit, 200)).all()
