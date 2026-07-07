"""Alembic 环境：async engine + ai schema。

- 业务表全部在 ai schema；alembic_version 表也放 ai。
- 在线迁移前确保 ai schema 存在（否则无法创建版本表）。
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings

# 触发所有模型注册到 Base.metadata
from app.models import Base  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
DB_SCHEMA = settings.db_schema


def _configure(connection: Connection | None = None, url: str | None = None) -> None:
    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        version_table_schema=DB_SCHEMA,
        include_schemas=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"} if url else {},
    )


def run_migrations_offline() -> None:
    """离线模式：仅生成 SQL（无需活库）。先输出建 schema。"""
    _configure(url=settings.database_url)
    with context.begin_transaction():
        context.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}")
        context.run_migrations()


def _do_run(connection: Connection) -> None:
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run)
        await connection.commit()
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
