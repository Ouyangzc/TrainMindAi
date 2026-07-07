"""向量库抽象接口。MVP 用 pgvector 实现，规模上来切 Qdrant 不改业务代码。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorHit:
    chunk_id: int
    score: float


class VectorStore(ABC):
    """向量库统一接口。"""

    @abstractmethod
    async def upsert(
        self,
        embedding_index_version_id: int,
        items: list[tuple[int, list[float]]],
    ) -> None:
        """写入/更新向量。items: [(chunk_id, embedding), ...]"""

    @abstractmethod
    async def search(
        self,
        embedding_index_version_id: int,
        query_vector: list[float],
        top_k: int,
        metadata_filter: dict | None = None,
    ) -> list[VectorHit]:
        """余弦近邻检索。"""

    @abstractmethod
    async def delete(self, embedding_index_version_id: int) -> None:
        """删除某索引版本的全部向量。"""
