"""资料文件解析任务模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocumentParseTask(Base):
    """映射 Java 业务库 public.document_parse_task。"""

    __tablename__ = "document_parse_task"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    current_step: Mapped[str | None] = mapped_column(String(64))
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[str] = mapped_column(String(1), nullable=False, default="0")
    create_by: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    update_by: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    remark: Mapped[str | None] = mapped_column(String(500))
