"""Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 认证 ----------
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: str
    department: str
    phone: str
    is_active: bool
    is_admin: bool
    source: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class VerifyResponse(BaseModel):
    code: int
    user: UserOut | None = None


class SsoUrlRequest(BaseModel):
    app_id: str
    redirect: str = ""


# ---------- 应用注册表 ----------
class AppCreate(BaseModel):
    app_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    icon: str = "AppstoreOutlined"
    home_url: str = ""
    sso_type: str = "token"
    # 接入方式：gateway(经统一网关) / direct(业务自验签 JWKS)
    access_mode: str = "gateway"
    enabled: bool = True
    sort_order: int = 0


class AppUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    home_url: str | None = None
    sso_type: str | None = None
    access_mode: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class AppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: str
    name: str
    description: str
    icon: str
    home_url: str
    sso_type: str
    access_mode: str
    client_id: str | None = None
    enabled: bool
    sort_order: int


class AppCreateOut(AppOut):
    """创建响应：client_secret 仅在此一次性返回，之后不再暴露。"""
    client_secret: str | None = None


# ---------- 用户管理 ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = ""
    email: str = ""
    department: str = ""
    phone: str = ""
    is_active: bool = True
    is_admin: bool = False
    source: str = "local"


class UserUpdate(BaseModel):
    password: str | None = None
    display_name: str | None = None
    email: str | None = None
    department: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    source: str | None = None


# ---------- 系统 ----------
class ProviderStatus(BaseModel):
    name: str
    order: int
    available: bool
    note: str = ""


class SystemHealth(BaseModel):
    status: str
    app: str
    version: str
    providers: list[ProviderStatus] = []


class AuthLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    source: str
    success: bool
    ip: str
    detail: str
    created_at: datetime
