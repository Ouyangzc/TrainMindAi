"""Chunk 策略：title / knowledge_point / semantic / fixed_size。"""

import hashlib
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb import DocumentPage, KnowledgeChunk


def _chunk_hash(text: str, strategy_version: str) -> str:
    return hashlib.sha256(
        (text + strategy_version).encode("utf-8")
    ).hexdigest()[:16]


async def process_fixed_size_chunk(
    session: AsyncSession,
    knowledge_base_version_id: int,
    course_id: int,
    document_id: int,
    document_version_id: int,
    pages: list[DocumentPage],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    strategy_version: str = "fixed_size@1",
) -> list[KnowledgeChunk]:
    """固定长度切分（按字符），兜底策略。"""
    chunks: list[KnowledgeChunk] = []

    full_text = ""
    page_map: list[tuple[int, int]] = []
    for page in pages:
        text = page.text or ""
        page_map.append((page.page_number, len(full_text)))
        full_text += text + "\n"

    if not full_text.strip():
        return chunks

    start = 0
    text_len = len(full_text)
    page_idx = 0
    current_page = pages[0].page_number if pages else 0

    while start < text_len:
        end = min(start + chunk_size, text_len)
        if end < text_len:
            last_newline = full_text.rfind("\n", start, end)
            if last_newline > start + chunk_size // 2:
                end = last_newline

        segment = full_text[start:end]
        if not segment.strip():
            start = end
            continue

        while page_idx + 1 < len(page_map) and page_map[page_idx + 1][1] <= start:
            page_idx += 1
            current_page = pages[page_idx].page_number

        chunk = KnowledgeChunk(
            knowledge_base_version_id=knowledge_base_version_id,
            course_id=course_id,
            document_id=document_id,
            document_version_id=document_version_id,
            chunk_text=segment.strip(),
            page_start=current_page,
            page_end=current_page,
            chunk_hash=_chunk_hash(segment, strategy_version),
            chunk_strategy_version=strategy_version,
        )
        chunks.append(chunk)
        start = end - chunk_overlap if end < text_len else text_len

    return chunks


async def process_title_chunk(
    session: AsyncSession,
    knowledge_base_version_id: int,
    course_id: int,
    document_id: int,
    document_version_id: int,
    pages: list[DocumentPage],
    *,
    strategy_version: str = "title@1",
) -> list[KnowledgeChunk]:
    """按 Markdown 标题层级切分。无标题结构时回退 fixed_size。"""

    def _extract_title(text: str) -> str | None:
        m = re.match(r"^#{1,6}\s+(.+)$", text.strip(), re.MULTILINE)
        return m.group(1).strip() if m else None

    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] = {"title": None, "texts": [], "pages": set()}

    for page in pages:
        text = page.text or ""
        lines = text.split("\n")
        for line in lines:
            title = _extract_title(line)
            if title:
                if current_section["texts"]:
                    sections.append(current_section)
                current_section = {
                    "title": title,
                    "texts": [],
                    "pages": {page.page_number},
                }
            else:
                current_section["texts"].append(line)
                current_section["pages"].add(page.page_number)
    if current_section["texts"]:
        sections.append(current_section)

    if len(sections) > 1:
        chunks = []
        for sec in sections:
            text = "\n".join(sec["texts"]).strip()
            if not text:
                continue
            pages_list = sorted(sec["pages"])
            chunk = KnowledgeChunk(
                knowledge_base_version_id=knowledge_base_version_id,
                course_id=course_id,
                document_id=document_id,
                document_version_id=document_version_id,
                chunk_text=text,
                page_start=pages_list[0],
                page_end=pages_list[-1],
                chunk_hash=_chunk_hash(text, strategy_version),
                chunk_strategy_version=strategy_version,
                metadata_json={"title": sec["title"]},
            )
            chunks.append(chunk)
        return chunks

    return await process_fixed_size_chunk(
        session,
        knowledge_base_version_id,
        course_id,
        document_id,
        document_version_id,
        pages,
        strategy_version="fixed_size@1",
    )
