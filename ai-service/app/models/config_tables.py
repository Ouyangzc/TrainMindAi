"""配置类表：chunk 策略、检索策略、prompt 模板。"""

from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, PkMixin


class ChunkStrategy(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "chunk_strategy"

    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_method: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_size: Mapped[int | None] = mapped_column(Integer)
    chunk_overlap: Mapped[int | None] = mapped_column(Integer)
    merge_rule: Mapped[str | None] = mapped_column(String(255))
    split_rule: Mapped[str | None] = mapped_column(String(255))
    metadata_rule: Mapped[str | None] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class RetrievalStrategyConfig(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "retrieval_strategy_config"

    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    vector_top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    keyword_top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    final_top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    vector_weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.600)
    keyword_weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.300)
    metadata_weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.100)
    min_score_threshold: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.0)
    rerank_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class PromptTemplate(Base, PkMixin, CreatedAtMixin):
    __tablename__ = "prompt_template"

    prompt_code: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scenario: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_content: Mapped[str] = mapped_column(Text, nullable=False)
    output_schema: Mapped[dict | None] = mapped_column(JSONB)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger)
