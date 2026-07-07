"""数据访问层（DB 仓储）。"""

from app.repositories.base import BaseRepository
from app.repositories.config_repo import (
    ChunkStrategyRepo,
    PromptTemplateRepo,
    RetrievalStrategyConfigRepo,
)
from app.repositories.doc_repo import DocumentPageRepo, KnowledgeChunkRepo
from app.repositories.embedding_repo import (
    ChunkEmbeddingRepo,
    EmbeddingIndexVersionRepo,
    KeywordIndexVersionRepo,
)
from app.repositories.eval_repo import (
    RagEvalCaseRepo,
    RagEvalDatasetRepo,
    RagEvalResultRepo,
    RagEvalRunRepo,
)
from app.repositories.log_repo import ModelCallLogRepo, QaRetrievalLogRepo
from app.repositories.task_repo import KbBuildTaskRepo

__all__ = [
    "BaseRepository",
    "KbBuildTaskRepo",
    "DocumentPageRepo",
    "KnowledgeChunkRepo",
    "EmbeddingIndexVersionRepo",
    "KeywordIndexVersionRepo",
    "ChunkEmbeddingRepo",
    "QaRetrievalLogRepo",
    "ModelCallLogRepo",
    "ChunkStrategyRepo",
    "RetrievalStrategyConfigRepo",
    "PromptTemplateRepo",
    "RagEvalDatasetRepo",
    "RagEvalCaseRepo",
    "RagEvalRunRepo",
    "RagEvalResultRepo",
]

