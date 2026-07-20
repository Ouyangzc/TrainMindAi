"""Concrete kb_build_task handlers used by the polling worker."""

import os
from collections.abc import Awaitable, Callable

import jieba
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.kb import EmbeddingIndexVersion, KeywordIndexVersion
from app.repositories.doc_repo import DocumentPageRepo, KnowledgeChunkRepo
from app.repositories.document_task_repo import DocumentParseTaskRepo
from app.repositories.embedding_repo import (
    EmbeddingIndexVersionRepo,
    KeywordIndexVersionRepo,
)
from app.repositories.task_repo import KbBuildTaskRepo
from app.services.chunking import process_title_chunk
from app.services.embedding import run_embedding_pipeline
from app.services.parsing import parse_markdown
from app.services.parsing.dispatcher import parse_file
from app.services.parsing.file_downloader import (
    cleanup_download,
    download_from_object_storage,
)

TaskHandler = Callable[[int, str, dict, AsyncSession], Awaitable[None]]


async def _update_progress(
    session: AsyncSession, task_id: int, step: str, progress: int
) -> None:
    repo = KbBuildTaskRepo(session)
    task = await repo.get(task_id)
    if task is not None:
        await repo.update_progress(task, step, progress)


async def _update_parse_progress(
    session: AsyncSession, task_id: int, step: str, progress: int
) -> None:
    repo = DocumentParseTaskRepo(session)
    task = await repo.get(task_id)
    if task is not None:
        await repo.update_progress(task, step, progress)


def _require_int(payload: dict, key: str) -> int:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"payload.{key} is required")
    return int(value)


async def parse_document_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Parse markdown payload or object storage file into ai.document_page rows."""
    document_id = _require_int(payload, "document_id")
    document_version_id = _require_int(payload, "document_version_id")
    object_name = payload.get("object_name")
    markdown_content = payload.get("markdown_content")

    if not isinstance(object_name, str) and not isinstance(markdown_content, str):
        raise ValueError("payload.object_name or payload.markdown_content is required")

    local_path: str | None = None
    try:
        if isinstance(object_name, str) and object_name.strip():
            await _update_parse_progress(session, task_id, "downloading", 5)
            local_path = await download_from_object_storage(
                bucket=settings.object_storage_bucket,
                object_name=object_name,
                expected_md5=payload.get("checksum_md5"),
            )
            file_ext = payload.get("file_ext") or os.path.splitext(object_name)[1] or ".bin"
            await _update_parse_progress(session, task_id, "parsing", 30)
            pages = await parse_file(
                local_path,
                str(file_ext),
                document_id,
                document_version_id,
            )
        else:
            if not isinstance(markdown_content, str) or not markdown_content.strip():
                raise ValueError("payload.markdown_content is empty")
            await _update_parse_progress(session, task_id, "parsing", 30)
            pages = await parse_markdown(markdown_content, document_id, document_version_id)

        if not pages:
            raise ValueError("parse result is empty")

        await _update_parse_progress(session, task_id, "saving", 80)
        page_repo = DocumentPageRepo(session)
        await page_repo.delete_by_version(document_version_id)
        await page_repo.add_all(pages)
        await _update_parse_progress(session, task_id, "parsed", 100)
    finally:
        cleanup_download(local_path)


async def build_chunk_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Build active knowledge chunks from parsed document pages."""
    course_id = _require_int(payload, "course_id")
    document_id = _require_int(payload, "document_id")
    document_version_id = _require_int(payload, "document_version_id")

    task_repo = KbBuildTaskRepo(session)
    task = await task_repo.get(task_id)
    if task is None:
        raise ValueError(f"task not found: {task_id}")
    kb_version_id = task.knowledge_base_version_id

    await task_repo.update_progress(task, "loading_pages", 10)
    page_repo = DocumentPageRepo(session)
    pages = await page_repo.list_by_version(document_version_id)
    if not pages:
        raise ValueError(f"document pages not found: {document_version_id}")

    await task_repo.update_progress(task, "chunking", 40)
    chunks = await process_title_chunk(
        session,
        knowledge_base_version_id=kb_version_id,
        course_id=course_id,
        document_id=document_id,
        document_version_id=document_version_id,
        pages=pages,
    )

    chunk_repo = KnowledgeChunkRepo(session)
    await chunk_repo.delete_by_version(kb_version_id)
    await chunk_repo.add_all(chunks)
    await task_repo.update_progress(task, "chunked", 100)


