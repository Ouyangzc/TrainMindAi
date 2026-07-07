"""知识结构化：page -> Markdown 中间层。阶段 1 仅占位，知识点由人工维护。"""

from app.models.kb import DocumentPage


async def structure_pages_to_markdown(pages: list[DocumentPage]) -> str:
    """将解析后的 page 列表合并为 Markdown 中间层。占位。"""
    parts = []
    for p in pages:
        title = f"# {p.title}" if p.title else f"## 第 {p.page_number} 页"
        parts.append(f"{title}\n\n{p.text or ''}")
    return "\n\n".join(parts)
