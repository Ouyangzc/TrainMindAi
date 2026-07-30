"""检索：query_rewrite / vector / keyword / hybrid / scorer。

检索全过程逐条写 qa_retrieval_log。
"""

import re
from math import sqrt

import jieba
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.embedding_client import EmbeddingClient
from app.models.kb import ChunkEmbedding, KnowledgeChunk
from app.models.logs import QaRetrievalLog
from app.repositories.config_repo import RetrievalStrategyConfigRepo
from app.repositories.embedding_repo import EmbeddingIndexVersionRepo
from app.repositories.log_repo import QaRetrievalLogRepo
from app.vectorstore import get_vector_store
from app.vectorstore.base import VectorHit

_ZH_RE = re.compile(r"[\u4e00-\u9fff]")
_EN_RE = re.compile(r"[A-Za-z]")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*|[0-9]+(?:\.[0-9]+)?|[\u4e00-\u9fff]+")


def _normalize_query(raw: str) -> str:
    """Normalize whitespace while preserving user-visible terms."""
    return " ".join(raw.strip().split())


def _detect_language(text: str) -> str:
    """Detect query language as zh, en, mixed, or unknown."""
    has_zh = bool(_ZH_RE.search(text))
    has_en = bool(_EN_RE.search(text))
    if has_zh and has_en:
        return "mixed"
    if has_zh:
        return "zh"
    if has_en:
        return "en"
    return "unknown"


def _english_tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text) if _EN_RE.search(token)]


def _chinese_tokens(text: str) -> list[str]:
    return [token for token in jieba.cut(text) if len(token.strip()) > 1]


def _mixed_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for part in _TOKEN_RE.findall(text):
        if _ZH_RE.search(part):
            tokens.extend(_chinese_tokens(part))
        elif _EN_RE.search(part):
            tokens.append(part)
        else:
            tokens.append(part)
    return [token for token in tokens if token.strip()]


def _build_keyword_query(text: str, language: str) -> str:
    if language == "en":
        return " ".join(_english_tokens(text))
    if language == "mixed":
        return " ".join(_mixed_tokens(text))
    return " ".join(_chinese_tokens(text))


async def query_rewrite(raw: str) -> dict:
    """查询改写：规范化 + 中英文检测 + 关键词提取。"""
    normalized = _normalize_query(raw)
    language = _detect_language(normalized)
    keyword_query = _build_keyword_query(normalized, language)
    return {
        "raw_query": raw,
        "normalized_query": normalized,
        "keyword_query": keyword_query,
        "semantic_query": normalized,
        "language": language,
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


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity for MMR diversity scoring."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def mmr_diversify(
    items: list[dict],
    embeddings: dict[int, list[float]],
    *,
    lambda_param: float = 0.5,
    top_k: int = 5,
) -> list[dict]:
    """Re-rank retrieval hits with Maximum Marginal Relevance."""
    candidates = [
        (idx, item)
        for idx, item in enumerate(items)
        if item.get("chunk_id") in embeddings
    ]
    if len(candidates) <= 1:
        return items[:top_k]

    selected: list[int] = []
    remaining = [idx for idx, _ in candidates]

    while remaining and len(selected) < min(top_k, len(items)):
        best_idx = remaining[0]
        best_score = float("-inf")
        for idx in remaining:
            item = items[idx]
            chunk_id = item["chunk_id"]
            relevance = float(item.get("final_score") or 0)
            diversity_penalty = 0.0
            if selected:
                diversity_penalty = max(
                    _cosine_similarity(embeddings[chunk_id], embeddings[items[other]["chunk_id"]])
                    for other in selected
                )
            score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            if score > best_score:
                best_score = score
                best_idx = idx
        items[best_idx]["rerank_score"] = best_score
        selected.append(best_idx)
        remaining.remove(best_idx)

    selected_items = [items[idx] for idx in selected]
    if len(selected_items) >= top_k:
        return selected_items[:top_k]

    selected_ids = {item["chunk_id"] for item in selected_items}
    for item in items:
        if item.get("chunk_id") not in selected_ids:
            selected_items.append(item)
        if len(selected_items) >= top_k:
            break
    return selected_items


