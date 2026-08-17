"""应用注册表接口：门户应用广场 + 管理 CRUD。"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.deps import get_current_admin, get_current_user
from ..db import get_db
from ..models import AppRegistration
from ..schemas import AppCreate, AppCreateOut, AppOut, AppUpdate

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.get("", response_model=list[AppOut], summary="门户应用广场列表（需登录）")
def list_apps(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(AppRegistration)
        .filter(AppRegistration.enabled.is_(True))
        .order_by(AppRegistration.sort_order, AppRegistration.id)
        .all()
    )


@router.post("", response_model=AppCreateOut, status_code=status.HTTP_201_CREATED, summary="新增应用（管理员，返回一次性 client_secret）")
def create_app(req: AppCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if db.query(AppRegistration).filter(AppRegistration.app_id == req.app_id).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "app_id 已存在")
    app = AppRegistration(
        app_id=req.app_id,
        name=req.name,
        description=req.description,
        icon=req.icon,
        home_url=req.home_url,
        sso_type=req.sso_type,
        access_mode=req.access_mode,
        enabled=req.enabled,
        sort_order=req.sort_order,
        client_id=f"{req.app_id}-{secrets.token_hex(4)}",
        client_secret=secrets.token_urlsafe(24),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return AppCreateOut.model_validate(app)


@router.get("/manage", response_model=list[AppOut], summary="应用管理列表（管理员，含禁用项与 client_id）")
def manage_apps(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return (
        db.query(AppRegistration)
        .order_by(AppRegistration.sort_order, AppRegistration.id)
        .all()
    )


@router.put("/{app_id}", response_model=AppOut, summary="更新应用（管理员）")
def update_app(app_id: str, req: AppUpdate, db: Session = Depends(get_db),
               _=Depends(get_current_admin)):
    app = db.query(AppRegistration).filter(AppRegistration.app_id == app_id).first()
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "应用不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return AppOut.model_validate(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除应用（管理员）")
def delete_app(app_id: str, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    app = db.query(AppRegistration).filter(AppRegistration.app_id == app_id).first()
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "应用不存在")
    db.delete(app)
    db.commit()
    return None
