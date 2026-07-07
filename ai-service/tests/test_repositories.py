"""Repository 层测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.kb import KbBuildTask
from app.repositories.task_repo import KbBuildTaskRepo


@pytest.mark.asyncio
async def test_claim_pending_returns_none_when_no_task(mock_session) -> None:  # noqa: ANN001
    """无 pending 任务时 claim_pending 返回 None。"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = KbBuildTaskRepo(mock_session)
    task = await repo.claim_pending()
    assert task is None


@pytest.mark.asyncio
async def test_claim_pending_returns_task(mock_session) -> None:  # noqa: ANN001
    """有 pending 任务时 claim_pending 返回任务并置 running。"""
    task_expected = KbBuildTask(
        id=1,
        knowledge_base_version_id=1,
        task_type="parse_document",
        status="pending",
        created_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = task_expected
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = KbBuildTaskRepo(mock_session)
    task = await repo.claim_pending()
    assert task is not None
    assert task.status == "running"


@pytest.mark.asyncio
async def test_create_task(mock_session) -> None:  # noqa: ANN001
    """创建 KbBuildTask 并检查字段。"""
    repo = KbBuildTaskRepo(mock_session)
    task = await repo.create_task(
        knowledge_base_version_id=1,
        task_type="parse_document",
        payload={"document_version_id": 42},
    )
    assert task.knowledge_base_version_id == 1
    assert task.task_type == "parse_document"


@pytest.mark.asyncio
async def test_mark_success(mock_session) -> None:  # noqa: ANN001
    """标记任务成功。"""
    repo = KbBuildTaskRepo(mock_session)
    task = KbBuildTask(
        id=1,
        knowledge_base_version_id=1,
        task_type="build_chunk",
        status="running",
        created_at=datetime.now(UTC),
    )
    await repo.mark_success(task)
    assert task.status == "success"
    assert task.progress == 100
    assert task.finished_at is not None


@pytest.mark.asyncio
async def test_mark_failed(mock_session) -> None:  # noqa: ANN001
    """标记任务失败。"""
    repo = KbBuildTaskRepo(mock_session)
    task = KbBuildTask(
        id=2,
        knowledge_base_version_id=1,
        task_type="build_embedding_index",
        status="running",
        created_at=datetime.now(UTC),
    )
    await repo.mark_failed(task, "EMBED_ERROR", "embedding api timeout")
    assert task.status == "failed"
    assert task.error_code == "EMBED_ERROR"
    assert task.error_message == "embedding api timeout"
