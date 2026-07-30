from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.rag as rag
from app.schemas.qa import QaHistoryTurn
from app.services.rag import qa_answer, validate_citations


@pytest.mark.asyncio
async def test_qa_answer_rejects_empty_retrieval_without_calling_llm() -> None:
    session = AsyncMock()

    result = await qa_answer(session, "资料中没有的问题", [], message_id=1)

    assert result["answer"] == ""
    assert result["reject_reason"] == "low_score"


class FakeLogRepo:
    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    async def log_call(self, **kwargs):  # noqa: ANN003, ANN202
        return SimpleNamespace(id=1, **kwargs)


@pytest.mark.asyncio
async def test_qa_answer_uses_configured_prompt_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class FakePromptRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def get_by_scenario(self, scenario: str):  # noqa: ANN201
            assert scenario == "qa"
            return [
                SimpleNamespace(prompt_version="v1", prompt_content="默认模板"),
                SimpleNamespace(prompt_version="v2", prompt_content="自定义 QA 模板"),
            ]

    class FakeLlm:
        model = "fake"

        async def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["messages"] = messages
            return "回答[来源:1]"

    monkeypatch.setattr(rag, "PromptTemplateRepo", FakePromptRepo)
    monkeypatch.setattr(rag, "LlmClient", FakeLlm)
    monkeypatch.setattr(rag, "ModelCallLogRepo", FakeLogRepo)

    result = await qa_answer(
        AsyncMock(),
        "什么是机器学习",
        [{"chunk_id": 1, "final_score": 0.9, "text": "机器学习资料"}],
        message_id=1,
        prompt_version="v2",
    )

    assert result["answer"] == "回答[来源:1]"
    assert captured["messages"][0]["content"] == "自定义 QA 模板"


@pytest.mark.asyncio
async def test_qa_answer_falls_back_to_default_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class EmptyPromptRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def get_by_scenario(self, scenario: str):  # noqa: ARG002, ANN201
            return []

    class FakeLlm:
        model = "fake"

        async def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["messages"] = messages
            return "回答"

    monkeypatch.setattr(rag, "PromptTemplateRepo", EmptyPromptRepo)
    monkeypatch.setattr(rag, "LlmClient", FakeLlm)
    monkeypatch.setattr(rag, "ModelCallLogRepo", FakeLogRepo)

    await qa_answer(
        AsyncMock(),
        "什么是机器学习",
        [{"chunk_id": 1, "final_score": 0.9, "text": "机器学习资料"}],
    )

    assert "专业的知识助教" in captured["messages"][0]["content"]


@pytest.mark.asyncio
async def test_qa_answer_includes_history_in_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class EmptyPromptRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def get_by_scenario(self, scenario: str):  # noqa: ARG002, ANN201
            return []

    class FakeLlm:
        model = "fake"

        async def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["messages"] = messages
            return "它指监督学习。[来源:1]"

    monkeypatch.setattr(rag, "PromptTemplateRepo", EmptyPromptRepo)
    monkeypatch.setattr(rag, "LlmClient", FakeLlm)
    monkeypatch.setattr(rag, "ModelCallLogRepo", FakeLogRepo)

    await qa_answer(
        AsyncMock(),
        "它是什么？",
        [{"chunk_id": 1, "final_score": 0.9, "text": "监督学习资料"}],
        history=[QaHistoryTurn(user="什么是监督学习？", assistant="监督学习是带标签训练。")],
    )

    user_prompt = captured["messages"][1]["content"]
    assert "历史对话" in user_prompt
    assert "什么是监督学习" in user_prompt
    assert "它是什么" in user_prompt


def test_validate_citations_keeps_valid_markers() -> None:
    answer, source_indices, warnings = validate_citations(
        "监督学习需要标签。[来源:1]",
        [{"chunk_id": 1, "final_score": 0.9}],
    )

    assert answer == "监督学习需要标签。[来源:1]"
    assert source_indices == {1}
    assert warnings == []


def test_validate_citations_removes_invalid_markers() -> None:
    answer, source_indices, warnings = validate_citations(
        "监督学习需要标签。[来源:99]",
        [{"chunk_id": 1, "final_score": 0.9}],
    )

    assert answer == "监督学习需要标签。"
    assert source_indices == set()
    assert "INVALID_CITATION:99" in warnings
    assert "NO_VALID_CITATION" in warnings


def test_validate_citations_marks_weak_citations() -> None:
    _, source_indices, warnings = validate_citations(
        "可能相关。[来源 2]",
        [
            {"chunk_id": 1, "final_score": 0.9},
            {"chunk_id": 2, "final_score": 0.1},
        ],
    )

    assert source_indices == {2}
    assert warnings == ["WEAK_CITATION:2"]
