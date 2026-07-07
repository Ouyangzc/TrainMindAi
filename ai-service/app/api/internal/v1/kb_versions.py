"""知识库版本构建/重建触发（异步）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.task_repo import KbBuildTaskRepo
from app.schemas.common import TaskAccepted

router = APIRouter(prefix="/kb-versions", tags=["kb-versions"])


@router.post("/{kb_version_id}/build", response_model=TaskAccepted)
async def build(
    kb_version_id: int,
    session: AsyncSession = Depends(get_session),
) -> TaskAccepted:
    """构建知识库版本（parse->chunk->embedding->index）。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.create_task(
        knowledge_base_version_id=kb_version_id,
        task_type="build_knowledge_base_version",
    )
    await session.commit()
    return TaskAccepted(task_id=task.id, status=task.status)


@router.post("/{kb_version_id}/rebuild", response_model=TaskAccepted)
async def rebuild(
    kb_version_id: int,
    session: AsyncSession = Depends(get_session),
) -> TaskAccepted:
    """重建知识库版本（不覆盖线上版）。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.create_task(
        knowledge_base_version_id=kb_version_id,
        task_type="rebuild_knowledge_base_version",
    )
    await session.commit()
    return TaskAccepted(task_id=task.id, status=task.status)
