"""EmbeddingIndexVersion / KeywordIndexVersion / ChunkEmbedding 仓储。"""

from sqlalchemy import select

from app.models.kb import ChunkEmbedding, EmbeddingIndexVersion, KeywordIndexVersion
from app.repositories.base import BaseRepository


class EmbeddingIndexVersionRepo(BaseRepository[EmbeddingIndexVersion]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, EmbeddingIndexVersion)

    async def get_latest_by_version(
        self, knowledge_base_version_id: int
    ) -> EmbeddingIndexVersion | None:
        stmt = (
            select(EmbeddingIndexVersion)
            .where(
                EmbeddingIndexVersion.knowledge_base_version_id
                == knowledge_base_version_id,
                EmbeddingIndexVersion.status == "ready",
            )
            .order_by(EmbeddingIndexVersion.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class KeywordIndexVersionRepo(BaseRepository[KeywordIndexVersion]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, KeywordIndexVersion)

    async def get_latest_by_version(
        self, knowledge_base_version_id: int
    ) -> KeywordIndexVersion | None:
        stmt = (
            select(KeywordIndexVersion)
            .where(
                KeywordIndexVersion.knowledge_base_version_id
                == knowledge_base_version_id,
                KeywordIndexVersion.status == "ready",
            )
            .order_by(KeywordIndexVersion.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ChunkEmbeddingRepo(BaseRepository[ChunkEmbedding]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, ChunkEmbedding)

    async def delete_by_index_version(self, embedding_index_version_id: int) -> int:
        stmt = select(ChunkEmbedding).where(
            ChunkEmbedding.embedding_index_version_id == embedding_index_version_id
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for r in rows:
            await self.session.delete(r)
        await self.session.flush()
        return len(rows)

    async def upsert_embeddings(
        self,
        embedding_index_version_id: int,
        items: list[tuple[int, list[float]]],
    ) -> None:
        """批量写入向量（INSERT ON CONFLICT，按 (chunk_id, index_version_id) 去重）。"""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        for chunk_id, embedding in items:
            stmt = pg_insert(ChunkEmbedding).values(
                chunk_id=chunk_id,
                embedding_index_version_id=embedding_index_version_id,
                embedding=embedding,
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["chunk_id", "embedding_index_version_id"]
            )
            await self.session.execute(stmt)
        await self.session.flush()
