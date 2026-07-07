"""Parser dispatcher."""

from app.core.errors import AppError
from app.models.kb import DocumentPage
from app.services.parsing import parse_markdown
from app.services.parsing.docx_parser import parse_docx
from app.services.parsing.pdf_parser import parse_pdf
from app.services.parsing.pptx_parser import parse_pptx
from app.services.parsing.xlsx_parser import parse_xlsx


async def parse_file(
    file_path: str, file_ext: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    """Route a local file to the matching parser."""
    ext = file_ext.lower().strip()
    if ext and not ext.startswith("."):
        ext = f".{ext}"

    if ext == ".pdf":
        return await parse_pdf(file_path, document_id, document_version_id)
    if ext == ".pptx":
        return await parse_pptx(file_path, document_id, document_version_id)
    if ext == ".docx":
        return await parse_docx(file_path, document_id, document_version_id)
    if ext == ".xlsx":
        return await parse_xlsx(file_path, document_id, document_version_id)
    if ext in {".md", ".markdown"}:
        with open(file_path, encoding="utf-8") as file:
            return await parse_markdown(file.read(), document_id, document_version_id)

    raise AppError(
        "PARSE_UNSUPPORTED_FORMAT",
        f"不支持的文件格式: {file_ext}",
        http_status=400,
    )
