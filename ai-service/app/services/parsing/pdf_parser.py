"""PDF parser."""

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError
from app.models.kb import DocumentPage


def _title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:512]
    return fallback


async def parse_pdf(
    file_path: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    """Extract text pages from a text-based PDF."""
    try:
        reader = PdfReader(file_path)
    except PdfReadError as exc:
        raise AppError("PARSE_CORRUPTED", "PDF 文件损坏", http_status=400) from exc
    except Exception as exc:
        raise AppError("PARSE_CORRUPTED", "PDF 文件无法读取", http_status=400) from exc

    if getattr(reader, "is_encrypted", False):
        raise AppError("PARSE_ENCRYPTED", "PDF 文件已加密", http_status=400)

    pages: list[DocumentPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=index,
                title=_title_from_text(text, f"第 {index} 页"),
                text=text,
            )
        )

    if not pages:
        raise AppError("PARSE_UNSUPPORTED", "扫描版 PDF 暂不支持解析", http_status=400)

    return pages
