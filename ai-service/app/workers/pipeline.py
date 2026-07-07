"""task_type -> handler 路由。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.handlers import HANDLERS

# task_type 取值见表结构文档 §kb_build_task
TASK_TYPES = (
    "parse_document",
    "structure_knowledge",
    "build_chunk",
    "build_embedding_index",
    "build_keyword_index",
    "build_knowledge_base_version",
    "rebuild_knowledge_base_version",
)


async def dispatch(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    handler = HANDLERS.get(task_type)
    if handler is None:
        raise ValueError(f"未知 task_type: {task_type}")
    await handler(task_id, task_type, payload, session)
