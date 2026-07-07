"""PgVectorStore 单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.vectorstore.pgvector_store import PgVectorStore


@pytest.mark.asyncio
async def test_search_calls_execute(mock_session) -> None:  # noqa: ANN001
    """search 方法应执行 SQL 并返回正确结构。"""
    store = PgVectorStore(mock_session)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (1, 0.95),
        (2, 0.87),
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    hits = await store.search(
        embedding_index_version_id=1,
        query_vector=[0.1] * 1024,
        top_k=5,
    )
    assert len(hits) == 2
    assert hits[0].chunk_id == 1
    assert abs(hits[0].score - 0.95) < 0.001
    assert hits[1].chunk_id == 2
