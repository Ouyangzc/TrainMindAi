"""后台 Worker：轮询 ai.kb_build_task 抢占待处理任务并执行。

启动： uv run python -m app.workers.worker
"""

import asyncio

from app.core.db import SessionLocal
from app.core.logging import get_logger, setup_logging
from app.repositories.task_repo import KbBuildTaskRepo
from app.workers.pipeline import dispatch

POLL_INTERVAL_SECONDS = 5

setup_logging()
log = get_logger("worker")


async def _claim_and_run_once() -> bool:
    """抢占并执行一个任务。返回是否处理了任务。"""
    async with SessionLocal() as session:
        repo = KbBuildTaskRepo(session)
        task = await repo.claim_pending()
        if task is None:
            return False

        log.info(
            "worker.claim_task",
            task_id=task.id,
            task_type=task.task_type,
            kb_version_id=task.knowledge_base_version_id,
        )

        try:
            await dispatch(task.id, task.task_type, task.payload_json or {}, session)
            await repo.mark_success(task)
            log.info("worker.task_success", task_id=task.id)
        except NotImplementedError:
            await repo.mark_failed(task, "NOT_IMPLEMENTED", "handler not implemented")
            log.warning("worker.task_not_implemented", task_id=task.id, task_type=task.task_type)
        except Exception as exc:  # noqa: BLE001
            await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
            log.exception("worker.task_failed", task_id=task.id, task_type=task.task_type)
        finally:
            await session.commit()
    return True


async def run() -> None:
    log.info("worker.start", poll_interval=POLL_INTERVAL_SECONDS)
    while True:
        try:
            handled = await _claim_and_run_once()
        except Exception:  # noqa: BLE001
            log.exception("worker.loop_error")
            handled = False
        if not handled:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
