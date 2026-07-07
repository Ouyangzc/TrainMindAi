"""知识库流水线表：解析页、索引版本、切片、向量、构建任务。

指向 public 业务表的列均为松耦合普通列（无跨 schema 外键）。
ai schema 内部的外键保留（chunk_embedding -> knowledge_chunk / embedding_index_version）。
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import Base, CreatedAtMixin, PkMixin

EMBEDDING_DIM = settings.embedding_dim


class DocumentPage(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "document_page"

    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF public.document
    document_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    text: Mapped[str | None] = mapped_column(Text)
    tables_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    images_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class EmbeddingIndexVersion(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "embedding_index_version"

    knowledge_base_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_store: Mapped[str] = mapped_column(String(32), nullable=False)
    collection_name: Mapped[str | None] = mapped_column(String(128))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="building")


class KeywordIndexVersion(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "keyword_index_version"

    knowledge_base_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    index_engine: Mapped[str] = mapped_column(String(32), nullable=False, default="pg_fts")
    analyzer: Mapped[str | None] = mapped_column(String(64))
    index_name: Mapped[str | None] = mapped_column(String(128))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="building")


class KnowledgeChunk(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "knowledge_chunk"

    knowledge_base_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    chapter_id: Mapped[int | None] = mapped_column(BigInteger)  # XREF
    knowledge_point_id: Mapped[int | None] = mapped_column(BigInteger)  # XREF
    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    document_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(512))
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_type: Mapped[str | None] = mapped_column(String(32))
    chunk_strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    tsv: Mapped[str | None] = mapped_column(TSVECTOR)  # jieba 预分词后写入
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class ChunkEmbedding(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "chunk_embedding"
    __table_args__ = (
        UniqueConstraint(
            "chunk_id",
            "embedding_index_version_id",
            name="uq_chunk_embedding_chunk_index_version",
        ),
    )

    chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge_chunk.id", ondelete="CASCADE"), nullable=False
    )
    embedding_index_version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("embedding_index_version.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)


class KbBuildTask(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "kb_build_task"

    knowledge_base_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    current_step: Mapped[str | None] = mapped_column(String(64))
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
