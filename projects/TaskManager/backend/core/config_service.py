"""
config_service — 配置层服务（模拟 Apollo 配置中心）。

任务树「配置层」数据源：账号/区域/endpoint。
- 生产：Apollo 配置中心热更新
- Demo：DB 表承载（AccountRegion），启动时幂等播种

对外只暴露纯函数式接口，供视图/编排层调用。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── 演示账号/区域配置（模拟 Apollo 发布内容） ──────────────────────

DEMO_ACCOUNT_CONFIG = [
    {
        "account": "生产环境",
        "account_id": "123456789012",
        "regions": [
            {"region": "ap-northeast-1", "endpoint": "https://ec2.ap-northeast-1.amazonaws.com", "cron": "0 2 * * *", "concurrency": 50},
            {"region": "us-east-1", "endpoint": "https://ec2.us-east-1.amazonaws.com", "cron": "0 3 * * *", "concurrency": 50},
            {"region": "eu-west-1", "endpoint": "https://ec2.eu-west-1.amazonaws.com", "cron": "0 5 * * *", "concurrency": 30},
            {"region": "ap-southeast-1", "endpoint": "https://ec2.ap-southeast-1.amazonaws.com", "cron": "0 4 * * *", "concurrency": 30},
        ],
    },
    {
        "account": "预发布环境",
        "account_id": "987654321098",
        "regions": [
            {"region": "ap-northeast-1", "endpoint": "https://ec2.ap-northeast-1.amazonaws.com", "cron": "0 3 * * *", "concurrency": 20},
            {"region": "us-east-1", "endpoint": "https://ec2.us-east-1.amazonaws.com", "cron": "0 4 * * *", "concurrency": 20},
        ],
    },
    {
        "account": "开发环境",
        "account_id": "555666777888",
        "regions": [
            {"region": "ap-northeast-1", "endpoint": "https://ec2.ap-northeast-1.amazonaws.com", "cron": "0 9 * * *", "concurrency": 10},
            {"region": "us-east-1", "endpoint": "https://ec2.us-east-1.amazonaws.com", "cron": "0 10 * * *", "concurrency": 10},
        ],
    },
]


def ensure_config_seeded():
    """幂等播种账号/区域配置（get_or_create）。"""
    from .models import AccountRegion

    created = 0
    for acct in DEMO_ACCOUNT_CONFIG:
        for reg in acct["regions"]:
            _, was_created = AccountRegion.objects.get_or_create(
                account=acct["account"],
                region=reg["region"],
                defaults={
                    "account_id": acct["account_id"],
                    "endpoint": reg.get("endpoint", ""),
                    "cron": reg.get("cron", "0 2 * * *"),
                    "concurrency": reg.get("concurrency", 50),
                    "source": "seed",
                },
            )
            if was_created:
                created += 1
    if created:
        logger.info(f"config_service: seeded {created} account/region configs")
    return created


def list_account_regions(enabled_only: bool = True) -> list[dict]:
    """返回配置层数据（账号 → 区域列表）。"""
    from .models import AccountRegion

    qs = AccountRegion.objects.all()
    if enabled_only:
        qs = qs.filter(enabled=True)

    accounts: dict[str, dict] = {}
    for row in qs:
        entry = accounts.setdefault(
            row.account,
            {"name": row.account, "account_id": row.account_id, "regions": []},
        )
        entry["regions"].append(
            {
                "code": row.region,
                "endpoint": row.endpoint,
                "cron": row.cron,
                "concurrency": row.concurrency,
                "enabled": row.enabled,
                "source": row.source,
            }
        )
    return list(accounts.values())


def get_account_region(account: str, region: str):
    """按账号+区域取配置记录，不存在返回 None。"""
    from .models import AccountRegion

    try:
        return AccountRegion.objects.get(account=account, region=region)
    except AccountRegion.DoesNotExist:
        return None
