"""Chunk strategy tests."""

from unittest.mock import MagicMock

import pytest

from app.models.config_tables import ChunkStrategy
from app.models.kb import DocumentPage


def _strategy_result(strategies: list[ChunkStrategy]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = strategies
    return result


@pytest.mark.asyncio
async def test_get_chunk_strategy_from_repo(mock_session) -> None:  # noqa: ANN001
    """应从 ChunkStrategy 表读取策略配置。"""
    from app.repositories.config_repo import ChunkStrategyRepo

    expected = ChunkStrategy(
        strategy_code="title",
        strategy_version="title@1",
        chunk_method="title",
        chunk_size=512,
        chunk_overlap=64,
        enabled=True,
    )
    mock_session.execute.return_value = _strategy_result([expected])

    repo = ChunkStrategyRepo(mock_session)
    strategies = await repo.get_enabled()

    assert len(strategies) == 1
    assert strategies[0].chunk_method == "title"


@pytest.mark.asyncio
async def test_process_chunks_uses_matching_strategy_code(mock_session) -> None:  # noqa: ANN001
    """指定 strategy_code 时应使用匹配策略配置。"""
    from app.services.chunking import process_chunks

    mock_session.execute.return_value = _strategy_result(
        [
            ChunkStrategy(
                strategy_code="title",
                strategy_version="title@1",
                chunk_method="title",
                chunk_size=512,
                chunk_overlap=64,
                enabled=True,
            ),
            ChunkStrategy(
                strategy_code="fixed",
                strategy_version="fixed@small",
                chunk_method="fixed_size",
                chunk_size=8,
                chunk_overlap=0,
                enabled=True,
            ),
        ]
    )
    pages = [
        DocumentPage(
            document_id=1,
            document_version_id=2,
            page_number=1,
            text="abcdefghij\nklmnop",
        )
    ]

    chunks = await process_chunks(
        mock_session,
        knowledge_base_version_id=3,
        course_id=4,
        document_id=1,
        document_version_id=2,
        pages=pages,
        strategy_code="fixed",
    )

    assert len(chunks) >= 2
    assert chunks[0].chunk_strategy_version == "fixed@small"
    assert len(chunks[0].chunk_text) <= 8


@pytest.mark.asyncio
async def test_process_chunks_falls_back_to_title_when_no_strategy(mock_session) -> None:  # noqa: ANN001
    """无启用策略时回退 title@1。"""
    from app.services.chunking import process_chunks

    mock_session.execute.return_value = _strategy_result([])
    pages = [
        DocumentPage(
            document_id=1,
            document_version_id=2,
            page_number=1,
            text="# 第一章\n\n内容\n\n# 第二章\n\n更多内容",
        )
    ]

    chunks = await process_chunks(
        mock_session,
        knowledge_base_version_id=3,
        course_id=4,
        document_id=1,
        document_version_id=2,
        pages=pages,
    )

    assert len(chunks) == 2
    assert chunks[0].chunk_strategy_version == "title@1"
    assert chunks[0].metadata_json == {"title": "第一章"}


@pytest.mark.asyncio
async def test_process_chunks_rejects_unknown_method(mock_session) -> None:  # noqa: ANN001
    """未知 chunk_method 应明确失败。"""
    from app.services.chunking import process_chunks

    mock_session.execute.return_value = _strategy_result(
        [
            ChunkStrategy(
                strategy_code="bad",
                strategy_version="bad@1",
                chunk_method="unknown",
                chunk_size=512,
                chunk_overlap=64,
                enabled=True,
            )
        ]
    )

    with pytest.raises(ValueError, match="unknown chunk_method"):
        await process_chunks(
            mock_session,
            knowledge_base_version_id=3,
            course_id=4,
            document_id=1,
            document_version_id=2,
            pages=[
                DocumentPage(
                    document_id=1,
                    document_version_id=2,
                    page_number=1,
                    text="content",
                )
            ],
            strategy_code="bad",
        )


@pytest.mark.asyncio
async def test_semantic_chunk_splits_at_paragraphs(mock_session) -> None:  # noqa: ANN001
    """Semantic 策略应优先按段落边界切分。"""
    from app.services.chunking.semantic import process_semantic_chunk

    pages = [
        DocumentPage(
            document_id=1,
            document_version_id=2,
            page_number=1,
            text="第一段内容。\n\n第二段内容。\n\n第三段内容。\n\n第四段内容。\n\n第五段内容。",
        )
    ]

    chunks = await process_semantic_chunk(
        mock_session,
        knowledge_base_version_id=3,
        course_id=4,
        document_id=1,
        document_version_id=2,
        pages=pages,
        chunk_size=500,
        chunk_overlap=0,
    )

    assert len(chunks) >= 5
    assert "第一段" in chunks[0].chunk_text
    assert "第二段" in chunks[1].chunk_text
    assert chunks[0].chunk_strategy_version == "semantic@1"


@pytest.mark.asyncio
async def test_semantic_chunk_prefers_sentence_boundary(mock_session) -> None:  # noqa: ANN001
    """超长段落应优先在句末边界切分。"""
    from app.services.chunking.semantic import process_semantic_chunk

    pages = [
        DocumentPage(
            document_id=1,
            document_version_id=2,
            page_number=1,
            text="第一句很长但是完整。第二句也应该完整。第三句用于溢出。",
        )
    ]

    chunks = await process_semantic_chunk(
        mock_session,
        knowledge_base_version_id=3,
        course_id=4,
        document_id=1,
        document_version_id=2,
        pages=pages,
        chunk_size=18,
        chunk_overlap=0,
    )

    assert len(chunks) >= 2
    assert chunks[0].chunk_text.endswith("。")


@pytest.mark.asyncio
async def test_semantic_chunk_falls_back_for_unstructured_text(mock_session) -> None:  # noqa: ANN001
    """无结构长文本应降级 fixed_size。"""
    from app.services.chunking.semantic import process_semantic_chunk

    chunks = await process_semantic_chunk(
        mock_session,
        knowledge_base_version_id=3,
        course_id=4,
        document_id=1,
        document_version_id=2,
        pages=[
            DocumentPage(
                document_id=1,
                document_version_id=2,
                page_number=1,
                text="abcdefghijklmnopqrstuvwxyz",
            )
        ],
        chunk_size=8,
        chunk_overlap=0,
    )

    assert len(chunks) >= 3
    assert chunks[0].chunk_strategy_version == "fixed_size@1"
