"""向量化 + 写向量库 / 登记 embedding_index_version。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.embedding_client import EmbeddingClient
from app.repositories.doc_repo import KnowledgeChunkRepo
from app.repositories.embedding_repo import EmbeddingIndexVersionRepo
from app.vectorstore import get_vector_store


async def run_embedding_pipeline(
    session: AsyncSession,
    embedding_index_version_id: int,
) -> int:
    """对某索引版本的全部 active chunk 执行向量化并写入向量库。返回嵌入数。"""
    embedding_client = EmbeddingClient()
    vector_store = get_vector_store(session)
    chunk_repo = KnowledgeChunkRepo(session)
    emb_idx_repo = EmbeddingIndexVersionRepo(session)

    index_version = await emb_idx_repo.get(embedding_index_version_id)
    if index_version is None:
        raise ValueError(
            f"embedding_index_version not found: {embedding_index_version_id}"
        )

    chunks = await chunk_repo.list_by_version(
        index_version.knowledge_base_version_id
    )
    if not chunks:
        return 0

    texts = [c.chunk_text for c in chunks]
    embeddings = await embedding_client.embed(texts)
    items = list(zip([c.id for c in chunks], embeddings, strict=True))

    await vector_store.upsert(embedding_index_version_id, items)

    index_version.chunk_count = len(items)
    index_version.status = "ready"
    await session.flush()

    return len(items)
