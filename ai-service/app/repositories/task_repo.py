"""KbBuildTask 仓储：任务抢占、状态流转。"""

from datetime import UTC, datetime

from sqlalchemy import select

from app.models.kb import KbBuildTask
from app.repositories.base import BaseRepository


class KbBuildTaskRepo(BaseRepository[KbBuildTask]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, KbBuildTask)

    async def claim_pending(self) -> KbBuildTask | None:
        """抢占一个 pending 任务（FOR UPDATE SKIP LOCKED）。"""
        stmt = (
            select(KbBuildTask)
            .where(KbBuildTask.status == "pending")
            .order_by(KbBuildTask.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()
        if task is not None:
            task.status = "running"
            task.started_at = datetime.now(UTC)
            await self.session.flush()
        return task

    async def update_progress(
        self, task: KbBuildTask, step: str, progress: int
    ) -> None:
        task.current_step = step
        task.progress = progress
        await self.session.flush()

    async def mark_success(self, task: KbBuildTask) -> None:
        task.status = "success"
        task.progress = 100
        task.finished_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_failed(
        self, task: KbBuildTask, error_code: str, error_message: str
    ) -> None:
        task.status = "failed"
        task.error_code = error_code
        task.error_message = error_message
        task.finished_at = datetime.now(UTC)
        await self.session.flush()

    async def create_task(
        self,
        knowledge_base_version_id: int,
        task_type: str,
        payload: dict | None = None,
        created_by: int | None = None,
    ) -> KbBuildTask:
        task = KbBuildTask(
            knowledge_base_version_id=knowledge_base_version_id,
            task_type=task_type,
            payload_json=payload or {},
            created_by=created_by,
        )
        return await self.add(task)
