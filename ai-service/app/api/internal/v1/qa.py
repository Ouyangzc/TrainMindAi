"""RAG 问答（同步 + SSE；上下文由 Java 解析后传入）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.qa import QaAnswerRequest, QaAnswerResponse, QaSource
from app.services.rag import qa_answer
from app.services.retrieval import hybrid_retrieve

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/answer", response_model=QaAnswerResponse)
async def answer(
    req: QaAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> QaAnswerResponse:
    """同步问答：查询改写->混合检索->Prompt->LLM->引用校验。"""
    _, fused, log_ref = await hybrid_retrieve(
        session,
        question=req.question,
        kb_version_id=req.kb_version_id,
        course_id=req.course_id,
    )

    result = await qa_answer(
        session,
        question=req.question,
        context_chunks=fused,
        message_id=req.message_id,
    )

    sources = [
        QaSource(
            chunk_id=c["chunk_id"],
            document_id=0,
            source_file=c.get("source_file"),
            page_start=c.get("page_start"),
            page_end=c.get("page_end"),
            score=c.get("final_score"),
        )
        for c in fused
    ]

    return QaAnswerResponse(
        answer=result["answer"],
        sources=sources,
        reject_reason=result["reject_reason"],
        retrieval_log_ref=log_ref,
    )


@router.post("/answer/stream")
async def answer_stream(req: QaAnswerRequest) -> None:
    """SSE 流式问答（逐 token，结束补 sources）。"""
    # 当前 stub，后续实现
    from app.api.internal.v1._stub import not_implemented  # noqa: PLC0415

    raise not_implemented("RAG 流式问答")
