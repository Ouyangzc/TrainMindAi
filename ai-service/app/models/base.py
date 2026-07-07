"""ORM 基类。所有 AI 自有表落在 ai schema。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

# 统一命名约定，便于 Alembic 生成稳定的约束/索引名
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.db_schema, naming_convention=NAMING_CONVENTION)


class PkMixin:
    """bigserial 主键（对齐 RuoYi）。"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