async def _load_chunk_embeddings(
    session: AsyncSession,
    embedding_index_version_id: int,
    chunk_ids: list[int],
) -> dict[int, list[float]]:
    if not chunk_ids:
        return {}
    stmt = select(ChunkEmbedding.chunk_id, ChunkEmbedding.embedding).where(
        ChunkEmbedding.embedding_index_version_id == embedding_index_version_id,
        ChunkEmbedding.chunk_id.in_(chunk_ids),
    )
    result = await session.execute(stmt)
    embeddings: dict[int, list[float]] = {}
    for row in result.fetchall():
        embeddings[int(row[0])] = list(row[1])
    return embeddings


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
    rerank_enabled = bool(strategy.rerank_enabled) if strategy else False

    emb_idx_repo = EmbeddingIndexVersionRepo(session)
    emb_idx = await emb_idx_repo.get_latest_by_version(kb_version_id)

    vector_hits: list[VectorHit] = []
    keyword_hits: list[tuple[int, float]] = []
    vector_failed = False
    keyword_failed = False

    if emb_idx:
        filter_dict = {"course_id": course_id} if course_id else None
        try:
            vector_hits = await _vector_search(
                session, emb_idx.id, semantic_query, v_top_k, filter_dict
            )
        except Exception:  # noqa: BLE001
            vector_failed = True

    try:
        keyword_hits = await _keyword_search(
            session, kw_query, kb_version_id, kw_top_k
        )
    except Exception:  # noqa: BLE001
        keyword_failed = True

    retrieval_channel = _resolve_retrieval_channel(
        vector_hits=vector_hits,
        keyword_hits=keyword_hits,
        vector_failed=vector_failed,
        keyword_failed=keyword_failed,
        has_embedding_index=emb_idx is not None,
    )

    candidate_top_k = max(v_top_k, kw_top_k, final_top_k) if rerank_enabled else final_top_k
    fused = _hybrid_fusion(
        vector_hits, keyword_hits, v_weight, kw_weight, candidate_top_k
    )
    if rerank_enabled and emb_idx and fused:
        embeddings = await _load_chunk_embeddings(
            session, emb_idx.id, [int(r["chunk_id"]) for r in fused]
        )
        fused = mmr_diversify(fused, embeddings, top_k=final_top_k)

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
    log_rows = fused or [{"chunk_id": None, "final_score": None}]
    for rank, r in enumerate(log_rows):
        log_entry = await log_repo.add(
            QaRetrievalLog(
                session_id=session_id,
                message_id=message_id or 0,
                raw_query=rewritten["raw_query"],
                normalized_query=rewritten["normalized_query"],
                keyword_query=rewritten["keyword_query"],
                semantic_query=rewritten["semantic_query"],
                language=rewritten["language"],
                retrieval_strategy="hybrid",
                knowledge_base_version_id=kb_version_id,
                chunk_id=r.get("chunk_id"),
                rank_no=rank + 1 if r.get("chunk_id") is not None else None,
                final_score=r["final_score"],
                retrieval_channel=retrieval_channel,
                used_in_prompt=bool(r.get("chunk_id") is not None and rank < final_top_k),
                reject_reason="RETRIEVAL_EMPTY" if not fused else None,
            )
        )
        if retrieval_log_id is None:
            retrieval_log_id = log_entry.id
    await session.flush()

    return rewritten["normalized_query"], fused, retrieval_log_id


def _resolve_retrieval_channel(
    *,
    vector_hits: list[VectorHit],
    keyword_hits: list[tuple[int, float]],
    vector_failed: bool,
    keyword_failed: bool,
    has_embedding_index: bool,
) -> str:
    """Return the actual retrieval channel used for audit logs."""
    if vector_hits and keyword_hits:
        return "hybrid"
    if vector_hits and keyword_failed:
        return "vector_only"
    if keyword_hits and (vector_failed or not has_embedding_index):
        return "keyword_only"
    if vector_hits:
        return "vector_only"
    if keyword_hits:
        return "keyword_only"
    return "empty"
