"""Worker concurrency tests."""

from unittest.mock import AsyncMock

import pytest

from app.models.kb import KbBuildTask
from app.workers.worker import (
    acquire_task_lock,
    pop_due_retries,
    release_task_lock,
    schedule_retry,
)


@pytest.mark.asyncio
async def test_acquire_lock_success() -> None:
    """获取锁成功应返回 True。"""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True

    result = await acquire_task_lock(mock_redis, "build_chunk", 1)

    assert result is True
    mock_redis.set.assert_awaited_once_with(
        "lock:build_chunk:1",
        "1",
        nx=True,
        ex=300,
    )


@pytest.mark.asyncio
async def test_acquire_lock_failure() -> None:
    """锁已存在应返回 False。"""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = None

    result = await acquire_task_lock(mock_redis, "build_chunk", 1)

    assert result is False


@pytest.mark.asyncio
async def test_release_lock() -> None:
    """释放锁应删除对应 Redis key。"""
    mock_redis = AsyncMock()

    await release_task_lock(mock_redis, "build_chunk", 1)

    mock_redis.delete.assert_awaited_once_with("lock:build_chunk:1")


@pytest.mark.asyncio
async def test_schedule_retry() -> None:
    """重试任务应写入 Redis ZSET。"""
    mock_redis = AsyncMock()

    await schedule_retry(mock_redis, task_id=3, delay_seconds=5)

    args = mock_redis.zadd.await_args.args
    assert args[0] == "retry:tasks"
    assert "3" in args[1]


@pytest.mark.asyncio
async def test_pop_due_retries() -> None:
    """到期重试任务应从 ZSET 取出并移除。"""
    mock_redis = AsyncMock()
    mock_redis.zrangebyscore.return_value = ["3", "4"]

    task_ids = await pop_due_retries(mock_redis)

    assert task_ids == [3, 4]
    mock_redis.zremrangebyscore.assert_awaited_once()


@pytest.mark.asyncio
async def test_kb_worker_defers_task_when_lock_is_held(monkeypatch) -> None:
    """获取锁失败时任务应恢复 pending，且不执行 handler。"""
    from app.workers import worker

    task = KbBuildTask(
        id=1,
        knowledge_base_version_id=10,
        task_type="build_chunk",
        status="running",
        payload_json={},
    )

    class FakeSession:
        def __init__(self) -> None:
            self.commit_count = 0

        async def commit(self) -> None:
            self.commit_count += 1

    session = FakeSession()

    class FakeSessionContext:
        async def __aenter__(self) -> FakeSession:
            return session

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

    class FakeTaskRepo:
        def __init__(self, session_arg) -> None:  # noqa: ANN001
            self.session = session_arg

        async def claim_pending(self, retryable_ids=None) -> KbBuildTask:  # noqa: ANN001
            return task

    async def fail_dispatch(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise AssertionError("dispatch should not run when lock is held")

    mock_redis = AsyncMock()
    mock_redis.set.return_value = None
    mock_redis.zrangebyscore.return_value = []

    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(worker, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(worker, "redis_client", mock_redis)
    monkeypatch.setattr(worker, "dispatch", fail_dispatch)

    handled = await worker._claim_and_run_kb_once()

    assert handled is True
    assert task.status == "pending"
    assert task.started_at is None
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_kb_worker_schedules_retry_on_transient_error(monkeypatch) -> None:
    """构建任务 transient 失败时应记录 retry_count 并写入重试队列。"""
    from app.workers import worker

    task = KbBuildTask(
        id=2,
        knowledge_base_version_id=10,
        task_type="build_chunk",
        status="running",
        payload_json={},
        retry_count=0,
    )

    class FakeSession:
        def __init__(self) -> None:
            self.commit_count = 0

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            self.commit_count += 1

    session = FakeSession()

    class FakeSessionContext:
        async def __aenter__(self) -> FakeSession:
            return session

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

    class FakeTaskRepo:
        def __init__(self, session_arg) -> None:  # noqa: ANN001
            self.session = session_arg

        async def claim_pending(self, retryable_ids=None) -> KbBuildTask:  # noqa: ANN001
            return task

        async def mark_failed(
            self, task_arg: KbBuildTask, error_code: str, error_message: str
        ) -> None:
            task_arg.status = "failed"
            task_arg.error_code = error_code
            task_arg.error_message = error_message

    async def fail_dispatch(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise RuntimeError("temporary gateway error")

    mock_redis = AsyncMock()
    mock_redis.set.return_value = True
    mock_redis.zrangebyscore.return_value = []

    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(worker, "KbBuildTaskRepo", FakeTaskRepo)
    monkeypatch.setattr(worker, "redis_client", mock_redis)
    monkeypatch.setattr(worker, "dispatch", fail_dispatch)

    handled = await worker._claim_and_run_kb_once()

    assert handled is True
    assert task.status == "failed"
    assert task.retry_count == 1
    assert task.error_code == "HANDLER_ERROR"
    mock_redis.zadd.assert_awaited_once()
    mock_redis.delete.assert_awaited_once_with("lock:build_chunk:10")
