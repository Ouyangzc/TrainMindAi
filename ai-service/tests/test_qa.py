from unittest.mock import AsyncMock

import pytest

from app.services.rag import qa_answer


@pytest.mark.asyncio
async def test_qa_answer_rejects_empty_retrieval_without_calling_llm() -> None:
    session = AsyncMock()

    result = await qa_answer(session, "资料中没有的问题", [], message_id=1)

    assert result["answer"] == ""
    assert result["reject_reason"] == "low_score"
