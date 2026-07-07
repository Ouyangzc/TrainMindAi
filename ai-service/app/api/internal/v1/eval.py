"""RAG 离线评估。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.eval import RagEvalRun
from app.repositories.eval_repo import RagEvalRunRepo

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/runs")
async def create_run(
    dataset_id: int,
    kb_version_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """触发离线评估：固定 kb_version，跑改写->混合检索->生成，算指标。"""
    repo = RagEvalRunRepo(session)
    run = await repo.add(
        RagEvalRun(
            dataset_id=dataset_id,
            knowledge_base_version_id=kb_version_id,
        )
    )
    await session.commit()
    return {"run_id": run.id, "status": run.status}


@router.get("/runs/{run_id}")
async def get_run(
    run_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """评估结果查询。"""
    repo = RagEvalRunRepo(session)
    run = await repo.get(run_id)
    if run is None:
        from app.api.internal.v1._stub import not_implemented as _ni  # noqa: PLC0415

        raise _ni("评估结果查询")
    return {
        "run_id": run.id,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
