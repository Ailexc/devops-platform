"""身份源抽象层 + 降级链（本项目核心设计）。

设计要点：
- Authenticator 抽象接口：authenticate(username, password) -> UserProfile
- 三种实现：LocalAuthenticator（本地库）/ LdapAuthenticator（LDAP bind）/ OktaAuthenticator（预留 OIDC）
- AuthProviderChain：按配置顺序尝试，身份源「不可用」时自动降级到下一个
- 安全边界：认证失败（用户不存在/密码错）不降级，只有「身份源不可用」才降级
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import User
from ..security import verify_password

logger = logging.getLogger("auth.providers")

settings = get_settings()


# ---------- 异常（区分失败语义） ----------
class AuthError(Exception):
    """认证相关错误基类。"""


class UserNotFound(AuthError):
    """用户在身份源中不存在。不降级，直接失败。"""


class AuthenticationFailed(AuthError):
    """用户名或密码错误。不降级，直接失败。"""


class AuthProviderUnavailable(AuthError):
    """身份源本身不可用（网络/超时/宕机/未配置）。触发降级。"""


# ---------- 标准化返回 ----------
@dataclass
class UserProfile:
    """屏蔽不同身份源差异的标准化用户信息。"""

    username: str
    display_name: str = ""
    email: str = ""
    department: str = ""
    phone: str = ""
    source: str = "local"  # 实际认证来源，用于审计
    groups: list[str] = field(default_factory=list)


# ---------- 抽象 ----------
class Authenticator(ABC):
    name: str = "abstract"

    @abstractmethod
    def is_available(self) -> bool:
        """探活：身份源是否可用（决定是否跳过 / 降级）。"""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> UserProfile:
        """校验用户名/密码，成功返回 UserProfile，失败抛 AuthError 子类。"""


# ---------- 实现 1：本地用户库 ----------
class LocalAuthenticator(Authenticator):
    name = "local"

    def __init__(self, db: Session):
        self.db = db
        self.enabled = settings.auth_provider_local_enabled

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        # 有至少一个启用的本地用户才认为可用（有数据可认证）
        return self.db.query(User).filter(User.is_active.is_(True)).count() > 0

    def authenticate(self, username: str, password: str) -> UserProfile:
        if not self.enabled:
            raise AuthProviderUnavailable("本地身份源未启用")
        user = self.db.query(User).filter(User.username == username).first()
        if user is None:
            raise UserNotFound(f"用户 {username} 在本地身份源不存在")
        if not user.is_active:
            raise AuthenticationFailed("用户已被禁用")
        if not verify_password(password, user.password_hash):
            raise AuthenticationFailed("密码错误")
        return UserProfile(
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            department=user.department,
            phone=user.phone,
            source="local",
        )


# ---------- 实现 2：LDAP ----------
class LdapAuthenticator(Authenticator):
    name = "ldap"

    def __init__(self):
        self.enabled = settings.auth_provider_ldap_enabled

    def _server(self):
        from ldap3 import Server

        return Server(
            settings.ldap_server_uri,
            connect_timeout=settings.ldap_connect_timeout,
            use_ssl=settings.ldap_use_tls,
        )

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            from ldap3 import ALL, Connection

            conn = Connection(
                self._server(), user=settings.ldap_bind_dn,
                password=settings.ldap_bind_password, auto_bind=True,
            )
            conn.unbind()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("LDAP 探活失败: %s", exc)
            return False

    def authenticate(self, username: str, password: str) -> UserProfile:
        if not self.enabled:
            raise AuthProviderUnavailable("LDAP 身份源未启用")
        try:
            from ldap3 import Connection

            # 第 1 步：服务账号 bind + 按 uid 搜索用户，得到 DN
            conn = Connection(
                self._server(), user=settings.ldap_bind_dn,
                password=settings.ldap_bind_password, auto_bind=True,
            )
            filter_str = settings.ldap_user_search_filter.format(username=username)
            conn.search(
                settings.ldap_user_search_base,
                filter_str,
                attributes=["uid", "cn", "mail", "departmentNumber", "displayName"],
            )
            if not conn.entries:
                conn.unbind()
                raise UserNotFound(f"用户 {username} 在 LDAP 不存在")

            entry = conn.entries[0]
            user_dn = entry.entry_dn
            # 第 2 步：用用户 DN + 密码 bind，成功即密码正确
            # 手动 bind 并区分结果：返回码 49(LDAP_INVALID_CREDENTIALS)=认证失败(不降级)；
            # 其他(连接/网络)=身份源不可用(降级)
            user_conn = Connection(self._server(), user=user_dn, password=password, auto_bind=False)
            bound = user_conn.bind()
            bind_result = user_conn.result or {}
            bind_desc = bind_result.get("description") or bind_result.get("message") or ""
            user_conn.unbind()
            conn.unbind()
            if not bound:
                if bind_result.get("result") == 49:  # LDAP_INVALID_CREDENTIALS
                    raise AuthenticationFailed("密码错误")
                raise AuthProviderUnavailable(f"LDAP bind 失败: {bind_desc}")

            return UserProfile(
                username=username,
                display_name=str(entry.displayName.value or entry.cn.value or username),
                email=str(entry.mail.value or ""),
                department=str(entry.departmentNumber.value or ""),
                source="ldap",
            )
        except (UserNotFound, AuthenticationFailed):
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("LDAP 认证不可用: %s", exc)
            raise AuthProviderUnavailable(f"LDAP 认证不可用: {exc}") from exc


# ---------- 实现 3：Okta（预留 OIDC） ----------
class OktaAuthenticator(Authenticator):
    """预留实现。Demo 环境无真实 Okta，未配置时 is_available=False。

    接真实 Okta / 自建 mock OIDC Provider 时，在此实现 OIDC 授权码流：
    /authorize -> code -> /token -> userinfo，再映射为 UserProfile。
    """

    name = "okta"

    def __init__(self):
        self.enabled = settings.auth_provider_okta_enabled

    def is_available(self) -> bool:
        return self.enabled and bool(settings.okta_issuer)

    def authenticate(self, username: str, password: str) -> UserProfile:
        raise AuthProviderUnavailable("Okta 身份源未配置（Demo 预留）")


# ---------- 降级链 ----------
class AuthProviderChain:
    """按配置顺序尝试多个身份源，身份源不可用时自动降级。"""

    def __init__(self, providers: list[Authenticator]):
        self.providers = providers

    def authenticate(self, username: str, password: str) -> UserProfile:
        last_error: AuthError | None = None
        for provider in self.providers:
            if not provider.is_available():
                logger.info("[降级链] %s 不可用，跳过", provider.name)
                continue
            try:
                profile = provider.authenticate(username, password)
                logger.info("[降级链] %s 认证成功，来源=%s", username, provider.name)
                return profile
            except (UserNotFound, AuthenticationFailed) as exc:
                # 认证失败：不降级，直接返回（安全边界）
                raise exc
            except AuthProviderUnavailable as exc:
                logger.warning("[降级链] %s 认证异常，降级到下一个身份源: %s", provider.name, exc)
                last_error = exc
                continue
        if last_error is not None:
            raise AuthProviderUnavailable(f"所有身份源均不可用: {last_error}")
        raise AuthenticationFailed("没有可用的身份源")


def build_provider_chain(db: Session) -> AuthProviderChain:
    """根据配置构建降级链。order 形如 "okta,ldap,local"（优先级从高到低）。"""
    registry = {
        "local": LocalAuthenticator(db),
        "ldap": LdapAuthenticator(),
        "okta": OktaAuthenticator(),
    }
    order = [s.strip() for s in settings.auth_provider_order.split(",") if s.strip()]
    # 补齐未在 order 中声明的已启用身份源（追加到末尾）
    for name in registry:
        if name not in order:
            order.append(name)
    providers = [registry[name] for name in order if name in registry]
    return AuthProviderChain(providers)


def sync_local_user(db: Session, profile: UserProfile) -> User:
    """把身份源认证成功的用户投影到本地 users 表（以 username 为键 upsert）。

    设计：身份源负责「校验」，本地表作为「用户仓库/投影」，
    保证 JWT 里有稳定的本地 user id，也便于权限中心等下游系统引用。
    """
    user = db.query(User).filter(User.username == profile.username).first()
    if user is None:
        user = User(
            username=profile.username,
            display_name=profile.display_name,
            email=profile.email,
            department=profile.department,
            phone=profile.phone,
            source=profile.source,
            is_active=True,
        )
        db.add(user)
    else:
        # 仅更新身份源带来的权威字段，不覆盖本地管理字段
        user.display_name = profile.display_name or user.display_name
        user.email = profile.email or user.email
        user.department = profile.department or user.department
        user.source = profile.source
    db.commit()
    db.refresh(user)
    return user
