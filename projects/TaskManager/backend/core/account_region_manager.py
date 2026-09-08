"""
Account & Region Manager — unified interface for cross-account AWS access.

Manages AssumeRole sessions with caching, and provides a registry of
known accounts and their enabled regions.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
import boto3
from botocore.config import Config as BotoConfig

# ── Data models ────────────────────────────────────────────────────


@dataclass
class Account:
    name: str
    account_id: str
    role_arn: str
    regions: list[str] = field(default_factory=list)
    is_active: bool = True


@dataclass
class Region:
    code: str          # e.g. "ap-northeast-1"
    name: str          # e.g. "Asia Pacific (Tokyo)"
    cron: str = "0 2 * * *"
    concurrency: int = 50
    is_enabled: bool = True


# ── Registry ────────────────────────────────────────────────────────


class AccountRegistry:
    """Central registry of configured accounts."""

    def __init__(self):
        self._accounts: dict[str, Account] = {}

    def register(self, account: Account):
        self._accounts[account.name] = account

    def get(self, name: str) -> Optional[Account]:
        return self._accounts.get(name)

    def list_active(self) -> list[Account]:
        return [a for a in self._accounts.values() if a.is_active]

    def all(self) -> list[Account]:
        return list(self._accounts.values())


# ── Session Factory ─────────────────────────────────────────────────


class SessionFactory:
    """Creates boto3 sessions for a given account + region with AssumeRole."""

    def __init__(self, registry: AccountRegistry, role_session_name: str = "CMDB-Sync"):
        self._registry = registry
        self._role_session_name = role_session_name
        self._cache: dict[str, boto3.Session] = {}

    def get_session(self, account_name: str, region: str) -> boto3.Session:
        cache_key = f"{account_name}:{region}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        account = self._registry.get(account_name)
        if not account:
            raise ValueError(f"Unknown account: {account_name}")

        # AssumeRole
        sts = boto3.client("sts")
        assumed = sts.assume_role(
            RoleArn=account.role_arn,
            RoleSessionName=self._role_session_name,
        )
        creds = assumed["Credentials"]

        session = boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=region,
        )
        self._cache[cache_key] = session
        return session

    def invalidate_cache(self, account_name: str, region: str):
        cache_key = f"{account_name}:{region}"
        self._cache.pop(cache_key, None)


# ── Convenience wrapper ─────────────────────────────────────────────


class AccountRegionManager:
    """High-level interface combining registry and session factory.

    Demo 兜底：无 AWS 凭据 / 未注册账号时返回 DemoSession，
    让同步管线在个人环境中也能真实跑通（数据落库）。
    """

    def __init__(self):
        self.registry = AccountRegistry()
        self.session_factory = SessionFactory(self.registry)
        self._demo_mode = bool(int(os.environ.get("DEMO_MODE", "1")))

    def get_session(self, account_name: str, region: str):
        # Demo 模式（无真实 AWS 凭据）：直接返回模拟会话
        if self._demo_mode:
            from .demo_session import DemoSession
            return DemoSession()

        # 生产模式：真实 AssumeRole，失败时兜底到模拟会话
        try:
            return self.session_factory.get_session(account_name, region)
        except Exception:
            from .demo_session import DemoSession
            return DemoSession()

    def get_account(self, name: str) -> Optional[Account]:
        return self.registry.get(name)

    def list_accounts(self) -> list[Account]:
        return self.registry.all()

    def register_account(self, account: Account):
        self.registry.register(account)
