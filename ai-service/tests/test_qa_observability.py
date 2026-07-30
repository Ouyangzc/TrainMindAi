"""QA observability tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.api.internal.v1.qa as qa_api
from app.schemas.qa import QaAnswerRequest


@pytest.mark.asyncio
async def test_safe_log_observation_counts_quality_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class FakeObservationRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def log_observation(self, **values):  # noqa: ANN003, ANN202
            captured.update(values)
            return SimpleNamespace(id=1)

    async def fake_retrieval_meta(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return "mixed", "hybrid"

    monkeypatch.setattr(qa_api, "QaAnswerObservationRepo", FakeObservationRepo)
    monkeypatch.setattr(qa_api, "_retrieval_meta", fake_retrieval_meta)

    req = QaAnswerRequest(
        user_id=1,
        course_id=10,
        kb_version_id=20,
        session_id=30,
        message_id=40,
        question="ML 算法",
    )

    await qa_api._safe_log_observation(
        AsyncMock(),
        req=req,
        fused=[{"chunk_id": 1, "final_score": 0.8}, {"chunk_id": 2, "final_score": 0.2}],
        retrieval_log_ref=99,
        model_call_log_ref=88,
        answer_status="grounded",
        reject_reason=None,
        warnings=["INVALID_CITATION:99", "WEAK_CITATION:2", "NO_VALID_CITATION"],
        cited_source_count=1,
        retrieval_latency_ms=12,
        llm_latency_ms=34,
        first_token_ms=20,
        total_latency_ms=50,
    )

    assert captured["course_id"] == 10
    assert captured["language"] == "mixed"
    assert captured["retrieval_channel"] == "hybrid"
    assert captured["source_count"] == 2
    assert captured["cited_source_count"] == 1
    assert captured["invalid_citation_count"] == 1
    assert captured["weak_citation_count"] == 1
    assert captured["no_valid_citation"] is True
    assert captured["top_score"] == 0.8
    assert captured["total_latency_ms"] == 50


@pytest.mark.asyncio
async def test_stream_success_writes_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    async def fake_retrieve(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return (
            "query",
            [
                {
                    "chunk_id": 7,
                    "document_id": 1,
                    "document_version_id": 2,
                    "final_score": 0.9,
                    "text": "资料",
                }
            ],
            99,
        )

    class FakeLlm:
        model = "fake"

        async def chat_stream(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            yield "回答[来源:1]"

    class FakeLogRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def log_call(self, **kwargs):  # noqa: ANN003, ANN202
            return SimpleNamespace(id=55, **kwargs)

    class FakeObservationRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            self.session = session

        async def log_observation(self, **values):  # noqa: ANN003, ANN202
            captured.update(values)
            return SimpleNamespace(id=1)

    async def no_template(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return None

    async def fake_retrieval_meta(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return "zh", "hybrid"

    monkeypatch.setattr(qa_api, "hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr(qa_api, "LlmClient", FakeLlm)
    monkeypatch.setattr(qa_api, "ModelCallLogRepo", FakeLogRepo)
    monkeypatch.setattr(qa_api, "QaAnswerObservationRepo", FakeObservationRepo)
    monkeypatch.setattr(qa_api, "_select_qa_prompt_template", no_template)
    monkeypatch.setattr(qa_api, "_retrieval_meta", fake_retrieval_meta)

    req = QaAnswerRequest(
        user_id=1,
        course_id=10,
        kb_version_id=20,
        session_id=30,
        message_id=40,
        question="问题",
    )

    events = [event async for event in qa_api._stream_events(req, AsyncMock())]

    assert any("event: sources" in event for event in events)
    assert captured["message_id"] == 40
    assert captured["model_call_log_ref"] == 55
    assert captured["answer_status"] == "grounded"
    assert captured["cited_source_count"] == 1
    assert captured["first_token_ms"] is not None
