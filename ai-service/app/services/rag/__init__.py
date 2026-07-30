"""RAG：prompt 组装 / 生成 / 引用校验 / 拒答策略。"""

import re
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.gateway.llm_client import LlmClient
from app.models.config_tables import PromptTemplate
from app.repositories.config_repo import PromptTemplateRepo
from app.repositories.log_repo import ModelCallLogRepo
from app.schemas.qa import QaHistoryTurn

# 拒答阈值：最终分数低于此值时拒答
_MIN_SCORE_THRESHOLD = 0.3
_DEFAULT_QA_PROMPT = (
    "你是一个专业的知识助教。请基于提供的参考资料，用中文回答用户问题。"
    "回答要求：\n"
    "1. 如果参考资料足够回答，请给出准确、完整的答案\n"
    "2. 如果参考资料不足以回答，请说明无法回答\n"
    "3. 在答案末尾注明引用的资料编号，格式为「[来源:N]」\n"
    "4. 不要编造信息\n"
)
_CITATION_RE = re.compile(r"\[来源\s*[:： ]\s*(\d+)\]")
_MAX_HISTORY_USER_CHARS = 300
_MAX_HISTORY_ASSISTANT_CHARS = 800


def _build_rag_prompt(
    question: str,
    context_chunks: list[dict],
    *,
    prompt_template: str | None = None,
    history: list[QaHistoryTurn] | None = None,
) -> list[dict]:
    """组装 RAG prompt（messages 格式）。"""
    system = prompt_template or _DEFAULT_QA_PROMPT
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        ctx = f"[来源 {i + 1}]\n{chunk.get('text', '')}"
        if chunk.get("source_file"):
            ctx += f"\n(文件: {chunk['source_file']})"
        context_parts.append(ctx)

    context_block = "\n\n---\n\n".join(context_parts)
    history_block = _format_history(history or [])
    user_prompt = (
        f"{history_block}\n\n" if history_block else ""
    ) + f"参考资料：\n{context_block}\n\n问题：{question}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


def _truncate_text(value: str, max_chars: int) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "..."


def _format_history(history: list[QaHistoryTurn]) -> str:
    if not history:
        return ""
    parts = ["历史对话："]
    for turn in history:
        user = _truncate_text(turn.user, _MAX_HISTORY_USER_CHARS)
        assistant = _truncate_text(turn.assistant, _MAX_HISTORY_ASSISTANT_CHARS)
        if not user or not assistant:
            continue
        parts.append(f"用户：{user}\n助手：{assistant}")
    return "\n---\n".join(parts) if len(parts) > 1 else ""


async def _select_qa_prompt_template(
    session: AsyncSession,
    prompt_version: str | None = None,
) -> PromptTemplate | None:
    """Select an enabled QA prompt template, falling back to the built-in prompt."""
    templates = await PromptTemplateRepo(session).get_by_scenario("qa")
    if prompt_version:
        return next(
            (item for item in templates if item.prompt_version == prompt_version),
            None,
        )
    return templates[-1] if templates else None


def validate_citations(answer: str, context_chunks: list[dict]) -> tuple[str, set[int], list[str]]:
    """Validate answer citation markers against the current retrieval context."""
    valid_indices = set(range(1, len(context_chunks) + 1))
    cited_indices: set[int] = set()
    warnings: list[str] = []

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if index in valid_indices:
            cited_indices.add(index)
            return match.group(0)
        warnings.append(f"INVALID_CITATION:{index}")
        return ""

    cleaned_answer = _CITATION_RE.sub(replace, answer)
    if not cited_indices and context_chunks:
        warnings.append("NO_VALID_CITATION")

    for index in sorted(cited_indices):
        score = float(context_chunks[index - 1].get("final_score") or 0)
        if score < 0.2:
            warnings.append(f"WEAK_CITATION:{index}")

    return cleaned_answer, cited_indices, warnings


async def qa_answer(
    session: AsyncSession,
    question: str,
    context_chunks: list[dict],
    message_id: int | None = None,
    prompt_version: str | None = None,
    history: list[QaHistoryTurn] | None = None,
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
            "source_indices": set(),
            "warnings": ["LOW_SCORE"],
        }

    prompt_template = await _select_qa_prompt_template(session, prompt_version)
    messages = _build_rag_prompt(
        question,
        context_chunks,
        prompt_template=prompt_template.prompt_content if prompt_template else None,
        history=history,
    )

    llm = LlmClient()
    log_repo = ModelCallLogRepo(session)

    llm_started: float | None = None
    llm_latency_ms: int | None = None
    try:
        llm_started = perf_counter()
        answer = await llm.chat(messages)
        llm_latency_ms = int((perf_counter() - llm_started) * 1000)
        answer, source_indices, warnings = validate_citations(answer, context_chunks)

        model_call_log = await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=message_id,
            latency_ms=llm_latency_ms,
            success=True,
        )
        await session.flush()

        return {
            "answer": answer,
            "reject_reason": None,
            "model": llm.model,
            "model_call_log_ref": model_call_log.id,
            "llm_latency_ms": llm_latency_ms,
            "source_indices": source_indices,
            "warnings": warnings,
        }
    except Exception as exc:
        llm_latency_ms = (
            int((perf_counter() - llm_started) * 1000)
            if llm_started is not None
            else None
        )
        model_call_log = await log_repo.log_call(
            scenario="qa",
            provider="openai",
            model=llm.model,
            message_id=message_id,
            latency_ms=llm_latency_ms,
            success=False,
            error_code="LLM_ERROR",
            error_message=str(exc),
        )
        await session.flush()
        return {
            "answer": "",
            "reject_reason": "llm_error",
            "model": llm.model,
            "model_call_log_ref": model_call_log.id,
            "llm_latency_ms": llm_latency_ms,
            "source_indices": set(),
            "warnings": ["LLM_ERROR"],
        }
