"""Worker task handler tests."""

from datetime import UTC, datetime

import pytest

from app.models.kb import DocumentPage, KbBuildTask, KnowledgeChunk


class FakeSession:
    def __init__(self) -> None:
        self.executed: list[tuple[object, dict | None]] = []

    async def execute(self, stmt, params=None):  # noqa: ANN001
        self.executed.append((stmt, params))

        class Result:
            def fetchall(self):  # noqa: ANN201
                return []

        return Result()

    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_parse_document_task_writes_markdown_pages(monkeypatch) -> None:
    from app.workers import handlers

    progress: list[tuple[str, int]] = []
    saved_pages: list[DocumentPage] = []
    deleted_versions: list[int] = []

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=3,
                task_type="parse_document",
                status="running",
                created_at=datetime.now(UTC),
            )

        async def update_progress(self, task: KbBuildTask, step: str, progress_value: int) -> None:
            progress.append((step, progress_value))

    class FakeDocumentPageRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def delete_by_version(self, document_version_id: int) -> int:
            deleted_versions.append(document_version_id)
            return 0

        async def add_all(self, pages: list[DocumentPage]) -> list[DocumentPage]:
            saved_pages.extend(pages)
            return pages

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)

    await handlers.parse_document_task(
        task_id=9,
        task_type="parse_document",
        payload={
            "document_id": 11,
            "document_version_id": 22,
            "markdown_content": "# 第一章\n\n内容",
        },
        session=FakeSession(),
    )

    assert deleted_versions == [22]
    assert len(saved_pages) == 1
    assert saved_pages[0].document_id == 11
    assert saved_pages[0].document_version_id == 22
    assert saved_pages[0].title == "第一章"
    assert progress[-1] == ("parsed", 100)


@pytest.mark.asyncio
async def test_parse_document_task_with_minio(monkeypatch) -> None:
    from app.workers import handlers

    progress: list[tuple[str, int]] = []
    saved_pages: list[DocumentPage] = []
    deleted_versions: list[int] = []
    download_calls: list[dict] = []
    parse_calls: list[tuple[str, str, int, int]] = []
    cleaned_paths: list[str | None] = []

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=3,
                task_type="parse_document",
                status="running",
                created_at=datetime.now(UTC),
            )

        async def update_progress(self, task: KbBuildTask, step: str, progress_value: int) -> None:
            progress.append((step, progress_value))

    class FakeDocumentPageRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def delete_by_version(self, document_version_id: int) -> int:
            deleted_versions.append(document_version_id)
            return 0

        async def add_all(self, pages: list[DocumentPage]) -> list[DocumentPage]:
            saved_pages.extend(pages)
            return pages

    async def fake_download(**kwargs):  # noqa: ANN202
        download_calls.append(kwargs)
        return "D:/tmp/doc.pdf"

    async def fake_parse(
        local_path: str, file_ext: str, document_id: int, document_version_id: int
    ) -> list[DocumentPage]:
        parse_calls.append((local_path, file_ext, document_id, document_version_id))
        return [
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=1,
                title="PDF",
                text="content",
            )
        ]

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)
    monkeypatch.setattr(handlers, "download_from_minio", fake_download)
    monkeypatch.setattr(handlers, "parse_file", fake_parse)
    monkeypatch.setattr(handlers, "cleanup_download", lambda path: cleaned_paths.append(path))

    await handlers.parse_document_task(
        task_id=9,
        task_type="parse_document",
        payload={
            "document_id": 11,
            "document_version_id": 22,
            "object_name": "kb-docs/doc.pdf",
            "file_ext": ".pdf",
            "checksum_md5": "abc123",
        },
        session=FakeSession(),
    )

    assert download_calls == [
        {
            "bucket": handlers.settings.minio_bucket,
            "object_name": "kb-docs/doc.pdf",
            "expected_md5": "abc123",
        }
    ]
    assert parse_calls == [("D:/tmp/doc.pdf", ".pdf", 11, 22)]
    assert deleted_versions == [22]
    assert len(saved_pages) == 1
    assert progress[-1] == ("parsed", 100)
    assert cleaned_paths == ["D:/tmp/doc.pdf"]


