"""问答相关 DTO（内部契约，上下文由 Java 解析后传入）。"""

from pydantic import BaseModel


class QaAnswerRequest(BaseModel):
    user_id: int
    course_id: int
    kb_version_id: int
    session_id: int
    message_id: int
    question: str


class QaSource(BaseModel):
    chunk_id: int
    document_id: int
    document_version_id: int
    source_file: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    score: float | None = None


class QaAnswerResponse(BaseModel):
    answer: str
    answer_status: str
    knowledge_base_version_id: int
    sources: list[QaSource] = []
    reject_reason: str | None = None
    retrieval_log_ref: int | None = None
