"""所有 ORM 模型聚合导出，便于 Alembic env.py 一次性 import 触发注册。"""

from app.models.base import Base
from app.models.config_tables import (
    ChunkStrategy,
    PromptTemplate,
    RetrievalStrategyConfig,
)
from app.models.eval import (
    RagEvalCase,
    RagEvalDataset,
    RagEvalResult,
    RagEvalRun,
)
from app.models.kb import (
    ChunkEmbedding,
    DocumentPage,
    EmbeddingIndexVersion,
    KbBuildTask,
    KeywordIndexVersion,
    KnowledgeChunk,
)
from app.models.logs import ModelCallLog, QaRetrievalLog

__all__ = [
    "Base",
    "ChunkStrategy",
    "RetrievalStrategyConfig",
    "PromptTemplate",
    "DocumentPage",
    "EmbeddingIndexVersion",
    "KeywordIndexVersion",
    "KnowledgeChunk",
    "ChunkEmbedding",
    "KbBuildTask",
    "QaRetrievalLog",
    "ModelCallLog",
    "RagEvalDataset",
    "RagEvalCase",
    "RagEvalRun",
    "RagEvalResult",
]
