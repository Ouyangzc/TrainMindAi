"""RAG 问答（同步 + SSE；上下文由 Java 解析后传入）。"""

import json
import logging
from collections.abc import AsyncIterator
from time import perf_counter

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.gateway.llm_client import LlmClient
from app.models.logs import QaRetrievalLog
from app.repositories.log_repo import ModelCallLogRepo, QaAnswerObservationRepo
from app.schemas.qa import QaAnswerRequest, QaAnswerResponse, QaSource
from app.services.rag import (
    _MIN_SCORE_THRESHOLD,
    _build_rag_prompt,
    _select_qa_prompt_template,
    qa_answer,
    validate_citations,
)
from app.services.retrieval import hybrid_retrieve

router = APIRouter(prefix="/qa", tags=["qa"])
logger = logging.getLogger(__name__)


@router.post("/answer", response_model=QaAnswerResponse)
async def answer(
    req: QaAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> QaAnswerResponse:
    """同步问答：查询改写->混合检索->Prompt->LLM->引用校验。"""
    started = perf_counter()
    retrieval_started = perf_counter()
    _, fused, log_ref = await hybrid_retrieve(
        session,
        question=req.question,
        kb_version_id=req.kb_version_id,
        course_id=req.course_id,
        session_id=req.session_id,
        message_id=req.message_id,
    )
    retrieval_latency_ms = int((perf_counter() - retrieval_started) * 1000)

    result = await qa_answer(
        session,
        question=req.question,
        context_chunks=fused,
        message_id=req.message_id,
        prompt_version=req.prompt_version,
        history=req.history,
    )

    sources = _build_sources(fused, result.get("source_indices") or set())
    answer_status = _answer_status(result["reject_reason"])
    await _safe_log_observation(
        session,
        req=req,
        fused=fused,
        retrieval_log_ref=log_ref,
        model_call_log_ref=result.get("model_call_log_ref"),
        answer_status=answer_status,
        reject_reason=result["reject_reason"],
        warnings=result.get("warnings") or [],
        cited_source_count=len(sources),
        retrieval_latency_ms=retrieval_latency_ms,
        llm_latency_ms=result.get("llm_latency_ms"),
        total_latency_ms=int((perf_counter() - started) * 1000),
    )

    return QaAnswerResponse(
        answer=result["answer"],
        answer_status=answer_status,
        knowledge_base_version_id=req.kb_version_id,
        sources=sources,
        warnings=result.get("warnings") or [],
        reject_reason=result["reject_reason"],
        retrieval_log_ref=log_ref,
    )


def _build_sources(fused: list[dict], source_indices: set[int]) -> list[QaSource]:
    sources: list[QaSource] = []
    for index, c in enumerate(fused, start=1):
        if index not in source_indices:
            continue
        sources.append(
            QaSource(
                chunk_id=c["chunk_id"],
                source_index=index,
                document_id=c["document_id"],
                document_version_id=c["document_version_id"],
                source_file=c.get("source_file"),
                page_start=c.get("page_start"),
                page_end=c.get("page_end"),
                section_title=c.get("section_title"),
                score=c.get("final_score"),
            )
        )
    return sources


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _answer_status(reject_reason: str | None) -> str:
    if reject_reason is None:
        return "grounded"
    if reject_reason == "llm_error":
        return "service_unavailable"
    return "insufficient_evidence"


def _warning_count(warnings: list[str], prefix: str) -> int:
    return sum(1 for warning in warnings if warning.startswith(prefix))


async def _retrieval_meta(
    session: AsyncSession,
    retrieval_log_ref: int | None,
) -> tuple[str | None, str | None]:
    if retrieval_log_ref is None:
        return None, None
    result = await session.execute(
        select(QaRetrievalLog.language, QaRetrievalLog.retrieval_channel).where(
            QaRetrievalLog.id == retrieval_log_ref
        )
    )
    row = result.first()
    if row is None:
        return None, None
    return row[0], row[1]


async def _safe_log_observation(
    session: AsyncSession,
    *,
    req: QaAnswerRequest,
    fused: list[dict],
    retrieval_log_ref: int | None,
    model_call_log_ref: int | None = None,
    answer_status: str,
    reject_reason: str | None,
    warnings: list[str],
    cited_source_count: int,
    retrieval_latency_ms: int | None,
    llm_latency_ms: int | None = None,
    first_token_ms: int | None = None,
    total_latency_ms: int | None = None,
) -> None:
    """Best-effort answer-level observation; never block the user path."""
    try:
        language, retrieval_channel = await _retrieval_meta(session, retrieval_log_ref)
        await QaAnswerObservationRepo(session).log_observation(
            course_id=req.course_id,
            session_id=req.session_id,
            message_id=req.message_id,
            knowledge_base_version_id=req.kb_version_id,
            retrieval_log_ref=retrieval_log_ref,
            model_call_log_ref=model_call_log_ref,
            language=language,
            retrieval_channel=retrieval_channel,
            answer_status=answer_status,
            reject_reason=reject_reason,
            warnings=warnings,
            source_count=len(fused),
            cited_source_count=cited_source_count,
            invalid_citation_count=_warning_count(warnings, "INVALID_CITATION:"),
            weak_citation_count=_warning_count(warnings, "WEAK_CITATION:"),
            no_valid_citation="NO_VALID_CITATION" in warnings,
            top_score=max((c.get("final_score") or 0 for c in fused), default=None),
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            first_token_ms=first_token_ms,
            total_latency_ms=total_latency_ms,
        )
        await session.flush()
    except Exception:  # noqa: BLE001
        logger.exception("failed to write QA answer observation")


async def _stream_events(req: QaAnswerRequest, session: AsyncSession) -> AsyncIterator[str]:
    started = perf_counter()
    retrieval_started = perf_counter()
    try:
        _, fused, log_ref = await hybrid_retrieve(
            session,
            question=req.question,
            kb_version_id=req.kb_version_id,
            course_id=req.course_id,
            session_id=req.session_id,
            message_id=req.message_id,
        )
        retrieval_latency_ms = int((perf_counter() - retrieval_started) * 1000)
    except Exception as exc:  # noqa: BLE001
        await _safe_log_observation(
            session,
            req=req,
            fused=[],
            retrieval_log_ref=None,
            answer_status="service_unavailable",
            reject_reason="retrieval_error",
            warnings=["RETRIEVAL_ERROR"],
            cited_source_count=0,
            retrieval_latency_ms=int((perf_counter() - retrieval_started) * 1000),
            total_latency_ms=int((perf_counter() - started) * 1000),
        )
        yield _sse("error", {"message": str(exc)})
        yield _sse("done", {})
        return

    yield _sse(
        "metadata",
        {
            "knowledge_base_version_id": req.kb_version_id,
            "retrieval_log_ref": log_ref,
        },
    )

    scores = [c.get("final_score", 0) for c in fused]
    if not scores or max(scores) < _MIN_SCORE_THRESHOLD:
        await _safe_log_observation(
            session,
            req=req,
            fused=fused,
            retrieval_log_ref=log_ref,
            answer_status="insufficient_evidence",
            reject_reason="low_score",
            warnings=["LOW_SCORE"],
            cited_source_count=0,
            retrieval_latency_ms=retrieval_latency_ms,
            total_latency_ms=int((perf_counter() - started) * 1000),
        )
        yield _sse(
            "sources",
            {
                "answer": "",
                "answer_status": "insufficient_evidence",
                "knowledge_base_version_id": req.kb_version_id,
                "sources": [],
                "warnings": ["LOW_SCORE"],
                "reject_reason": "low_score",
                "retrieval_log_ref": log_ref,
            },
        )
        yield _sse("done", {})
        return

    prompt_template = await _select_qa_prompt_template(session, req.prompt_version)
    messages = _build_rag_prompt(
        req.question,
        fused,
        prompt_template=prompt_template.prompt_content if prompt_template else None,
        history=req.history,
    )
    llm = LlmClient()
    log_repo = ModelCallLogRepo(session)
    answer_parts: list[str] = []
    first_token_ms: int | None = None
    llm_started = perf_counter()
    try:
        async for token in llm.chat_stream(messages):
            if first_token_ms is None:
                first_token_ms = int((perf_counter() - started) * 1000)
            answer_parts.append(token)
            yield _sse("token", {"token": token})
        llm_latency_ms = int((perf_counter() - llm_started) * 1000)
        model_call_log = await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=req.message_id,
            latency_ms=llm_latency_ms,
            success=True,
        )
        await session.flush()
    except Exception as exc:  # noqa: BLE001
        llm_latency_ms = int((perf_counter() - llm_started) * 1000)
        model_call_log = await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=req.message_id,
            latency_ms=llm_latency_ms,
            success=False,
            error_code="LLM_ERROR",
            error_message=str(exc),
        )
        await session.flush()
        await _safe_log_observation(
            session,
            req=req,
            fused=fused,
            retrieval_log_ref=log_ref,
            model_call_log_ref=model_call_log.id,
            answer_status="service_unavailable",
            reject_reason="llm_error",
            warnings=["LLM_ERROR"],
            cited_source_count=0,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            first_token_ms=first_token_ms,
            total_latency_ms=int((perf_counter() - started) * 1000),
        )
        yield _sse("error", {"message": str(exc)})
        yield _sse("done", {})
        return

    answer_text, source_indices, warnings = validate_citations("".join(answer_parts), fused)
    sources = _build_sources(fused, source_indices)
    await _safe_log_observation(
        session,
        req=req,
        fused=fused,
        retrieval_log_ref=log_ref,
        model_call_log_ref=model_call_log.id,
        answer_status="grounded",
        reject_reason=None,
        warnings=warnings,
        cited_source_count=len(sources),
        retrieval_latency_ms=retrieval_latency_ms,
        llm_latency_ms=llm_latency_ms,
        first_token_ms=first_token_ms,
        total_latency_ms=int((perf_counter() - started) * 1000),
    )
    yield _sse(
        "sources",
        {
            "answer": answer_text,
            "answer_status": "grounded",
            "knowledge_base_version_id": req.kb_version_id,
            "sources": [source.model_dump() for source in sources],
            "warnings": warnings,
            "reject_reason": None,
            "retrieval_log_ref": log_ref,
        },
    )
    yield _sse("done", {})


@router.post("/answer/stream")
async def answer_stream(
    req: QaAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """SSE 流式问答（逐 token，结束补 sources）。"""
    return StreamingResponse(
        _stream_events(req, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
