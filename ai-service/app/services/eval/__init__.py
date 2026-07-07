"""RAG 离线评估 runner + 指标。脚手架阶段为占位。"""

from sqlalchemy.ext.asyncio import AsyncSession


async def run_evaluation(
    session: AsyncSession,
    dataset_id: int,
    knowledge_base_version_id: int,
    run_id: int,
) -> None:
    """评估 runner。占位实现。"""
    raise NotImplementedError("RAG 离线评估待实现")
