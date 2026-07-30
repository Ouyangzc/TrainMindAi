"""Worker task handler tests."""

from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_task import DocumentParseTask
from app.models.kb import (
    DocumentPage,
    EmbeddingIndexVersion,
    KbBuildTask,
    KeywordIndexVersion,
    KnowledgeChunk,
)


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

        async def get(self, task_id: int) -> DocumentParseTask:
            return DocumentParseTask(
                id=task_id,
                tenant_id=1,
                document_id=11,
                document_version_id=22,
                status="running",
                create_time=datetime.now(UTC),
            )

        async def update_progress(
            self, task: DocumentParseTask, step: str, progress_value: int
        ) -> None:
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

    monkeypatch.setattr(handlers, "DocumentParseTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)

    await handlers.parse_document_task(
        task_id=9,
        task_type="parse_document",
        payload={
            "document_id": 11,
            "document_version_id": 22,
            "markdown_content": "# 第一章\n\n内容",
        },
        session=cast(AsyncSession, FakeSession()),
    )

    assert deleted_versions == [22]
    assert len(saved_pages) == 1
    assert saved_pages[0].document_id == 11
    assert saved_pages[0].document_version_id == 22
    assert saved_pages[0].title == "第一章"
    assert progress[-1] == ("parsed", 100)


@pytest.mark.asyncio
async def test_parse_document_task_with_object_storage(monkeypatch) -> None:
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

        async def get(self, task_id: int) -> DocumentParseTask:
            return DocumentParseTask(
                id=task_id,
                tenant_id=1,
                document_id=11,
                document_version_id=22,
                status="running",
                create_time=datetime.now(UTC),
            )

        async def update_progress(
            self, task: DocumentParseTask, step: str, progress_value: int
        ) -> None:
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

    monkeypatch.setattr(handlers, "DocumentParseTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)
    monkeypatch.setattr(handlers, "download_from_object_storage", fake_download)
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
        session=cast(AsyncSession, FakeSession()),
    )

    assert download_calls == [
        {
            "bucket": handlers.settings.object_storage_bucket,
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
    deleted_document_versions: list[tuple[int, int]] = []
    process_calls: list[dict] = []

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

        async def delete_by_document_version(
            self, knowledge_base_version_id: int, document_version_id: int
        ) -> int:
            deleted_document_versions.append(
                (knowledge_base_version_id, document_version_id)
            )
            return 0

        async def add_all(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
            saved_chunks.extend(chunks)
            return chunks

    async def fake_process_chunks(session, **kwargs) -> list[KnowledgeChunk]:  # noqa: ANN001, ANN003
        process_calls.append(kwargs)
        return [
            KnowledgeChunk(
                knowledge_base_version_id=kwargs["knowledge_base_version_id"],
                course_id=kwargs["course_id"],
                document_id=kwargs["document_id"],
                document_version_id=kwargs["document_version_id"],
                chunk_text="hello",
                page_start=1,
                page_end=1,
                chunk_hash="hash",
                chunk_strategy_version="fixed@small",
            )
        ]

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)
    monkeypatch.setattr(handlers, "KnowledgeChunkRepo", FakeKnowledgeChunkRepo)
    monkeypatch.setattr(handlers, "process_chunks", fake_process_chunks)

    await handlers.build_chunk_task(
        task_id=10,
        task_type="build_chunk",
        payload={
            "course_id": 2,
            "document_id": 10,
            "document_version_id": 20,
            "chunk_strategy_code": "fixed",
        },
        session=cast(AsyncSession, FakeSession()),
    )

    assert deleted_document_versions == [(5, 20)]
    assert process_calls[0]["strategy_code"] == "fixed"
    assert len(saved_chunks) == 1
    assert saved_chunks[0].knowledge_base_version_id == 5
    assert saved_chunks[0].course_id == 2
    assert saved_chunks[0].document_id == 10


@pytest.mark.asyncio
async def test_build_keyword_index_task_updates_tsv_and_marks_ready(monkeypatch) -> None:
    from app.workers import handlers

    index_versions = []
    session = cast(AsyncSession, FakeSession())

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
    assert cast(FakeSession, session).executed


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

    await dispatch(12, "structure_knowledge", {}, cast(AsyncSession, FakeSession()))

    assert progress == [("structure_skipped", 100)]


@pytest.mark.asyncio
async def test_cleanup_kb_version_artifacts_removes_indexes_and_chunks(
    monkeypatch,
) -> None:
    from app.workers import handlers

    deleted_rows: list[object] = []
    deleted_versions: list[int] = []

    class FakeResult:
        def __init__(self, rows: list[object]) -> None:
            self.rows = rows

        def scalars(self):  # noqa: ANN201
            return self

        def all(self) -> list[object]:
            return self.rows

    class CleanupSession(FakeSession):
        def __init__(self) -> None:
            super().__init__()
            self.results = [
                FakeResult(
                    [
                        EmbeddingIndexVersion(
                            id=1,
                            knowledge_base_version_id=5,
                            embedding_model="m",
                            embedding_model_version="v",
                            embedding_dim=3,
                            vector_store="pgvector",
                            status="building",
                        )
                    ]
                ),
                FakeResult(
                    [
                        KeywordIndexVersion(
                            id=2,
                            knowledge_base_version_id=5,
                            index_engine="pg_fts",
                            status="ready",
                        )
                    ]
                ),
            ]

        async def execute(self, stmt, params=None):  # noqa: ANN001
            self.executed.append((stmt, params))
            return self.results.pop(0)

        async def delete(self, row: object) -> None:
            deleted_rows.append(row)

    class FakeKnowledgeChunkRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def delete_by_version(self, knowledge_base_version_id: int) -> int:
            deleted_versions.append(knowledge_base_version_id)
            return 3

    monkeypatch.setattr(handlers, "KnowledgeChunkRepo", FakeKnowledgeChunkRepo)

    await handlers._cleanup_kb_version_artifacts(
        cast(AsyncSession, CleanupSession()), knowledge_base_version_id=5
    )

    assert [type(row) for row in deleted_rows] == [
        EmbeddingIndexVersion,
        KeywordIndexVersion,
    ]
    assert deleted_versions == [5]


@pytest.mark.asyncio
async def test_build_kb_version_cleans_up_on_index_failure(monkeypatch) -> None:
    from app.workers import handlers

    cleanup_versions: list[int] = []

    class DocumentResult:
        def mappings(self):  # noqa: ANN201
            return self

        def all(self) -> list[dict]:
            return [{"course_id": 2, "document_id": 10, "document_version_id": 20}]

    class BuildSession(FakeSession):
        async def execute(self, stmt, params=None):  # noqa: ANN001
            self.executed.append((stmt, params))
            return DocumentResult()

    class FakeTaskRepo:
        def __init__(self, session) -> None:  # noqa: ANN001
            pass

        async def get(self, task_id: int) -> KbBuildTask:
            return KbBuildTask(
                id=task_id,
                knowledge_base_version_id=5,
                task_type="build_knowledge_base_version",
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
            return 0

        async def add_all(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
            return chunks

    async def fake_process_chunks(session, **kwargs) -> list[KnowledgeChunk]:  # noqa: ANN001, ANN003
        return [
            KnowledgeChunk(
                knowledge_base_version_id=kwargs["knowledge_base_version_id"],
                course_id=kwargs["course_id"],
                document_id=kwargs["document_id"],
                document_version_id=kwargs["document_version_id"],
                chunk_text="hello",
                page_start=1,
                page_end=1,
                chunk_hash="hash",
                chunk_strategy_version="title@1",
            )
        ]

    async def fail_keyword(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise RuntimeError("keyword index failed")

    async def fake_cleanup(session, knowledge_base_version_id: int) -> None:  # noqa: ANN001
        cleanup_versions.append(knowledge_base_version_id)

    monkeypatch.setattr(handlers, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(handlers, "DocumentPageRepo", FakeDocumentPageRepo)
    monkeypatch.setattr(handlers, "KnowledgeChunkRepo", FakeKnowledgeChunkRepo)
    monkeypatch.setattr(handlers, "process_chunks", fake_process_chunks)
    monkeypatch.setattr(handlers, "build_keyword_index_task", fail_keyword)
    monkeypatch.setattr(handlers, "_cleanup_kb_version_artifacts", fake_cleanup)

    with pytest.raises(RuntimeError, match="keyword index failed"):
        await handlers.build_knowledge_base_version_task(
            task_id=99,
            task_type="build_knowledge_base_version",
            payload={},
            session=cast(AsyncSession, BuildSession()),
        )

    assert cleanup_versions == [5]
