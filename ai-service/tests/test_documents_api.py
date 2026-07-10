"""Document parse API contract tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.internal.v1 import documents
from app.core.config import settings
from app.core.db import get_session
from app.main import app
from app.models.document_task import DocumentParseTask


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
            document_id: int,
            document_version_id: int,
            payload: dict,
            tenant_id: int = 1,
        ) -> DocumentParseTask:
            captured["document_id"] = document_id
            captured["document_version_id"] = document_version_id
            captured["payload"] = payload
            return DocumentParseTask(
                id=99,
                tenant_id=tenant_id,
                document_id=document_id,
                document_version_id=document_version_id,
                status="pending",
                payload_json=payload,
            )

    monkeypatch.setattr(documents, "DocumentParseTaskRepo", FakeTaskRepo)

    response = await client.post(
        "/internal/v1/documents/3001/parse",
        headers={"X-Internal-Token": settings.internal_token},
        json={
            "course_id": 10,
            "document_id": 2001,
            "object_name": "kb-docs/course-10/document-2001/v3001.pdf",
            "file_ext": ".pdf",
            "checksum_md5": "abc123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"task_id": 99, "status": "pending"}
    assert captured["document_id"] == 2001
    assert captured["document_version_id"] == 3001
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
            "course_id": 10,
            "document_id": 2001,
        },
    )

    assert response.status_code == 422
