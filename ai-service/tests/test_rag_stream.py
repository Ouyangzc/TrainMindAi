"""RAG SSE stream tests."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.api.internal.v1.qa as qa_api
from app.schemas.qa import QaAnswerRequest


class FakeLogRepo:
    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    async def log_call(self, **kwargs):  # noqa: ANN003, ANN202
        return SimpleNamespace(id=1, **kwargs)


def parse_sse(frame: str) -> tuple[str, dict]:
    lines = frame.strip().splitlines()
    event = lines[0].removeprefix("event: ")
    data = json.loads(lines[1].removeprefix("data: "))
    return event, data


@pytest.mark.asyncio
async def test_stream_events_yield_tokens_and_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_retrieve(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return (
            "query",
            [
                {
                    "chunk_id": 7,
                    "document_id": 1,
                    "document_version_id": 2,
                    "source_file": "lesson.pdf",
                    "page_start": 1,
                    "page_end": 1,
                    "section_title": "概念",
                    "final_score": 0.9,
                    "text": "机器学习资料",
                }
            ],
            99,
        )

    class FakeLlm:
        model = "fake"

        async def chat_stream(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            yield "你好"
            yield "世界[来源:1]"

    async def no_template(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return None

    async def noop_observation(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return None

    monkeypatch.setattr(qa_api, "hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr(qa_api, "LlmClient", FakeLlm)
    monkeypatch.setattr(qa_api, "_select_qa_prompt_template", no_template)
    monkeypatch.setattr(qa_api, "ModelCallLogRepo", FakeLogRepo)
    monkeypatch.setattr(qa_api, "_safe_log_observation", noop_observation)

    req = QaAnswerRequest(
        user_id=1,
        course_id=1,
        kb_version_id=1,
        session_id=1,
        message_id=1,
        question="test",
    )
    events = [parse_sse(frame) async for frame in qa_api._stream_events(req, AsyncMock())]

    assert [event for event, _ in events] == ["metadata", "token", "token", "sources", "done"]
    assert events[1][1] == {"token": "你好"}
    assert events[3][1]["answer"] == "你好世界[来源:1]"
    assert events[3][1]["sources"][0]["chunk_id"] == 7
    assert events[3][1]["sources"][0]["source_index"] == 1
    assert events[3][1]["retrieval_log_ref"] == 99


@pytest.mark.asyncio
async def test_stream_events_return_structured_low_score_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_retrieve(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return ("query", [{"chunk_id": 1, "final_score": 0.1}], 5)

    async def noop_observation(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return None

    monkeypatch.setattr(qa_api, "hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr(qa_api, "_safe_log_observation", noop_observation)

    req = QaAnswerRequest(
        user_id=1,
        course_id=1,
        kb_version_id=1,
        session_id=1,
        message_id=1,
        question="test",
    )
    events = [parse_sse(frame) async for frame in qa_api._stream_events(req, AsyncMock())]

    assert [event for event, _ in events] == ["metadata", "sources", "done"]
    assert events[1][1]["answer_status"] == "insufficient_evidence"
    assert events[1][1]["reject_reason"] == "low_score"


@pytest.mark.asyncio
async def test_answer_stream_returns_sse_response() -> None:
    req = QaAnswerRequest(
        user_id=1,
        course_id=1,
        kb_version_id=1,
        session_id=1,
        message_id=1,
        question="test",
    )

    response = await qa_api.answer_stream(req, AsyncMock())

    assert response.media_type == "text/event-stream"
