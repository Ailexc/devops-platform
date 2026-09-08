"""用户管理接口（管理员）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.deps import get_current_admin
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut], summary="用户列表（管理员）")
def list_users(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="新增用户（管理员）")
def create_user(req: UserCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
        email=req.email,
        department=req.department,
        phone=req.phone,
        is_active=req.is_active,
        is_admin=req.is_admin,
        source=req.source,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut, summary="更新用户（管理员）")
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db),
                _=Depends(get_current_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    data = req.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户（管理员）")
def delete_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    db.delete(user)
    db.commit()
    return None
