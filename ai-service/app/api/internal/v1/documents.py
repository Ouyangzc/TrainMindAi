"""文档解析触发（异步）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.task_repo import KbBuildTaskRepo
from app.schemas.common import ParseDocumentRequest, TaskAccepted

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{document_version_id}/parse", response_model=TaskAccepted)
async def parse_document(
    document_version_id: int,
    req: ParseDocumentRequest,
    session: AsyncSession = Depends(get_session),
) -> TaskAccepted:
    """触发文档解析，入队后返回 task_id。"""
    repo = KbBuildTaskRepo(session)
    task = await repo.create_task(
        knowledge_base_version_id=req.knowledge_base_version_id,
        task_type="parse_document",
        payload={
            "course_id": req.course_id,
            "document_id": req.document_id,
            "document_version_id": document_version_id,
            "object_name": req.object_name,
            "file_ext": req.file_ext,
            "checksum_md5": req.checksum_md5,
            "markdown_content": req.markdown_content,
        },
    )
    await session.commit()
    return TaskAccepted(task_id=task.id, status=task.status)
