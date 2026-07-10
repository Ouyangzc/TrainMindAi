"""资料文件解析任务查询与重试。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.document_task_repo import DocumentParseTaskRepo

router = APIRouter(prefix="/document-parse-tasks", tags=["document-parse-tasks"])


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = DocumentParseTaskRepo(session)
    task = await repo.get(task_id)
    if task is None or task.del_flag != "0":
        raise HTTPException(status_code=404, detail="document parse task not found")
    return {
        "task_id": task.id,
        "document_id": task.document_id,
        "document_version_id": task.document_version_id,
        "status": task.status,
        "current_step": task.current_step,
        "progress": task.progress,
        "error_code": task.error_code,
        "error_message": task.error_message,
        "retry_count": task.retry_count,
        "created_at": task.create_time.isoformat() if task.create_time else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = DocumentParseTaskRepo(session)
    task = await repo.get(task_id)
    if task is None or task.del_flag != "0":
        raise HTTPException(status_code=404, detail="document parse task not found")
    if task.status != "failed":
        return {"task_id": task.id, "status": task.status, "message": "任务未失败，不可重试"}
    task.status = "pending"
    task.current_step = None
    task.progress = 0
    task.error_code = None
    task.error_message = None
    task.started_at = None
    task.finished_at = None
    task.retry_count += 1
    await session.commit()
    return {"task_id": task.id, "status": task.status}
