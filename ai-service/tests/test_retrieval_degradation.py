"""Retrieval degradation tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.retrieval as retrieval
from app.models.logs import QaRetrievalLog
from app.vectorstore.base import VectorHit


class FakeConfigRepo:
    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    async def get_default(self):  # noqa: ANN201
        return None


class FakeEmbeddingIndexRepo:
    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    async def get_latest_by_version(self, kb_version_id: int):  # noqa: ARG002, ANN201
        return SimpleNamespace(id=9)


class FakeLogRepo:
    logs: list[QaRetrievalLog] = []

    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    async def add(self, log: QaRetrievalLog) -> QaRetrievalLog:
        log.id = len(self.logs) + 1
        self.logs.append(log)
        return log


class FakeRows:
    def __init__(self, rows: list[tuple]) -> None:
        self.rows = rows

    def fetchall(self) -> list[tuple]:
        return self.rows


@pytest.fixture(autouse=True)
def patch_repos(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeLogRepo.logs = []
    monkeypatch.setattr(retrieval, "RetrievalStrategyConfigRepo", FakeConfigRepo)
    monkeypatch.setattr(retrieval, "EmbeddingIndexVersionRepo", FakeEmbeddingIndexRepo)
    monkeypatch.setattr(retrieval, "QaRetrievalLogRepo", FakeLogRepo)


def fake_session(rows: list[tuple] | None = None) -> AsyncMock:
    session = AsyncMock()
    session.execute.return_value = FakeRows(rows or [])
    return session


@pytest.mark.asyncio
async def test_hybrid_retrieve_degrades_to_keyword_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_vector(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        raise RuntimeError("embedding unavailable")

    async def keyword(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return [(1, 0.8)]

    monkeypatch.setattr(retrieval, "_vector_search", fail_vector)
    monkeypatch.setattr(retrieval, "_keyword_search", keyword)

    _, fused, log_ref = await retrieval.hybrid_retrieve(
        fake_session([(1, "文本", 10, 20, "a.pdf", 1, 1, {})]),
        question="机器学习",
        kb_version_id=1,
        course_id=1,
        message_id=5,
    )

    assert log_ref == 1
    assert fused[0]["chunk_id"] == 1
    assert FakeLogRepo.logs[0].retrieval_channel == "keyword_only"


@pytest.mark.asyncio
async def test_hybrid_retrieve_degrades_to_empty_when_all_channels_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        raise RuntimeError("down")

    monkeypatch.setattr(retrieval, "_vector_search", fail)
    monkeypatch.setattr(retrieval, "_keyword_search", fail)

    _, fused, log_ref = await retrieval.hybrid_retrieve(
        fake_session(),
        question="机器学习",
        kb_version_id=1,
        course_id=1,
        message_id=5,
    )

    assert log_ref == 1
    assert fused == []
    assert FakeLogRepo.logs[0].retrieval_channel == "empty"
    assert FakeLogRepo.logs[0].reject_reason == "RETRIEVAL_EMPTY"


@pytest.mark.asyncio
async def test_hybrid_retrieve_keeps_vector_hits_when_keyword_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def vector(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        return [VectorHit(chunk_id=2, score=0.9)]

    async def fail_keyword(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001, ANN202
        raise RuntimeError("fts unavailable")

    monkeypatch.setattr(retrieval, "_vector_search", vector)
    monkeypatch.setattr(retrieval, "_keyword_search", fail_keyword)

    _, fused, _ = await retrieval.hybrid_retrieve(
        fake_session([(2, "文本", 10, 20, "b.pdf", 2, 2, {})]),
        question="机器学习",
        kb_version_id=1,
        course_id=1,
        message_id=5,
    )

    assert fused[0]["chunk_id"] == 2
    assert FakeLogRepo.logs[0].retrieval_channel == "vector_only"
