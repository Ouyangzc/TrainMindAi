"""RAG 评估表：数据集、用例、运行批次、结果（仅 intra-ai FK）。"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, PkMixin


class RagEvalDataset(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "rag_eval_dataset"

    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF public.course
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RagEvalCase(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "rag_eval_case"

    dataset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("rag_eval_dataset.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    standard_answer: Mapped[str | None] = mapped_column(Text)
    expected_knowledge_point_id: Mapped[int | None] = mapped_column(BigInteger)  # XREF
    expected_sources: Mapped[list | None] = mapped_column(JSONB)
    expected_keywords: Mapped[list | None] = mapped_column(JSONB)
    allow_reject: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    difficulty: Mapped[str | None] = mapped_column(String(16))
    question_type: Mapped[str | None] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RagEvalRun(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "rag_eval_run"

    dataset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("rag_eval_dataset.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_base_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # XREF
    chunk_strategy_version: Mapped[str | None] = mapped_column(String(32))
    retrieval_strategy_version: Mapped[str | None] = mapped_column(String(32))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class RagEvalResult(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "rag_eval_result"

    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("rag_eval_run.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("rag_eval_case.id", ondelete="CASCADE"), nullable=False
    )
    raw_query: Mapped[str | None] = mapped_column(Text)
    normalized_query: Mapped[str | None] = mapped_column(Text)
    hit_knowledge_point: Mapped[bool | None] = mapped_column(Boolean)
    hit_document: Mapped[bool | None] = mapped_column(Boolean)
    hit_page: Mapped[bool | None] = mapped_column(Boolean)
    recall_at_k: Mapped[float | None] = mapped_column(Numeric(5, 4))
    mrr: Mapped[float | None] = mapped_column(Numeric(5, 4))
    answer_correct: Mapped[bool | None] = mapped_column(Boolean)
    citation_correct: Mapped[bool | None] = mapped_column(Boolean)
    reject_correct: Mapped[bool | None] = mapped_column(Boolean)
    failure_reason: Mapped[str | None] = mapped_column(String(32))
