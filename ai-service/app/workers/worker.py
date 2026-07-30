"""后台 Worker：轮询资料解析任务和知识库构建任务。

启动： uv run python -m app.workers.worker
"""

import asyncio
import time

from redis.asyncio import Redis as AsyncRedis

from app.core.db import SessionLocal
from app.core.errors import AppError
from app.core.logging import get_logger, setup_logging
from app.core.metrics import (
    kb_build_task_duration_seconds,
    kb_build_tasks_failed_total,
    kb_build_tasks_running,
    kb_build_tasks_total,
)
from app.core.redis import redis_client
from app.repositories.document_task_repo import DocumentParseTaskRepo
from app.repositories.task_repo import KbBuildTaskRepo
from app.workers.handlers import parse_document_task
from app.workers.pipeline import dispatch

POLL_INTERVAL_SECONDS = 5
_LOCK_TTL_SECONDS = 300
_RETRY_KEY = "retry:tasks"
_MAX_RETRIES = 3
_NON_RETRYABLE_ERROR_CODES = {
    "NOT_IMPLEMENTED",
    "PARSE_UNSUPPORTED",
    "PARSE_ENCRYPTED",
    "PARSE_CORRUPTED",
}

setup_logging()
log = get_logger("worker")


async def acquire_task_lock(
    redis: AsyncRedis, task_type: str, kb_version_id: int
) -> bool:
    """Acquire a Redis lock for one task type on one KB version."""
    lock_key = f"lock:{task_type}:{kb_version_id}"
    return bool(await redis.set(lock_key, "1", nx=True, ex=_LOCK_TTL_SECONDS))


async def release_task_lock(
    redis: AsyncRedis, task_type: str, kb_version_id: int
) -> None:
    """Release a Redis task lock."""
    lock_key = f"lock:{task_type}:{kb_version_id}"
    await redis.delete(lock_key)


async def schedule_retry(
    redis: AsyncRedis, task_id: int, delay_seconds: int
) -> None:
    """Schedule a KB build task retry."""
    await redis.zadd(_RETRY_KEY, {str(task_id): time.time() + delay_seconds})


async def pop_due_retries(redis: AsyncRedis) -> list[int]:
    """Pop retry task IDs whose scheduled time has arrived."""
    now = time.time()
    ids = await redis.zrangebyscore(_RETRY_KEY, 0, now)
    if ids:
        await redis.zremrangebyscore(_RETRY_KEY, 0, now)
    task_ids: list[int] = []
    for raw_id in ids:
        if isinstance(raw_id, tuple):
            raw_id = raw_id[0]
        if isinstance(raw_id, bytes):
            raw_id = raw_id.decode()
        task_ids.append(int(str(raw_id)))
    return task_ids


def _retry_delay_seconds(retry_count: int) -> int:
    if retry_count <= 1:
        return 5
    return 30


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, AppError):
        return exc.code not in _NON_RETRYABLE_ERROR_CODES
    return True


async def _claim_and_run_parse_once() -> bool:
    """抢占并执行一个资料解析任务。"""
    async with SessionLocal() as session:
        repo = DocumentParseTaskRepo(session)
        task = await repo.claim_pending()
        if task is None:
            return False

        log.info(
            "worker.claim_parse_task",
            task_id=task.id,
            document_version_id=task.document_version_id,
        )
        try:
            await parse_document_task(
                task.id, "parse_document", task.payload_json or {}, session
            )
            await repo.mark_success(task)
            log.info("worker.parse_task_success", task_id=task.id)
        except Exception as exc:  # noqa: BLE001
            await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
            log.exception("worker.parse_task_failed", task_id=task.id)
        finally:
            await session.commit()
    return True


async def _claim_and_run_kb_once() -> bool:
    """抢占并执行一个知识库构建任务。"""
    async with SessionLocal() as session:
        repo = KbBuildTaskRepo(session)
        retryable_ids: list[int] = []
        try:
            retryable_ids = await pop_due_retries(redis_client)
        except Exception:  # noqa: BLE001
            log.warning("worker.retry_queue_unavailable")

        task = await repo.claim_pending(retryable_ids=retryable_ids or None)
        if task is None:
            return False

        log.info(
            "worker.claim_task",
            task_id=task.id,
            task_type=task.task_type,
            kb_version_id=task.knowledge_base_version_id,
        )

        lock_managed = False
        try:
            lock_acquired = await acquire_task_lock(
                redis_client,
                task.task_type,
                task.knowledge_base_version_id,
            )
            lock_managed = lock_acquired
        except Exception:  # noqa: BLE001
            lock_acquired = True
            log.warning("worker.redis_lock_unavailable", task_id=task.id)

        if not lock_acquired:
            task.status = "pending"
            task.started_at = None
            await session.commit()
            log.info(
                "worker.task_lock_deferred",
                task_id=task.id,
                task_type=task.task_type,
                kb_version_id=task.knowledge_base_version_id,
            )
            return True

        start_time = time.monotonic()
        kb_build_tasks_running.inc()

        try:
            await dispatch(task.id, task.task_type, task.payload_json or {}, session)
            await repo.mark_success(task)
            kb_build_tasks_total.labels(status="success").inc()
            log.info("worker.task_success", task_id=task.id)
        except NotImplementedError:
            await repo.mark_failed(task, "NOT_IMPLEMENTED", "handler not implemented")
            kb_build_tasks_total.labels(status="failed").inc()
            kb_build_tasks_failed_total.labels(error_code="NOT_IMPLEMENTED").inc()
            log.warning("worker.task_not_implemented", task_id=task.id, task_type=task.task_type)
        except Exception as exc:  # noqa: BLE001
            task.retry_count = (task.retry_count or 0) + 1
            if task.retry_count < _MAX_RETRIES and _is_retryable_exception(exc):
                delay_seconds = _retry_delay_seconds(task.retry_count)
                try:
                    await schedule_retry(redis_client, task.id, delay_seconds)
                    await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
                    kb_build_tasks_total.labels(status="retry_scheduled").inc()
                    log.warning(
                        "worker.task_retry_scheduled",
                        task_id=task.id,
                        task_type=task.task_type,
                        retry_count=task.retry_count,
                        delay_seconds=delay_seconds,
                    )
                except Exception:  # noqa: BLE001
                    await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
                    kb_build_tasks_total.labels(status="failed").inc()
                    kb_build_tasks_failed_total.labels(error_code="HANDLER_ERROR").inc()
                    log.warning("worker.retry_schedule_failed", task_id=task.id)
            else:
                await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
                kb_build_tasks_total.labels(status="failed").inc()
                kb_build_tasks_failed_total.labels(error_code="HANDLER_ERROR").inc()
            log.exception("worker.task_failed", task_id=task.id, task_type=task.task_type)
        finally:
            kb_build_tasks_running.dec()
            kb_build_task_duration_seconds.labels(task_type=task.task_type).observe(
                time.monotonic() - start_time
            )
            if lock_managed:
                try:
                    await release_task_lock(
                        redis_client,
                        task.task_type,
                        task.knowledge_base_version_id,
                    )
                except Exception:  # noqa: BLE001
                    log.warning("worker.redis_lock_release_failed", task_id=task.id)
            await session.commit()
    return True


async def run() -> None:
    log.info("worker.start", poll_interval=POLL_INTERVAL_SECONDS)
    while True:
        try:
            handled = await _claim_and_run_parse_once()
            if not handled:
                handled = await _claim_and_run_kb_once()
        except Exception:  # noqa: BLE001
            log.exception("worker.loop_error")
            handled = False
        if not handled:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
