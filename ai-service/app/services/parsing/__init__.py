"""Document parsing entry points."""

from app.models.kb import DocumentPage


async def parse_document(
    file_path: str, file_ext: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    """Parse a local file into standard DocumentPage rows."""
    from app.services.parsing.dispatcher import parse_file

    return await parse_file(file_path, file_ext, document_id, document_version_id)


async def parse_markdown(
    content: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    """解析 Markdown 文本到 page 结构。"""

    def _title_from_lines(page_lines: list[str]) -> str:
        for page_line in page_lines:
            if page_line.startswith("# "):
                return page_line[2:].strip()
        return ""

    lines = content.split("\n")
    pages: list[DocumentPage] = []
    current_page_num = 1
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# ") and current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                title = _title_from_lines(current_lines)
                pages.append(
                    DocumentPage(
                        document_id=document_id,
                        document_version_id=document_version_id,
                        page_number=current_page_num,
                        title=title or None,
                        text=text,
                    )
                )
                current_page_num += 1
            current_lines = []

        current_lines.append(line)
        # 简单分页：每 50 行分页，H1 在下一轮开始新页
        if len(current_lines) >= 50:
            text = "\n".join(current_lines).strip()
            if text:
                title = _title_from_lines(current_lines)
                pages.append(
                    DocumentPage(
                        document_id=document_id,
                        document_version_id=document_version_id,
                        page_number=current_page_num,
                        title=title or None,
                        text=text,
                    )
                )
                current_page_num += 1
                current_lines = []

    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            title = _title_from_lines(current_lines)
            pages.append(
                DocumentPage(
                    document_id=document_id,
                    document_version_id=document_version_id,
                    page_number=current_page_num,
                    title=title or None,
                    text=text,
                )
            )

    return pages
