"""pgvector 实现（MVP）。向量存 ai.chunk_embedding，余弦检索用 <=> 运算符。"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb import ChunkEmbedding
from app.vectorstore.base import VectorHit, VectorStore


class PgVectorStore(VectorStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        embedding_index_version_id: int,
        items: list[tuple[int, list[float]]],
    ) -> None:
        """写入/更新向量（逐行 INSERT ON CONFLICT DO NOTHING）。"""
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

    async def search(
        self,
        embedding_index_version_id: int,
        query_vector: list[float],
        top_k: int,
        metadata_filter: dict | None = None,
    ) -> list[VectorHit]:
        """余弦近邻检索。"""
        # 基础条件
        conditions = [
            "ce.embedding_index_version_id = :idx_ver_id",
            "kc.status = 'active'",
        ]
        params: dict = {
            "idx_ver_id": embedding_index_version_id,
            "query_vec": query_vector,
        }

        # 可选 metadata 过滤（course_id, document_id 等）
        if metadata_filter:
            for key, value in metadata_filter.items():
                param_name = f"mf_{key}"
                conditions.append(f"kc.{key} = :{param_name}")
                params[param_name] = value

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT ce.chunk_id AS chunk_id,
                   1 - (ce.embedding <=> :query_vec) AS score
            FROM ai.chunk_embedding ce
            JOIN ai.knowledge_chunk kc ON kc.id = ce.chunk_id
            WHERE {where_clause}
            ORDER BY ce.embedding <=> :query_vec
            LIMIT :top_k
        """
        result = await self.session.execute(
            text(sql), {**params, "top_k": top_k}
        )
        rows = result.fetchall()
        return [VectorHit(chunk_id=row[0], score=float(row[1])) for row in rows]

    async def delete(self, embedding_index_version_id: int) -> None:
        """删除某索引版本的全部向量。"""
        stmt = select(ChunkEmbedding).where(
            ChunkEmbedding.embedding_index_version_id == embedding_index_version_id
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for r in rows:
            await self.session.delete(r)
        await self.session.flush()