@pytest.mark.asyncio
async def test_build_chunk_task_creates_chunks_from_pages(monkeypatch) -> None:
    from app.workers import handlers

    saved_chunks: list[KnowledgeChunk] = []
    deleted_versions: list[int] = []

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=5,
                task_type="build_chunk",
                status="running",
                created_at=datetime.now(UTC),
            )

        async def update_progress(self, task: KbBuildTask, step: str, progress_value: int) -> None:
            return None

    class FakeDocumentPageRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def list_by_version(self, document_version_id: int) -> list[DocumentPage]:
            return [
                DocumentPage(
                    document_id=10,
                    document_version_id=document_version_id,
                    page_number=1,
                    text="# A\n\nhello",
                )
            ]

    class FakeKnowledgeChunkRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def delete_by_version(self, knowledge_base_version_id: int) -> int:
            deleted_versions.append(knowledge_base_version_id)
            return 0

        async def add_all(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
            saved_chunks.extend(chunks)
            return chunks

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)
    monkeypatch.setattr(handlers, "KnowledgeChunkRepo", FakeKnowledgeChunkRepo)

    await handlers.build_chunk_task(
        task_id=10,
        task_type="build_chunk",
        payload={"course_id": 2, "document_id": 10, "document_version_id": 20},
        session=FakeSession(),
    )

    assert deleted_versions == [5]
    assert len(saved_chunks) == 1
    assert saved_chunks[0].knowledge_base_version_id == 5
    assert saved_chunks[0].course_id == 2
    assert saved_chunks[0].document_id == 10


@pytest.mark.asyncio
async def test_build_keyword_index_task_updates_tsv_and_marks_ready(monkeypatch) -> None:
    from app.workers import handlers

    index_versions = []
    session = FakeSession()

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=8,
                task_type="build_keyword_index",
                status="running",
                created_at=datetime.now(UTC),
            )

        async def update_progress(self, task: KbBuildTask, step: str, progress_value: int) -> None:
            return None

    class FakeKnowledgeChunkRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def list_by_version(
            self, knowledge_base_version_id: int, status: str = "active"
        ) -> list[KnowledgeChunk]:
            return [
                KnowledgeChunk(
                    id=100,
                    knowledge_base_version_id=knowledge_base_version_id,
                    course_id=1,
                    document_id=2,
                    document_version_id=3,
                    chunk_text="机器学习基础",
                    chunk_hash="hash",
                    chunk_strategy_version="fixed_size@1",
                )
            ]

    class FakeKeywordIndexVersionRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def add(self, index_version):  # noqa: ANN001
            index_versions.append(index_version)
            return index_version

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "KnowledgeChunkRepo", FakeKnowledgeChunkRepo)
    monkeypatch.setattr(handlers, "KeywordIndexVersionRepo", FakeKeywordIndexVersionRepo)

    await handlers.build_keyword_index_task(
        task_id=11,
        task_type="build_keyword_index",
        payload={},
        session=session,
    )

    assert len(index_versions) == 1
    assert index_versions[0].knowledge_base_version_id == 8
    assert index_versions[0].chunk_count == 1
    assert index_versions[0].status == "ready"
    assert session.executed


@pytest.mark.asyncio
async def test_dispatch_uses_concrete_handler(monkeypatch) -> None:
    from app.workers import handlers
    from app.workers.pipeline import dispatch

    progress: list[tuple[str, int]] = []

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=1,
                task_type="structure_knowledge",
                status="running",
                created_at=datetime.now(UTC),
            )

        async def update_progress(self, task: KbBuildTask, step: str, progress_value: int) -> None:
            progress.append((step, progress_value))

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)

    await dispatch(12, "structure_knowledge", {}, FakeSession())

    assert progress == [("structure_skipped", 100)]
