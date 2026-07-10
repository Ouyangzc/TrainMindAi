"""资料文件解析任务仓储。"""

from datetime import UTC, datetime

from sqlalchemy import select

from app.models.document_task import DocumentParseTask
from app.repositories.base import BaseRepository


class DocumentParseTaskRepo(BaseRepository[DocumentParseTask]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, DocumentParseTask)

    async def claim_pending(self) -> DocumentParseTask | None:
        stmt = (
            select(DocumentParseTask)
            .where(
                DocumentParseTask.status == "pending",
                DocumentParseTask.del_flag == "0",
            )
            .order_by(DocumentParseTask.create_time)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()
        if task is not None:
            task.status = "running"
            task.started_at = _now()
            task.update_time = _now()
            await self.session.flush()
        return task

    async def update_progress(
        self, task: DocumentParseTask, step: str, progress: int
    ) -> None:
        task.current_step = step
        task.progress = progress
        task.update_time = _now()
        await self.session.flush()

    async def mark_success(self, task: DocumentParseTask) -> None:
        task.status = "success"
        task.progress = 100
        task.finished_at = _now()
        task.update_time = _now()
        await self.session.flush()

    async def mark_failed(
        self, task: DocumentParseTask, error_code: str, error_message: str
    ) -> None:
        task.status = "failed"
        task.error_code = error_code
        task.error_message = error_message[:1000]
        task.finished_at = _now()
        task.update_time = _now()
        await self.session.flush()

    async def create_task(
        self,
        document_id: int,
        document_version_id: int,
        payload: dict,
        tenant_id: int = 1,
    ) -> DocumentParseTask:
        task = DocumentParseTask(
            tenant_id=tenant_id,
            document_id=document_id,
            document_version_id=document_version_id,
            payload_json=payload,
            create_by="ai-service",
        )
        return await self.add(task)


def _now() -> datetime:
    """返回与 PostgreSQL timestamp 字段匹配的无时区 UTC 时间。"""
    return datetime.now(UTC).replace(tzinfo=None)
