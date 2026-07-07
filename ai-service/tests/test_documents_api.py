"""Document parse API contract tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.internal.v1 import documents
from app.core.config import settings
from app.core.db import get_session
from app.main import app
from app.models.kb import KbBuildTask


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


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
async def test_parse_document_creates_task_with_complete_payload(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}

    class FakeTaskRepo:
        def __init__(self, session: FakeSession) -> None:
            self.session = session

        async def create_task(
            self,
            knowledge_base_version_id: int,
            task_type: str,
            payload: dict | None = None,
            created_by: int | None = None,
        ) -> KbBuildTask:
            captured["knowledge_base_version_id"] = knowledge_base_version_id
            captured["task_type"] = task_type
            captured["payload"] = payload
            captured["created_by"] = created_by
            return KbBuildTask(
                id=99,
                knowledge_base_version_id=knowledge_base_version_id,
                task_type=task_type,
                status="pending",
                payload_json=payload or {},
            )

    monkeypatch.setattr(documents, "KbBuildTaskRepo", FakeTaskRepo)

    response = await client.post(
        "/internal/v1/documents/3001/parse",
        headers={"X-Internal-Token": settings.internal_token},
        json={
            "knowledge_base_version_id": 1001,
            "course_id": 10,
            "document_id": 2001,
            "object_name": "kb-docs/course-10/document-2001/v3001.pdf",
            "file_ext": ".pdf",
            "checksum_md5": "abc123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"task_id": 99, "status": "pending"}
    assert captured["knowledge_base_version_id"] == 1001
    assert captured["task_type"] == "parse_document"
    assert captured["payload"] == {
        "course_id": 10,
        "document_id": 2001,
        "document_version_id": 3001,
        "object_name": "kb-docs/course-10/document-2001/v3001.pdf",
        "file_ext": ".pdf",
        "checksum_md5": "abc123",
        "markdown_content": None,
    }


@pytest.mark.asyncio
async def test_parse_document_requires_object_name_or_markdown(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/internal/v1/documents/3001/parse",
        headers={"X-Internal-Token": settings.internal_token},
        json={
            "knowledge_base_version_id": 1001,
            "course_id": 10,
            "document_id": 2001,
        },
    )

    assert response.status_code == 422
