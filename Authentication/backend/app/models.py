"""ORM 模型：用户 / 应用注册 / 认证日志。"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # 仅本地身份源使用；LDAP/Okta 用户可为空
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    department: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # 默认身份源：local / ldap / okta
    source: Mapped[str] = mapped_column(String(16), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AppRegistration(Base):
    __tablename__ = "app_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    app_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(64), default="AppstoreOutlined")
    home_url: Mapped[str] = mapped_column(String(512), default="")
    # sso 类型：token(携带JWT跳转) / oidc(授权码流,预留)
    sso_type: Mapped[str] = mapped_column(String(16), default="token")
    # 接入方式：gateway=经统一网关 forwardAuth；direct=业务后端 JWKS 自验签
    access_mode: Mapped[str] = mapped_column(String(16), default="gateway")
    client_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AuthLog(Base):
    __tablename__ = "auth_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(16), default="")  # 实际认证来源
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    ip: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
