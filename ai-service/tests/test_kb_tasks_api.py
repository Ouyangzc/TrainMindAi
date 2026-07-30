"""KB build task API tests."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.internal.v1 import kb_tasks
from app.core.config import settings
from app.core.db import get_session
from app.main import app
from app.models.kb import KbBuildTask


class FakeSession:
    async def commit(self) -> None:
        return None


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async def override_session() -> FakeSession:
        return FakeSession()

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_tasks_filters_by_kb_version(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}
    created_at = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)
    finished_at = datetime(2026, 7, 30, 10, 5, tzinfo=UTC)

    class FakeTaskRepo:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def count(self, *filters) -> int:  # noqa: ANN002
            captured["filter_count"] = len(filters)
            return 1

        async def find(self, *filters, order_by=None, limit=100, offset=0):  # noqa: ANN001, ANN002
            captured["limit"] = limit
            captured["offset"] = offset
            return [
                KbBuildTask(
                    id=7,
                    knowledge_base_version_id=5,
                    task_type="build_knowledge_base_version",
                    status="success",
                    current_step="embedding_index_ready",
                    progress=100,
                    created_at=created_at,
                    finished_at=finished_at,
                )
            ]

    monkeypatch.setattr(kb_tasks, "KbBuildTaskRepo", FakeTaskRepo)

    response = await client.get(
        "/internal/v1/kb-tasks?kb_version_id=5&page=2&size=10",
        headers={"X-Internal-Token": settings.internal_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "task_id": 7,
                "task_type": "build_knowledge_base_version",
                "status": "success",
                "current_step": "embedding_index_ready",
                "progress": 100,
                "created_at": "2026-07-30T10:00:00+00:00",
                "finished_at": "2026-07-30T10:05:00+00:00",
            }
        ],
        "total": 1,
        "page": 2,
        "page_size": 10,
    }
    assert captured == {"filter_count": 1, "limit": 10, "offset": 10}
