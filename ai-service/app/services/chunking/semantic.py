"""Semantic chunk strategy based on Markdown and sentence boundaries."""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb import DocumentPage, KnowledgeChunk
from app.services.chunking import _chunk_hash, process_fixed_size_chunk

_LIST_BOUNDARY = re.compile(r"^(\s*[-*+]\s+|\s*\d+[.)]\s+)")
_SENTENCE_BOUNDARIES = "。！？；.!?;"


def _has_semantic_structure(text: str) -> bool:
    if "\n\n" in text:
        return True
    if any(mark in text for mark in _SENTENCE_BOUNDARIES):
        return True
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith(("#", ">", "```"))
            or _LIST_BOUNDARY.match(stripped) is not None
        ):
            return True
    return False


def _split_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code_block = False

    def flush() -> None:
        nonlocal current
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)
        current = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code_block and current:
                flush()
            current.append(line)
            in_code_block = not in_code_block
            if not in_code_block:
                flush()
            continue

        if in_code_block:
            current.append(line)
            continue

        if not stripped:
            flush()
            continue

        if stripped.startswith(("#", ">")) or _LIST_BOUNDARY.match(stripped):
            if current:
                flush()
            current.append(line)
            flush()
            continue

        current.append(line)

    flush()
    return blocks


def _split_overlong_block(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    pieces: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        limit = min(start + chunk_size, text_len)
        if limit == text_len:
            piece = text[start:].strip()
            if piece:
                pieces.append(piece)
            break

        boundary = -1
        for index in range(limit - 1, start, -1):
            if text[index] in _SENTENCE_BOUNDARIES:
                boundary = index + 1
                break

        if boundary == -1:
            for index in range(limit - 1, start, -1):
                if text[index].isspace():
                    boundary = index
                    break

        if boundary <= start:
            boundary = limit

        piece = text[start:boundary].strip()
        if piece:
            pieces.append(piece)
        start = boundary
        while start < text_len and text[start].isspace():
            start += 1

    return pieces


async def process_semantic_chunk(
    session: AsyncSession,
    knowledge_base_version_id: int,
    course_id: int,
    document_id: int,
    document_version_id: int,
    pages: list[DocumentPage],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    strategy_version: str = "semantic@1",
) -> list[KnowledgeChunk]:
    """Split text on Markdown blocks and sentence boundaries."""
    full_text = "\n".join(page.text or "" for page in pages).strip()
    if not full_text:
        return []

    chunk_size = max(chunk_size, 1)
    if not _has_semantic_structure(full_text):
        return await process_fixed_size_chunk(
            session,
            knowledge_base_version_id,
            course_id,
            document_id,
            document_version_id,
            pages,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy_version="fixed_size@1",
        )

    chunks: list[KnowledgeChunk] = []
    for page in pages:
        text = (page.text or "").strip()
        if not text:
            continue
        for block in _split_markdown_blocks(text):
            for piece in _split_overlong_block(block, chunk_size):
                chunks.append(
                    KnowledgeChunk(
                        knowledge_base_version_id=knowledge_base_version_id,
                        course_id=course_id,
                        document_id=document_id,
                        document_version_id=document_version_id,
                        chunk_text=piece,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        chunk_hash=_chunk_hash(piece, strategy_version),
                        chunk_strategy_version=strategy_version,
                        metadata_json={"strategy": "semantic"},
                    )
                )

    return chunks
