"""构建任务状态查询与重试/取消。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.task_repo import KbBuildTaskRepo

router = APIRouter(prefix="/kb-tasks", tags=["kb-tasks"])


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """查询任务状态/进度/错误。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.get(task_id)
    if task is None:
        from app.api.internal.v1._stub import not_implemented as _ni  # noqa: PLC0415

        raise _ni("任务查询")  # 后续替换为 404
    return {
        "task_id": task.id,
        "task_type": task.task_type,
        "status": task.status,
        "current_step": task.current_step,
        "progress": task.progress,
        "error_code": task.error_code,
        "error_message": task.error_message,
        "retry_count": task.retry_count,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """重试失败任务：重置状态为 pending。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.get(task_id)
    if task is None:
        from app.api.internal.v1._stub import not_implemented as _ni  # noqa: PLC0415

        raise _ni("任务重试")
    if task.status not in ("failed", "success"):
        return {"task_id": task_id, "status": task.status, "message": "任务未结束，不可重试"}
    task.status = "pending"
    task.error_code = None
    task.error_message = None
    task.retry_count = 0
    task.current_step = None
    task.progress = 0
    await session.commit()
    return {"task_id": task_id, "status": task.status}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """取消任务：标记为 cancelled。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.get(task_id)
    if task is None:
        from app.api.internal.v1._stub import not_implemented as _ni  # noqa: PLC0415

        raise _ni("任务取消")
    if task.status in ("success", "failed", "cancelled"):
        return {"task_id": task_id, "status": task.status, "message": "任务已结束"}
    task.status = "cancelled"
    await session.commit()
    return {"task_id": task_id, "status": task.status}
