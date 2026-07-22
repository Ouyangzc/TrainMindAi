"""RAG：prompt 组装 / 生成 / 引用校验 / 拒答策略。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.gateway.llm_client import LlmClient
from app.repositories.log_repo import ModelCallLogRepo

# 拒答阈值：最终分数低于此值时拒答
_MIN_SCORE_THRESHOLD = 0.3


def _build_rag_prompt(question: str, context_chunks: list[dict]) -> list[dict]:
    """组装 RAG prompt（messages 格式）。"""
    system = (
        "你是一个专业的知识助教。请基于提供的参考资料，用中文回答用户问题。"
        "回答要求：\n"
        "1. 如果参考资料足够回答，请给出准确、完整的答案\n"
        "2. 如果参考资料不足以回答，请说明无法回答\n"
        "3. 在答案末尾注明引用的资料编号，格式为「[来源:N]」\n"
        "4. 不要编造信息\n"
    )
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        ctx = f"[来源 {i + 1}]\n{chunk.get('text', '')}"
        if chunk.get("source_file"):
            ctx += f"\n(文件: {chunk['source_file']})"
        context_parts.append(ctx)

    context_block = "\n\n---\n\n".join(context_parts)
    user_prompt = f"参考资料：\n{context_block}\n\n问题：{question}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


async def qa_answer(
    session: AsyncSession,
    question: str,
    context_chunks: list[dict],
    message_id: int | None = None,
) -> dict:
    """RAG 问答：组装 prompt → LLM 生成 → 引用校验 → 返回结果。

    返回：{"answer": str, "reject_reason": str | None, "model": str}
    """
    # 拒答检查：最低分阈值
    scores = [c.get("final_score", 0) for c in context_chunks]
    if not scores or max(scores) < _MIN_SCORE_THRESHOLD:
        return {
            "answer": "",
            "reject_reason": "low_score",
            "model": settings.llm_model,
        }

    messages = _build_rag_prompt(question, context_chunks)

    llm = LlmClient()
    log_repo = ModelCallLogRepo(session)

    try:
        answer = await llm.chat(messages)

        await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=message_id,
            success=True,
        )
        await session.flush()

        return {
            "answer": answer,
            "reject_reason": None,
            "model": llm.model,
        }
    except Exception as exc:
        await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=message_id,
            success=False,
            error_message=str(exc),
        )
        await session.flush()
        return {
            "answer": "",
            "reject_reason": "llm_error",
            "model": llm.model,
        }
