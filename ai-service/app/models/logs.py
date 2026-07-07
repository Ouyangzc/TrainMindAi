"""运行日志：检索日志、模型调用日志（均弱引用，无 FK，便于长期留存审计）。"""

from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, PkMixin


class QaRetrievalLog(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "qa_retrieval_log"

    session_id: Mapped[int | None] = mapped_column(BigInteger)  # XREF public.qa_session
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF public.qa_message
    raw_query: Mapped[str | None] = mapped_column(Text)
    normalized_query: Mapped[str | None] = mapped_column(Text)
    keyword_query: Mapped[str | None] = mapped_column(Text)
    semantic_query: Mapped[str | None] = mapped_column(Text)
    retrieval_strategy: Mapped[str | None] = mapped_column(String(64))
    knowledge_base_version_id: Mapped[int | None] = mapped_column(BigInteger)
    chunk_id: Mapped[int | None] = mapped_column(BigInteger)  # 弱引用，不设 FK
    rank_no: Mapped[int | None] = mapped_column(Integer)
    vector_score: Mapped[float | None] = mapped_column(Numeric(8, 6))
    keyword_score: Mapped[float | None] = mapped_column(Numeric(8, 6))
    metadata_score: Mapped[float | None] = mapped_column(Numeric(8, 6))
    final_score: Mapped[float | None] = mapped_column(Numeric(8, 6))
    rerank_score: Mapped[float | None] = mapped_column(Numeric(8, 6))
    retrieval_channel: Mapped[str | None] = mapped_column(String(16))
    matched_terms: Mapped[dict | None] = mapped_column(JSONB)
    chunk_strategy_version: Mapped[str | None] = mapped_column(String(32))
    used_in_prompt: Mapped[bool | None] = mapped_column(Boolean, default=False)
    prompt_position: Mapped[int | None] = mapped_column(Integer)
    reject_reason: Mapped[str | None] = mapped_column(String(64))


class ModelCallLog(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "model_call_log"

    scenario: Mapped[str | None] = mapped_column(String(32))
    provider: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    request_id: Mapped[str | None] = mapped_column(String(64))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
