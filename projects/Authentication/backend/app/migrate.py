"""轻量 schema 迁移：Base.metadata.create_all 不会给「已存在的表」加列。

本模块在启动时为老库补齐新增列（SQLite / PostgreSQL 通用 ALTER 语法）。
新表（auth_codes / refresh_tokens）由 create_all 直接创建。
"""
import logging

from sqlalchemy import inspect, text

from .db import engine

logger = logging.getLogger("auth.migrate")

# 表 -> 需要补齐的列（列名 -> ALTER 类型定义；DEFAULT 为字符串字面量）
# 注意：PostgreSQL 对 boolean 默认值要求布尔字面量（FALSE/TRUE），不能用 0/1（integer）。
_ADD_COLUMNS: dict[str, dict[str, str]] = {
    "app_registrations": {
        "redirect_uris": "TEXT DEFAULT '[]'",
        "allowed_scopes": "TEXT DEFAULT '[\"openid\",\"profile\",\"email\"]'",
        "is_public": "BOOLEAN DEFAULT FALSE",
        "token_endpoint_auth_method": "VARCHAR(32) DEFAULT 'client_secret_post'",
        "grant_types": "TEXT DEFAULT '[\"authorization_code\",\"refresh_token\"]'",
    },
    "users": {
        "demo_systems": "TEXT DEFAULT '[]'",
    },
}


def ensure_schema() -> None:
    """为已存在的老表补齐新增列。新表由 create_all 创建。

    每个列独立事务：单列失败只告警，不影响其他列（避免 PostgreSQL 整事务回滚）。
    """
    try:
        inspector = inspect(engine)
        existing = {
            tname: {c["name"] for c in inspector.get_columns(tname)}
            for tname in inspector.get_table_names()
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("schema 迁移：读取表结构失败（可忽略）: %s", exc)
        return
    for table, cols in _ADD_COLUMNS.items():
        if table not in existing:
            continue
        for col, ddl in cols.items():
            if col in existing[table]:
                continue
            try:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                existing[table].add(col)
                logger.info("schema 迁移：%s 表补列 %s", table, col)
            except Exception as exc:  # noqa: BLE001
                logger.warning("schema 迁移：%s.%s 补列失败: %s", table, col, exc)
