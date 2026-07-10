"""通用 DTO：统一错误体、分页。"""

from typing import Any

from pydantic import BaseModel, model_validator


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class TaskAccepted(BaseModel):
    """异步任务受理响应。"""

    task_id: int
    status: str = "pending"


class ParseDocumentRequest(BaseModel):
    """文档解析任务请求。"""

    course_id: int
    document_id: int
    object_name: str | None = None
    file_ext: str | None = None
    checksum_md5: str | None = None
    markdown_content: str | None = None

    @model_validator(mode="after")
    def require_file_or_markdown(self) -> "ParseDocumentRequest":
        has_object = isinstance(self.object_name, str) and bool(self.object_name.strip())
        has_markdown = isinstance(self.markdown_content, str) and bool(
            self.markdown_content.strip()
        )
        if not has_object and not has_markdown:
            raise ValueError("object_name or markdown_content is required")
        return self