async def build_keyword_index_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Write jieba-tokenized tsvectors and register a keyword index version."""
    task_repo = KbBuildTaskRepo(session)
    task = await task_repo.get(task_id)
    if task is None:
        raise ValueError(f"task not found: {task_id}")
    kb_version_id = task.knowledge_base_version_id

    await task_repo.update_progress(task, "loading_chunks", 10)
    chunks = await KnowledgeChunkRepo(session).list_by_version(kb_version_id)

    for index, chunk in enumerate(chunks, start=1):
        tokenized = " ".join(jieba.cut(chunk.chunk_text))
        await session.execute(
            text(
                "UPDATE ai.knowledge_chunk "
                "SET tsv = to_tsvector('simple', :tokenized) "
                "WHERE id = :chunk_id"
            ),
            {"tokenized": tokenized, "chunk_id": chunk.id},
        )
        if chunks:
            progress = 10 + int(index / len(chunks) * 70)
            await task_repo.update_progress(task, "building_keyword_index", progress)

    index_version = KeywordIndexVersion(
        knowledge_base_version_id=kb_version_id,
        index_engine="pg_fts",
        analyzer="jieba+simple",
        index_name=f"ai.knowledge_chunk.tsv@{kb_version_id}",
        chunk_count=len(chunks),
        status="ready",
    )
    await KeywordIndexVersionRepo(session).add(index_version)
    await task_repo.update_progress(task, "keyword_index_ready", 100)


async def build_embedding_index_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Create or use an embedding index version, then fill chunk embeddings."""
    task_repo = KbBuildTaskRepo(session)
    task = await task_repo.get(task_id)
    if task is None:
        raise ValueError(f"task not found: {task_id}")

    emb_idx_id = payload.get("embedding_index_version_id")
    if emb_idx_id is None:
        index_version = EmbeddingIndexVersion(
            knowledge_base_version_id=task.knowledge_base_version_id,
            embedding_model=settings.embedding_model,
            embedding_model_version=payload.get("embedding_model_version", "default"),
            embedding_dim=settings.embedding_dim,
            vector_store=settings.vector_store,
            collection_name=None,
            status="building",
        )
        index_version = await EmbeddingIndexVersionRepo(session).add(index_version)
        emb_idx_id = index_version.id

    await task_repo.update_progress(task, "embedding", 20)
    await run_embedding_pipeline(session, int(emb_idx_id))
    await task_repo.update_progress(task, "embedding_index_ready", 100)


async def structure_knowledge_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """MVP placeholder for manually maintained knowledge structure."""
    await _update_progress(session, task_id, "structure_skipped", 100)


async def build_knowledge_base_version_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Run the MVP build chain for one knowledge_base_version."""
    task_repo = KbBuildTaskRepo(session)
    task = await task_repo.get(task_id)
    if task is None:
        raise ValueError(f"task not found: {task_id}")

    result = await session.execute(
        text(
            "SELECT d.course_id, s.document_id, s.document_version_id "
            "FROM public.knowledge_base_version_document s "
            "JOIN public.course_document d ON d.id = s.document_id "
            "JOIN public.course_document_version v ON v.id = s.document_version_id "
            "WHERE s.knowledge_base_version_id = :version_id "
            "AND s.del_flag = '0' AND d.del_flag = '0' "
            "AND v.del_flag = '0' AND v.status = 'parsed' "
            "ORDER BY s.id"
        ),
        {"version_id": task.knowledge_base_version_id},
    )
    documents = result.mappings().all()
    if not documents:
        raise ValueError("knowledge base snapshot is empty")

    chunk_repo = KnowledgeChunkRepo(session)
    await chunk_repo.delete_by_version(task.knowledge_base_version_id)
    all_chunks = []
    for index, document in enumerate(documents, start=1):
        pages = await DocumentPageRepo(session).list_by_version(document["document_version_id"])
        if not pages:
            raise ValueError(
                f"document pages not found: {document['document_version_id']}"
            )
        chunks = await process_title_chunk(
            session,
            knowledge_base_version_id=task.knowledge_base_version_id,
            course_id=document["course_id"],
            document_id=document["document_id"],
            document_version_id=document["document_version_id"],
            pages=pages,
        )
        all_chunks.extend(chunks)
        await task_repo.update_progress(
            task, "chunking_documents", int(index / len(documents) * 60)
        )
    await chunk_repo.add_all(all_chunks)
    await build_keyword_index_task(task_id, "build_keyword_index", payload, session)
    await build_embedding_index_task(task_id, "build_embedding_index", payload, session)


async def rebuild_knowledge_base_version_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Rebuild uses the same isolated version build chain in MVP."""
    await build_knowledge_base_version_task(
        task_id, "build_knowledge_base_version", payload, session
    )


HANDLERS: dict[str, TaskHandler] = {
    "parse_document": parse_document_task,
    "structure_knowledge": structure_knowledge_task,
    "build_chunk": build_chunk_task,
    "build_embedding_index": build_embedding_index_task,
    "build_keyword_index": build_keyword_index_task,
    "build_knowledge_base_version": build_knowledge_base_version_task,
    "rebuild_knowledge_base_version": rebuild_knowledge_base_version_task,
}
