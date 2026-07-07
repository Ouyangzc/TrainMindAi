"""检索服务测试。"""

import pytest

from app.services.retrieval import _hybrid_fusion, query_rewrite
from app.vectorstore.base import VectorHit


@pytest.mark.asyncio
async def test_query_rewrite_normalizes() -> None:
    """查询改写：去空格、分词。"""
    result = await query_rewrite("  什么是机器学习  ")
    assert result["normalized_query"] == "什么是机器学习"
    assert len(result["keyword_query"]) > 0


def test_hybrid_fusion_empty() -> None:
    """空结果融合返回空列表。"""
    fused = _hybrid_fusion([], [], 0.6, 0.3, 5)
    assert fused == []


def test_hybrid_fusion_dedup() -> None:
    """融合去重：相同 chunk_id 只保留一次。"""
    vector_hits = [VectorHit(chunk_id=1, score=0.9), VectorHit(chunk_id=2, score=0.8)]
    keyword_hits = [(1, 0.7), (3, 0.6)]

    fused = _hybrid_fusion(vector_hits, keyword_hits, 0.6, 0.3, 5)
    ids = [r["chunk_id"] for r in fused]
    assert len(ids) == len(set(ids))  # 无重复
    assert 1 in ids
    assert 2 in ids
    assert 3 in ids
