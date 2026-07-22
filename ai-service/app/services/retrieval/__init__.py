"""检索：query_rewrite / vector / keyword / hybrid / scorer。

检索全过程逐条写 qa_retrieval_log。
"""

import jieba
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.embedding_client import EmbeddingClient
from app.models.kb import KnowledgeChunk
from app.models.logs import QaRetrievalLog
from app.repositories.config_repo import RetrievalStrategyConfigRepo
from app.repositories.embedding_repo import EmbeddingIndexVersionRepo
from app.repositories.log_repo import QaRetrievalLogRepo
from app.vectorstore import get_vector_store
from app.vectorstore.base import VectorHit


async def query_rewrite(raw: str) -> dict:
    """查询改写：基本规范化 + 关键词提取。"""
    normalized = raw.strip().replace("\n", " ")
    words = list(jieba.cut(normalized))
    keyword_query = " ".join(w for w in words if len(w) > 1)
    return {
        "raw_query": raw,
        "normalized_query": normalized,
        "keyword_query": keyword_query,
        "semantic_query": normalized,
    }


async def _keyword_search(
    session: AsyncSession,
    keyword_query: str,
    kb_version_id: int,
    top_k: int,
) -> list[tuple[int, float]]:
    """PG 全文检索（tsvector 列）。"""
    if not keyword_query.strip():
        return []
    stmt = text("""
        SELECT id, ts_rank(tsv, plainto_tsquery('simple', :kw)) AS score
        FROM ai.knowledge_chunk
        WHERE knowledge_base_version_id = :kb_ver_id
          AND status = 'active'
          AND tsv @@ plainto_tsquery('simple', :kw)
        ORDER BY score DESC
        LIMIT :top_k
    """)
    result = await session.execute(
        stmt,
        {"kw": keyword_query, "kb_ver_id": kb_version_id, "top_k": top_k},
    )
    return [(row[0], float(row[1])) for row in result.fetchall()]


async def _vector_search(
    session: AsyncSession,
    embedding_index_version_id: int,
    semantic_query: str,
    top_k: int,
    metadata_filter: dict | None = None,
) -> list[VectorHit]:
    """向量近邻检索。"""
    embedding_client = EmbeddingClient()
    query_vec = (await embedding_client.embed([semantic_query]))[0]
    vector_store = get_vector_store(session)
    return await vector_store.search(
        embedding_index_version_id=embedding_index_version_id,
        query_vector=query_vec,
        top_k=top_k,
        metadata_filter=metadata_filter,
    )


def _hybrid_fusion(
    vector_hits: list[VectorHit],
    keyword_hits: list[tuple[int, float]],
    vector_weight: float,
    keyword_weight: float,
    final_top_k: int,
) -> list[dict]:
    """混合融合：加权分数 + 去重。"""
    score_map: dict[int, float] = {}
    for hit in vector_hits:
        score_map[hit.chunk_id] = (
            score_map.get(hit.chunk_id, 0) + hit.score * vector_weight
        )
    for chunk_id, kw_score in keyword_hits:
        score_map[chunk_id] = (
            score_map.get(chunk_id, 0) + kw_score * keyword_weight
        )
    sorted_ids = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    return [
        {"chunk_id": cid, "final_score": score}
        for cid, score in sorted_ids[:final_top_k]
    ]


async def hybrid_retrieve(
    session: AsyncSession,
    question: str,
    kb_version_id: int,
    course_id: int | None = None,
    top_k: int | None = None,
    session_id: int | None = None,
    message_id: int | None = None,
) -> tuple[str, list[dict], int | None]:
    """混合检索入口。

    返回 (normalized_query, results[], retrieval_log_ref_id)。

    results 形如：
        [{"chunk_id": int, "final_score": float, "text": str,
          "source_file": str|None, "page_start": int|None, "page_end": int|None}, ...]
    """
    rewritten = await query_rewrite(question)
    kw_query = rewritten["keyword_query"]
    semantic_query = rewritten["semantic_query"]

    config_repo = RetrievalStrategyConfigRepo(session)
    strategy = await config_repo.get_default()
    v_top_k = top_k or (strategy.vector_top_k if strategy else 20)
    kw_top_k = top_k or (strategy.keyword_top_k if strategy else 20)
    final_top_k = top_k or (strategy.final_top_k if strategy else 5)
    v_weight = float(strategy.vector_weight) if strategy else 0.6
    kw_weight = float(strategy.keyword_weight) if strategy else 0.3

    emb_idx_repo = EmbeddingIndexVersionRepo(session)
    emb_idx = await emb_idx_repo.get_latest_by_version(kb_version_id)

    vector_hits: list[VectorHit] = []
    keyword_hits: list[tuple[int, float]] = []

    if emb_idx:
        filter_dict = {"course_id": course_id} if course_id else None
        vector_hits = await _vector_search(
            session, emb_idx.id, semantic_query, v_top_k, filter_dict
        )

    keyword_hits = await _keyword_search(
        session, kw_query, kb_version_id, kw_top_k
    )

    fused = _hybrid_fusion(
        vector_hits, keyword_hits, v_weight, kw_weight, final_top_k
    )

    if fused:
        stmt = select(
            KnowledgeChunk.id,
            KnowledgeChunk.chunk_text,
            KnowledgeChunk.document_id,
            KnowledgeChunk.document_version_id,
            KnowledgeChunk.source_file,
            KnowledgeChunk.page_start,
            KnowledgeChunk.page_end,
            KnowledgeChunk.metadata_json,
        ).where(KnowledgeChunk.id.in_([r["chunk_id"] for r in fused]))
        result = await session.execute(stmt)
        chunk_map = {row[0]: row for row in result.fetchall()}
        for r in fused:
            row = chunk_map.get(r["chunk_id"])
            if row:
                r["text"] = row[1]
                r["document_id"] = row[2]
                r["document_version_id"] = row[3]
                r["source_file"] = row[4]
                r["page_start"] = row[5]
                r["page_end"] = row[6]
                metadata = row[7] or {}
                r["section_title"] = metadata.get("section_title") or metadata.get("title")
            else:
                r["text"] = ""

    log_repo = QaRetrievalLogRepo(session)
    retrieval_log_id: int | None = None
    for rank, r in enumerate(fused):
        log_entry = await log_repo.add(
            QaRetrievalLog(
                session_id=session_id,
                message_id=message_id or 0,
                raw_query=rewritten["raw_query"],
                normalized_query=rewritten["normalized_query"],
                keyword_query=rewritten["keyword_query"],
                semantic_query=rewritten["semantic_query"],
                retrieval_strategy="hybrid",
                knowledge_base_version_id=kb_version_id,
                chunk_id=r["chunk_id"],
                rank_no=rank + 1,
                final_score=r["final_score"],
                used_in_prompt=rank < final_top_k,
            )
        )
        if retrieval_log_id is None:
            retrieval_log_id = log_entry.id
    await session.flush()

    return rewritten["normalized_query"], fused, retrieval_log_id
