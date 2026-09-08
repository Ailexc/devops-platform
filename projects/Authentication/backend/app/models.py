"""ORM 模型：用户 / 应用注册 / 认证日志。"""
import json
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
from sqlalchemy.types import TypeDecorator

from .db import Base


class JSONText(TypeDecorator):
    """把 list/dict 存为 JSON 文本列；ORM 读写自动序列化/反序列化。"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return value
        return value


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
    # 演示分组索引（JSON 数组，如 ["cloud-manager","workflow-center"]）：
    # 仅用于登录页下拉按系统分组展示的演示便利，非用户模型（用户真正归属是组织 department）
    demo_systems: Mapped[list[str]] = mapped_column(JSONText, default=list)
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
    # ---- OIDC 客户端配置（P0 改造新增） ----
    # redirect_uri 白名单（JSON 数组，精确匹配；兼容旧数据：为空时回退到 home_url 精确匹配）
    redirect_uris: Mapped[list[str]] = mapped_column(JSONText, default=list)
    # 允许的 scope（JSON 数组，如 ["openid","profile","email"]）
    allowed_scopes: Mapped[list[str]] = mapped_column(
        JSONText, default=lambda: ["openid", "profile", "email"]
    )
    # 是否公共客户端（无 client_secret，必须 PKCE；SPA 直连场景）
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    # token 端点客户端认证方式：client_secret_post / client_secret_basic / none
    token_endpoint_auth_method: Mapped[str] = mapped_column(String(32), default="client_secret_post")
    # 允许的 grant_types（JSON 数组，如 ["authorization_code","refresh_token"]）
    grant_types: Mapped[list[str]] = mapped_column(
        JSONText, default=lambda: ["authorization_code", "refresh_token"]
    )
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


class AuthCode(Base):
    """OIDC 一次性授权码（入库存储：一次性、短时效、绑定客户端与 PKCE）。"""

    __tablename__ = "auth_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(512), default="")
    # PKCE：code_challenge + method，token 时用 code_verifier 验证
    code_challenge: Mapped[str] = mapped_column(String(128), default="")
    code_challenge_method: Mapped[str] = mapped_column(String(16), default="S256")
    nonce: Mapped[str] = mapped_column(String(128), default="")  # id_token 防重放
    scope: Mapped[str] = mapped_column(String(256), default="openid")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)  # 一次性：已使用即作废
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RefreshToken(Base):
    """OIDC refresh token 存储（轮换 + 复用检测 + 撤销）。"""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    family_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    replaced_by: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 轮换后指向新 token_hash
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
