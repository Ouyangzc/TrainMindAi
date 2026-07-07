"""DocumentPage / KnowledgeChunk 仓储。"""

from sqlalchemy import select

from app.models.kb import DocumentPage, KnowledgeChunk
from app.repositories.base import BaseRepository


class DocumentPageRepo(BaseRepository[DocumentPage]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, DocumentPage)

    async def list_by_version(self, document_version_id: int) -> list[DocumentPage]:
        stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_version_id == document_version_id)
            .order_by(DocumentPage.page_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_version(self, document_version_id: int) -> int:
        """删除某版本的解析页，返回删除数量。"""
        pages = await self.list_by_version(document_version_id)
        for p in pages:
            await self.session.delete(p)
        await self.session.flush()
        return len(pages)


class KnowledgeChunkRepo(BaseRepository[KnowledgeChunk]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, KnowledgeChunk)

    async def list_by_version(
        self, knowledge_base_version_id: int, status: str = "active"
    ) -> list[KnowledgeChunk]:
        stmt = (
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.knowledge_base_version_id == knowledge_base_version_id,
                KnowledgeChunk.status == status,
            )
            .order_by(KnowledgeChunk.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_version(self, knowledge_base_version_id: int) -> int:
        stmt = select(KnowledgeChunk).where(
            KnowledgeChunk.knowledge_base_version_id == knowledge_base_version_id
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())
        for c in chunks:
            await self.session.delete(c)
        await self.session.flush()
        return len(chunks)
