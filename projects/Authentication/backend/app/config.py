"""应用配置。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 基础
    app_name: str = "统一认证中心"
    debug: bool = False
    environment: str = "dev"

    # 安全 / JWT
    # RSA 私钥（PEM）。为空时自动生成并持久化到 backend/.jwt_keys/，开箱即用
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7
    issuer: str = "http://localhost:8099"  # JWT iss 声明（浏览器可达兑底，规范 R1；各环境可覆盖）
    audience: str = "devops-portal"

    # 数据库
    database_url: str = "sqlite:///./auth.db"

    # 身份源（降级链）
    # 逗号分隔，按优先级：如 "okta,ldap,local"
    auth_provider_order: str = "local"
    auth_provider_local_enabled: bool = True
    auth_provider_ldap_enabled: bool = False
    auth_provider_okta_enabled: bool = False

    # LDAP
    ldap_server_uri: str = "ldap://openldap:389"
    ldap_bind_dn: str = "cn=admin,dc=devops,dc=com"
    ldap_bind_password: str = "adminpass"
    ldap_user_search_base: str = "ou=people,dc=devops,dc=com"
    ldap_user_search_filter: str = "(uid={username})"
    ldap_use_tls: bool = False
    ldap_connect_timeout: int = 5

    # Okta（预留）
    okta_issuer: str = ""
    okta_client_id: str = ""
    okta_client_secret: str = ""

    # 门户前端地址（用于 verify 时 302 跳转登录页）
    portal_url: str = "http://localhost:5173"
    # 演示 mock 业务应用地址（网关保护）
    mock_app_url: str = "http://localhost:8001"
    # OIDC Provider 基础地址（用于 openid-configuration 端点拼接）
    oidc_base_url: str = "http://auth-backend:8000"

@lru_cache
def get_settings() -> Settings:
    return Settings()
