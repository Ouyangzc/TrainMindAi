"""向量库工厂：按配置选择实现。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.vectorstore.base import VectorHit, VectorStore
from app.vectorstore.pgvector_store import PgVectorStore


def get_vector_store(session: AsyncSession) -> VectorStore:
    if settings.vector_store == "pgvector":
        return PgVectorStore(session)
    raise NotImplementedError(f"未支持的向量库: {settings.vector_store}")


__all__ = ["VectorStore", "VectorHit", "get_vector_store"]
