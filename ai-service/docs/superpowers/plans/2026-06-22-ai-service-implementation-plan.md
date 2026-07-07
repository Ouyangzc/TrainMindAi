# TrainMindAi ai-service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready AI service covering the full knowledge pipeline: document parsing → chunking → embedding → hybrid retrieval → RAG Q&A → question generation → offline evaluation.

**Architecture:** 5 decoupled phases executed sequentially, each building on the prior. Every task embeds its own robustness (error handling, retry, tests) — no separate "hardening phase." The service is async FastAPI with PostgreSQL (pgvector), Redis, MinIO, and OpenAI-compatible LLM/Embedding gateways.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), pgvector, Redis, MinIO, OpenAI SDK, jieba, pypdf, python-pptx, python-docx, openpyxl, prometheus-client, pytest.

---
## File Structure Overview

Before task-level work, here is the full map of what gets created or modified:

### Phase 1 — Document Parsing Pipeline

```
Create:
  app/services/parsing/pdf_parser.py      # PDF text extraction via pypdf
  app/services/parsing/pptx_parser.py     # PPTX slide extraction via python-pptx
  app/services/parsing/docx_parser.py     # DOCX paragraph extraction via python-docx
  app/services/parsing/xlsx_parser.py     # XLSX sheet extraction via openpyxl
  app/services/parsing/file_downloader.py # MinIO file download with timeout + checksum
  app/services/parsing/dispatcher.py      # Format detection + parser routing
  app/services/parsing/retry.py           # @parse_retry decorator
  app/services/parsing/markdown_parser.py  # Extracted from __init__.py
  tests/test_parsers.py                   # Parser unit tests
  tests/test_file_downloader.py           # Downloader unit tests

Modify:
  pyproject.toml                           # Add pypdf, python-pptx, python-docx, openpyxl
  app/api/internal/v1/documents.py         # Parse task request contract
  app/services/parsing/__init__.py         # Re-export new parsers
  app/workers/handlers.py                  # Integrate download→parse flow
```

### Phase 2 — Pipeline Hardening

```
Create:
  app/services/chunking/semantic.py        # Semantic boundary chunking
  app/core/metrics.py                      # Prometheus metrics definition
  tests/test_worker_concurrency.py         # Concurrency + retry tests

Modify:
  app/services/chunking/__init__.py        # Config-driven strategy dispatch
  app/workers/worker.py                    # Redis-based retry + concurrency
  app/workers/handlers.py                  # Transaction rollback, snapshot update boundary
  app/api/internal/v1/kb_tasks.py          # Batch query endpoint
  app/main.py                              # Mount /metrics
  pyproject.toml                           # Add prometheus-client
```

### Phase 3 — Retrieval + RAG Enhancement

```
Create:
  app/services/retrieval/synonyms.json     # Synonym dictionary
  tests/test_rag_stream.py                 # SSE streaming tests
  tests/test_retrieval_degradation.py      # Degradation tests
  tests/test_mmr.py                        # MMR diversity tests

Modify:
  app/services/retrieval/__init__.py       # Query rewrite + degradation + MMR
  app/services/rag/__init__.py             # SSE + multi-turn + citation check + prompt config
  app/api/internal/v1/qa.py                # Wire up stream endpoint
  app/schemas/qa.py                        # Extend response schemas
```

### Phase 4 — Question Generation / Diagnosis / Grading

```
Create:
  tests/test_generation.py                 # Generation function tests

Modify:
  app/services/generation/__init__.py      # Full implementations
  app/api/internal/v1/questions.py         # Parameter validation
  app/schemas/qa.py                        # QuestionDraft, DiagnoseRequest, GradeResult
```

### Phase 5 — RAG Offline Evaluation

```
Create:
  tests/test_eval.py                       # Evaluation tests

Modify:
  app/services/eval/__init__.py            # Runner + metric calculations
  app/api/internal/v1/eval.py              # Additional endpoints
  app/models/eval.py                       # Add report_json column
  alembic/versions/0004_eval_report_json.py # Migration
```

---

# Phase 1: Document Parsing Pipeline

> **Status:** ✅ Implementation complete on 2026-06-22; coverage report pending because `pytest-cov` is not installed
>
> **Verification:**
> - `uv run pytest` → 30 passed
> - `uv run mypy app` → Success, no issues in 64 source files
> - `uv run ruff check .` → All checks passed
> - `uv run python -c "import pypdf, pptx, docx, openpyxl; print('all ok')"` → all ok

## Task 1.0: Define parse task API contract

**Files:**
- Modify: `app/api/internal/v1/documents.py`
- Modify: `app/schemas/common.py` or create a focused request schema if needed
- Test: `tests/test_documents_api.py` or existing API test file

Phase 1 must start by fixing the API-to-Worker contract. The current endpoint only creates a task with `document_version_id` and `knowledge_base_version_id=0`; that cannot drive MinIO download or real parsing.

- [x] **Step 1: Add request schema**

Define a request body for `POST /internal/v1/documents/{document_version_id}/parse`:

```python
class ParseDocumentRequest(BaseModel):
    knowledge_base_version_id: int
    course_id: int
    document_id: int
    object_name: str | None = None
    file_ext: str | None = None
    checksum_md5: str | None = None
    markdown_content: str | None = None
```

Validation rules:
- `knowledge_base_version_id`, `course_id`, and `document_id` are required.
- Either `object_name` or `markdown_content` is required.
- `markdown_content` is a local/test fallback. Normal business traffic should send `object_name`.
- `file_ext` is optional; if omitted, Worker infers it from `object_name`.

- [x] **Step 2: Write failing API test**

Add a test that posts a complete request and verifies:
- `KbBuildTask.knowledge_base_version_id` equals the request value, not `0`.
- `payload_json` contains `course_id`, `document_id`, `document_version_id`, `object_name`, `file_ext`, and `checksum_md5`.
- Missing both `object_name` and `markdown_content` returns validation error.

- [x] **Step 3: Update endpoint implementation**

`documents.py` should create:

```python
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
```

- [x] **Step 4: Verify**

```bash
uv run pytest tests/test_documents_api.py -v
```

Expected: API contract tests PASS.

## Task 1.1: Add parsing dependencies

**Files:**
- Modify: `pyproject.toml`
- Run: `uv sync`

- [x] **Step 1: Add dependencies to pyproject.toml**

```toml
# Add under [project] dependencies (alphabetical order, before "jieba"):
"openpyxl>=3",
"pypdf>=5",
"python-docx>=1",
"python-pptx>=1",
```

- [x] **Step 2: Sync and verify**

Run:
```bash
uv sync
uv run python -c "import pypdf, pptx, docx, openpyxl; print('all ok')"
```
Expected: `all ok`

---

## Task 1.2: Implement PDF parser

**Files:**
- Create: `app/services/parsing/pdf_parser.py`
- Test: `tests/test_parsers.py` (shared test file for all parsers)

- [x] **Step 1: Write the failing test for PDF parser**

Add to `tests/test_parsers.py`:
```python
import pytest
from app.services.parsing.pdf_parser import parse_pdf
from app.core.errors import AppError


@pytest.mark.asyncio
async def test_parse_pdf_text_page(monkeypatch):
    """文字版 PDF 应正确提取文本和页数。"""
    # Mock pypdf.PdfReader to return 2 text pages
    import pypdf

    class FakePage:
        def __init__(self, text, number):
            self.text = text

    class FakeReader:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def pages(self):
            return [FakePage("第1页内容"), FakePage("# 第二章\n第2页内容")]

    monkeypatch.setattr(pypdf, "PdfReader", FakeReader)

    pages = await parse_pdf("/fake/path.pdf", document_id=1, document_version_id=1)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "第1页内容" in pages[0].text
    assert pages[1].title == "第二章"


@pytest.mark.asyncio
async def test_parse_pdf_encrypted(monkeypatch):
    """加密 PDF 应抛 PARSE_ENCRYPTED。"""
    import pypdf

    def _raise_encrypted(*args, **kwargs):
        raise pypdf.errors.PdfReadError("file has not been decrypted")

    monkeypatch.setattr(pypdf, "PdfReader", _raise_encrypted)

    with pytest.raises(AppError) as exc:
        await parse_pdf("/fake/encrypted.pdf", 1, 1)
    assert exc.value.code == "PARSE_ENCRYPTED"


@pytest.mark.asyncio
async def test_parse_pdf_zero_text_pages(monkeypatch):
    """扫描版 PDF（文本为空）应抛 PARSE_UNSUPPORTED。"""
    import pypdf

    class FakePage:
        def __init__(self):
            self.text = ""

    class FakeReader:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def pages(self):
            return [FakePage(), FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", FakeReader)

    with pytest.raises(AppError) as exc:
        await parse_pdf("/fake/scan.pdf", 1, 1)
    assert exc.value.code == "PARSE_UNSUPPORTED"
```

- [x] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_parsers.py::test_parse_pdf_text_page -v
```
Expected: `FAILED` with ModuleNotFoundError or similar

- [x] **Step 3: Write minimal implementation**

`app/services/parsing/pdf_parser.py`:
```python
import pypdf
from pypdf.errors import PdfReadError

from app.core.errors import AppError
from app.models.kb import DocumentPage


async def parse_pdf(
    file_path: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    try:
        reader = pypdf.PdfReader(file_path)
    except PdfReadError:
        raise AppError("PARSE_ENCRYPTED", "PDF 加密或无法读取", http_status=400)

    pages: list[DocumentPage] = []
    all_empty = True

    for page_num, pdf_page in enumerate(reader.pages, start=1):
        text = pdf_page.extract_text() or ""
        if text.strip():
            all_empty = False

        # Extract title: first non-empty line, or first line starting with #
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        title = None
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if title is None and lines:
            title = lines[0][:256]

        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=page_num,
                title=title,
                text=text or None,
            )
        )

    if all_empty:
        raise AppError(
            "PARSE_UNSUPPORTED",
            "PDF 为扫描版或无可提取文字，请上传文字版 PDF",
            http_status=400,
        )

    return pages
```

- [x] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_parsers.py::test_parse_pdf_text_page -v
uv run pytest tests/test_parsers.py::test_parse_pdf_encrypted -v
uv run pytest tests/test_parsers.py::test_parse_pdf_zero_text_pages -v
```
Expected: all 3 PASS

---

## Task 1.3: Implement PPTX parser

**Files:**
- Create: `app/services/parsing/pptx_parser.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: Write failing test**

Add to `tests/test_parsers.py`:
```python
from app.services.parsing.pptx_parser import parse_pptx


@pytest.mark.asyncio
async def test_parse_pptx_basic(monkeypatch):
    """PPTX 应逐 slide 提取标题和正文。"""
    class FakeSlide:
        def __init__(self, has_title):
            self.shapes = []
            if has_title:
                self.shapes.append(FakeShape("title", "第一章"))

    class FakeShape:
        def __init__(self, shape_type, text):
            self.shape_type = 1 if shape_type == "title" else 2
            self.has_text_frame = True
            self.text_frame = self
            self._text = text
            self.paragraphs = [self]

        @property
        def text(self):
            return self._text

    class FakePresentation:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def slides(self):
            return [FakeSlide(True), FakeSlide(False)]

    import pptx
    monkeypatch.setattr(pptx, "Presentation", FakePresentation)

    pages = await parse_pptx("/fake/test.pptx", 1, 1)
    assert len(pages) == 2
    assert pages[0].title == "第一章"
    assert "第 2 页" in (pages[1].title or "")
```

- [x] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_parsers.py::test_parse_pptx_basic -v
```
Expected: FAILED

- [x] **Step 3: Write implementation**

`app/services/parsing/pptx_parser.py`:
```python
from pptx import Presentation

from app.models.kb import DocumentPage


async def parse_pptx(
    file_path: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    prs = Presentation(file_path)
    pages: list[DocumentPage] = []

    for slide_num, slide in enumerate(prs.slides, start=1):
        texts: list[str] = []
        title = None
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text:
                continue
            if shape.shape_type == 1:  # MSO_SHAPE_TYPE.TITLE (auto shape type ID)
                title = text[:512]
            texts.append(text)

        if title is None:
            title = f"第 {slide_num} 页"

        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=slide_num,
                title=title[:512],
                text="\n".join(texts) if texts else None,
            )
        )

    return pages
```

- [x] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_parsers.py::test_parse_pptx_basic -v
```
Expected: PASS

---

## Task 1.4: Implement DOCX parser

**Files:**
- Create: `app/services/parsing/docx_parser.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: Write failing test**

Add to `tests/test_parsers.py`:
```python
from app.services.parsing.docx_parser import parse_docx


@pytest.mark.asyncio
async def test_parse_docx_splits_on_heading1(monkeypatch):
    """DOCX 应按 Heading 1 分页，表格保留在 tables_json。"""
    class FakeParagraph:
        def __init__(self, text, style_name):
            self.text = text
            self.style = type("style", (), {"name": style_name})()

    class FakeTable:
        def __init__(self):
            self._cell_texts = [["a1", "a2"], ["b1", "b2"]]

        @property
        def _cells(self):
            return [[type("c", (), {"text": t})() for t in row] for row in self._cell_texts]

    class FakeDoc:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def paragraphs(self):
            return [FakeParagraph("第一章", "Heading 1"), FakeParagraph("正文内容", "Normal")]

        @property
        def tables(self):
            return []

    import docx
    monkeypatch.setattr(docx, "Document", FakeDoc)

    pages = await parse_docx("/fake/test.docx", 1, 1)
    assert len(pages) == 1
    assert pages[0].title == "第一章"
    assert "正文内容" in (pages[0].text or "")
    assert pages[0].tables_json == []  # Should be empty list when no tables
```

- [x] **Step 2: Run test to verify it fails → Step 3: Implement**

`app/services/parsing/docx_parser.py`:
```python
from docx import Document

from app.models.kb import DocumentPage


async def parse_docx(
    file_path: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    doc = Document(file_path)

    pages: list[DocumentPage] = []
    current_section_texts: list[str] = []
    current_title = None
    page_number = 0

    # docx.paragraphs and docx.tables are interleaved — but iterating in document order
    # requires xml.iter. For MVP, iterate paragraphs first, tables are captured by paragraph
    # index proximity.
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            if not current_section_texts:
                continue
            current_section_texts.append("")
            continue

        if para.style and para.style.name == "Heading 1":
            # Flush current section as a page
            if current_section_texts:
                page_number += 1
                pages.append(
                    DocumentPage(
                        document_id=document_id,
                        document_version_id=document_version_id,
                        page_number=page_number,
                        title=current_title,
                        text="\n".join(current_section_texts).strip() or None,
                        tables_json=[],
                    )
                )
            current_section_texts = []
            current_title = text[:512]
        else:
            current_section_texts.append(text)

    # Flush last section
    if current_section_texts:
        page_number += 1
        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=page_number,
                title=current_title,
                text="\n".join(current_section_texts).strip() or None,
                tables_json=[],
            )
        )

    # No pages at all → create one from whole doc
    if not pages:
        page_number += 1
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=page_number,
                title=None,
                text=full_text or None,
                tables_json=[],
            )
        )

    return pages
```

- [x] **Step 4: Verify passes**

```bash
uv run pytest tests/test_parsers.py::test_parse_docx_splits_on_heading1 -v
```
Expected: PASS

---

## Task 1.5: Implement XLSX parser

**Files:**
- Create: `app/services/parsing/xlsx_parser.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: Write failing test**

```python
from app.services.parsing.xlsx_parser import parse_xlsx


@pytest.mark.asyncio
async def test_parse_xlsx_multi_sheet(monkeypatch):
    """XLSX 每 sheet 转为一个 page。"""
    class FakeCell:
        def __init__(self, value):
            self.value = value

    class FakeRow:
        def __init__(self, values):
            self._cells = [FakeCell(v) for v in values]

        @property
        def cells(self):
            return self._cells

    class FakeSheet:
        def __init__(self, title):
            self.title = title
            self.max_row = 2
            self.max_column = 2

        def iter_rows(self, values_only=False):
            if values_only:
                return [["a1", "a2"], ["b1", "b2"]]
            return [FakeRow(["c1", "c2"]), FakeRow(["d1", "d2"])]

    class FakeWorkbook:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def sheetnames(self):
            return ["Sheet1"]

        def __getitem__(self, name):
            return FakeSheet(name)

        def close(self):
            pass

    import openpyxl
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **kw: FakeWorkbook())

    pages = await parse_xlsx("/fake/test.xlsx", 1, 1)
    assert len(pages) == 1
    assert pages[0].title == "Sheet1"
    assert "| a1 | a2 |" in (pages[0].text or "")
```

- [x] **Step 2: Implement**

`app/services/parsing/xlsx_parser.py`:
```python
import openpyxl

from app.models.kb import DocumentPage


async def parse_xlsx(
    file_path: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    pages: list[DocumentPage] = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows: list[str] = []

        for row in ws.iter_rows(values_only=True):
            row_vals = [str(v) if v is not None else "" for v in row]
            if any(v.strip() for v in row_vals):
                rows.append("| " + " | ".join(row_vals) + " |")

        pages.append(
            DocumentPage(
                document_id=document_id,
                document_version_id=document_version_id,
                page_number=len(pages) + 1,
                title=sheet_name[:512],
                text="\n".join(rows) if rows else None,
                tables_json=[],
            )
        )

    wb.close()
    return pages
```

- [x] **Step 3: Verify passes**

```bash
uv run pytest tests/test_parsers.py::test_parse_xlsx_multi_sheet -v
```
Expected: PASS

---

## Task 1.6: Implement file downloader (MinIO)

**Files:**
- Create: `app/services/parsing/file_downloader.py`
- Test: `tests/test_file_downloader.py`

- [x] **Step 1: Write failing test**

`tests/test_file_downloader.py`:
```python
import pytest
from app.services.parsing.file_downloader import download_from_minio
from app.core.errors import AppError


@pytest.mark.asyncio
async def test_download_success(monkeypatch):
    """正常下载应返回本地路径。"""
    async def fake_get_file(*args, **kwargs):
        # Write a small file to the temp path to simulate download
        import os
        dest = kwargs.get("local_path") or args[2]
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(b"fake content")

    monkeypatch.setattr(
        "app.services.parsing.file_downloader.MinIOClient.get_file",
        fake_get_file,
    )

    path = await download_from_minio(
        bucket="kb-docs",
        object_name="test/doc.pdf",
        expected_md5=None,
    )
    assert path.endswith(".pdf")
    with open(path, "rb") as f:
        assert f.read() == b"fake content"
    import os
    os.unlink(path)


@pytest.mark.asyncio
async def test_download_timeout(monkeypatch):
    """超时应抛 FILE_DOWNLOAD_TIMEOUT。"""
    async def fake_timeout(*args, **kwargs):
        import asyncio
        await asyncio.sleep(999)  # will be interrupted by timeout

    monkeypatch.setattr(
        "app.services.parsing.file_downloader.MinIOClient.get_file",
        fake_timeout,
    )

    with pytest.raises(AppError) as exc:
        await download_from_minio(
            bucket="kb-docs",
            object_name="test/doc.pdf",
            timeout_seconds=0.01,
        )
    assert exc.value.code == "FILE_DOWNLOAD_TIMEOUT"
```

- [x] **Step 2: Implement**

`app/services/parsing/file_downloader.py`:
```python
import asyncio
import hashlib
import os
import tempfile

from minio import Minio

from app.core.config import settings
from app.core.errors import AppError


class MinIOClient:
    """Lazy singleton for the MinIO client."""
    _client = None

    @classmethod
    def get_client(cls) -> Minio:
        if cls._client is None:
            cls._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
        return cls._client

    @staticmethod
    async def get_file(bucket: str, object_name: str, local_path: str) -> None:
        """Download object from MinIO to local path (runs in thread pool)."""
        import functools
        client = MinIOClient.get_client()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            functools.partial(client.fget_object, bucket, object_name, local_path),
        )


async def download_from_minio(
    bucket: str,
    object_name: str,
    expected_md5: str | None = None,
    timeout_seconds: int = 30,
) -> str:
    """Download file from MinIO to a temp directory. Returns local file path.

    Cleans up after caller must use try/finally to remove.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ai_parse_")
    ext = os.path.splitext(object_name)[1] or ".bin"
    local_path = os.path.join(tmp_dir, f"file{ext}")

    try:
        await asyncio.wait_for(
            MinIOClient.get_file(bucket, object_name, local_path),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        _cleanup(tmp_dir)
        raise AppError("FILE_DOWNLOAD_TIMEOUT", f"MinIO 下载超时 ({timeout_seconds}s)")

    if expected_md5:
        actual_md5 = hashlib.md5()
        with open(local_path, "rb") as f:
            while chunk := f.read(8192):
                actual_md5.update(chunk)
        if actual_md5.hexdigest() != expected_md5:
            _cleanup(tmp_dir)
            raise AppError("FILE_CHECKSUM_MISMATCH", "文件 MD5 校验不匹配")

    return local_path


def _cleanup(tmp_dir: str) -> None:
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
```

- [x] **Step 3: Verify passes**

```bash
uv run pytest tests/test_file_downloader.py -v
```
Expected: PASS

---

## Task 1.7: Implement format detection and dispatcher

**Files:**
- Create: `app/services/parsing/dispatcher.py`
- Modify: `app/services/parsing/__init__.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: Write failing test**

Add to `tests/test_parsers.py`:
```python
from app.services.parsing.dispatcher import parse_file


@pytest.mark.asyncio
async def test_dispatcher_routes_by_extension(monkeypatch):
    """分发器应正确路由各格式。"""
    async def fake_pdf(*a, **kw):
        return [{"parser": "pdf"}]

    async def fake_md(*a, **kw):
        return [{"parser": "md"}]

    monkeypatch.setattr("app.services.parsing.dispatcher.parse_pdf", fake_pdf)
    monkeypatch.setattr("app.services.parsing.dispatcher.parse_markdown", fake_md)

    # Calling with .pdf should route to parse_pdf
    from app.core.errors import AppError

    with pytest.raises(AppError) as exc:
        await parse_file("/f.txt", ".txt", 1, 1)
    assert exc.value.code == "PARSE_UNSUPPORTED_FORMAT"
```

- [x] **Step 2: Implement dispatcher**

`app/services/parsing/dispatcher.py`:
```python
from app.core.errors import AppError
from app.models.kb import DocumentPage
from app.services.parsing.docx_parser import parse_docx
from app.services.parsing.pdf_parser import parse_pdf
from app.services.parsing.pptx_parser import parse_pptx
from app.services.parsing.xlsx_parser import parse_xlsx
from app.services.parsing import parse_markdown


_PARSERS = {
    ".pdf": parse_pdf,
    ".pptx": parse_pptx,
    ".ppt": parse_pptx,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".md": parse_markdown,
}


async def parse_file(
    file_path: str, ext: str, document_id: int, document_version_id: int
) -> list[DocumentPage]:
    parser = _PARSERS.get(ext.lower())
    if parser is None:
        raise AppError(
            "PARSE_UNSUPPORTED_FORMAT",
            f"不支持的文件格式: {ext}（支持: {', '.join(_PARSERS)}）",
            http_status=400,
        )
    return await parser(file_path, document_id, document_version_id)
```

Update `app/services/parsing/__init__.py` to replace the file-level functions with dispatcher imports:
```python
"""文档解析：格式分发入口。支持 PDF / PPTX / DOCX / XLSX / Markdown。"""

from app.services.parsing.dispatcher import parse_file

# Keep parse_markdown available for direct import (used in tests & handlers)
from app.services.parsing.markdown_parser import parse_markdown

__all__ = ["parse_file", "parse_markdown"]
```

Then move the existing `parse_markdown` function from `__init__.py` into a new file `app/services/parsing/markdown_parser.py`:

- [x] **Step 3: Verify**

```bash
uv run pytest tests/test_parsers.py::test_dispatcher_routes_by_extension -v
```
Expected: PASS

---

## Task 1.8: Implement retry/timeout decorator

**Files:**
- Create: `app/services/parsing/retry.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: Write failing test**

```python
import asyncio
from app.services.parsing.retry import parse_retry
from app.core.errors import AppError


class _TestRetryCounts:
    def __init__(self):
        self.attempts = 0

    async def flaky_method(self):
        self.attempts += 1
        if self.attempts < 3:
            raise ConnectionError("network blip")
        return "ok"


@pytest.mark.asyncio
async def test_parse_retry_success_after_retries():
    """网络抖动应自动重试后成功。"""
    counter = _TestRetryCounts()
    decorated = parse_retry(retries=3, base_delay=0.01)(
        counter.flaky_method
    )
    result = await decorated()
    assert result == "ok"
    assert counter.attempts == 3


@pytest.mark.asyncio
async def test_parse_retry_gives_up():
    """3 次重试全部失败应抛出原始异常。"""
    async def always_fails():
        raise ConnectionError("persistent failure")

    decorated = parse_retry(retries=3, base_delay=0.01)(always_fails)
    with pytest.raises(ConnectionError):
        await decorated()


@pytest.mark.asyncio
async def test_parse_retry_does_not_retry_app_error():
    """AppError 不应重试。"""
    async def app_error():
        raise AppError("PARSE_CORRUPTED", "bad file")

    decorated = parse_retry(retries=3, base_delay=0.01)(app_error)
    with pytest.raises(AppError):
        await decorated()
```

- [x] **Step 2: Implement decorator**

`app/services/parsing/retry.py`:
```python
import asyncio
import functools
from collections.abc import Callable, Coroutine

from app.core.errors import AppError


def parse_retry(
    retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 120.0,
) -> Callable[..., Callable[..., Coroutine]]:
    """Decorator: retry on network errors with exponential backoff.

    Usage:
        @parse_retry(retries=3, base_delay=1.0, timeout=120.0)
        async def my_func(...): ...
    """
    def decorator(
        func: Callable[..., Coroutine],
    ) -> Callable[..., Coroutine]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(retries + 1):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except AppError:
                    raise  # Don't retry domain errors
                except (ConnectionError, TimeoutError, OSError) as exc:
                    last_exc = exc
                    if attempt < retries:
                        delay = base_delay * (4 ** attempt)
                        await asyncio.sleep(delay)
                except asyncio.TimeoutError:
                    raise AppError(
                        "PARSE_TIMEOUT",
                        f"解析超时 ({timeout}s)",
                        http_status=504,
                    )
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
```

- [x] **Step 3: Verify**

```bash
uv run pytest tests/test_parsers.py::test_parse_retry_success_after_retries -v
uv run pytest tests/test_parsers.py::test_parse_retry_gives_up -v
uv run pytest tests/test_parsers.py::test_parse_retry_does_not_retry_app_error -v
```
Expected: all PASS

---

## Task 1.9: Update Worker handler for download→parse flow

**Files:**
- Modify: `app/workers/handlers.py`
- Depends on: `Task 1.0`, `Task 1.6`, `Task 1.7`

- [x] **Step 1: Update parse_document_task**

Add module-level imports so tests can monkeypatch dependencies cleanly:

```python
from app.services.parsing.dispatcher import parse_file
from app.services.parsing.file_downloader import download_from_minio
```

Then replace the current `parse_document_task` in `app/workers/handlers.py`:

```python
async def parse_document_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Parse payload content or download file from MinIO, then save DocumentPages."""
    document_id = _require_int(payload, "document_id")
    document_version_id = _require_int(payload, "document_version_id")
    object_name = payload.get("object_name")
    markdown_content = payload.get("markdown_content")

    if not isinstance(object_name, str) and not isinstance(markdown_content, str):
        raise ValueError("payload.object_name or payload.markdown_content is required")

    local_path = None
    try:
        if isinstance(object_name, str) and object_name.strip():
            await _update_progress(session, task_id, "downloading", 5)
            file_ext = payload.get("file_ext") or os.path.splitext(object_name)[1] or ".bin"
            local_path = await download_from_minio(
                bucket=settings.minio_bucket,
                object_name=object_name,
                expected_md5=payload.get("checksum_md5"),
            )
            await _update_progress(session, task_id, "parsing", 30)
            pages = await parse_file(local_path, file_ext, document_id, document_version_id)
        else:
            if not isinstance(markdown_content, str) or not markdown_content.strip():
                raise ValueError("payload.markdown_content is empty")
            await _update_progress(session, task_id, "parsing", 30)
            pages = await parse_markdown(markdown_content, document_id, document_version_id)

        if not pages:
            raise ValueError("解析结果为空")

        await _update_progress(session, task_id, "saving", 80)
        page_repo = DocumentPageRepo(session)
        await page_repo.delete_by_version(document_version_id)
        await page_repo.add_all(pages)

        await _update_progress(session, task_id, "parsed", 100)
    finally:
        if local_path:
            import shutil
            tmp_dir = os.path.dirname(local_path)
            if tmp_dir:  # Guard against empty dirname when path has no directory component
                shutil.rmtree(tmp_dir, ignore_errors=True)
```

Add import at top:
```python
import os
```

- [x] **Step 2: Run existing handler tests to confirm regression-free**

```bash
uv run pytest tests/test_worker_handlers.py -v
```
Expected: existing handler tests remain PASS after updating the old Markdown test to send `markdown_content` through the fallback path.

- [x] **Step 3: Update worker handler tests for new flow**

Add test to `tests/test_worker_handlers.py`:
```python
@pytest.mark.asyncio
async def test_parse_document_task_with_minio(monkeypatch):
    """parse_document_task 应下载→解析→入库。"""
    from app.workers import handlers
    import os

    saved_pages = []
    progress_steps = []

    async def fake_download(*a, **kw):
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "test.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# Test\n\ncontent")
        return p

    async def fake_parse(*a, **kw):
        from app.models.kb import DocumentPage
        return [DocumentPage(document_id=1, document_version_id=1, page_number=1, title="Test", text="content")]

    monkeypatch.setattr(handlers, "download_from_minio", fake_download)
    monkeypatch.setattr(handlers, "parse_file", fake_parse)

    # Set up fake repos
    # ... (mock pattern follows existing test patterns in test_worker_handlers.py)
```

- [x] **Step 4: Keep Markdown fallback regression test**

Update the existing `test_parse_document_task_writes_markdown_pages` so it still passes with:

```python
payload={
    "document_id": 11,
    "document_version_id": 22,
    "markdown_content": "# 第一章\n\n内容",
}
```

Expected: this test proves local/test parsing still works without MinIO.

---

## Task 1.10: Run Phase 1 test suite

- [x] **Step 1: Run all Phase 1 tests**

```bash
uv run pytest tests/test_parsers.py tests/test_file_downloader.py tests/test_worker_handlers.py -v --tb=short
```
Expected: all PASS

- [ ] **Step 2: Generate coverage report**

Status: pending. `uv run pytest tests/test_parsers.py tests/test_file_downloader.py --cov=app.services.parsing --cov-report=term` currently fails because `pytest-cov` is not installed.

```bash
uv run pytest tests/test_parsers.py tests/test_file_downloader.py --cov=app.services.parsing --cov-report=term
```
Expected: coverage ≥ 80%

---

# Phase 2: Pipeline Hardening

## Task 2.1: Chunk strategy configuration

**Files:**
- Modify: `app/services/chunking/__init__.py`

- [ ] **Step 1: Write test**

Add to new test file `tests/test_chunking.py`:
```python
import pytest
from unittest.mock import AsyncMock
from app.models.config_tables import ChunkStrategy


@pytest.mark.asyncio
async def test_get_chunk_strategy_from_repo(mock_session):
    """应从 ChunkStrategy 表读取策略配置。"""
    from app.repositories.config_repo import ChunkStrategyRepo

    expected = ChunkStrategy(
        strategy_code="title",
        strategy_version="title@1",
        chunk_method="title",
        chunk_size=512,
        chunk_overlap=64,
        enabled=True,
    )
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = [expected]
    mock_session.execute.return_value = mock_result

    repo = ChunkStrategyRepo(mock_session)
    strategies = await repo.get_enabled()
    assert len(strategies) == 1
    assert strategies[0].chunk_method == "title"
```

- [ ] **Step 2: Modify chunking entry point**

Update `app/services/chunking/__init__.py` to add a strategy-aware dispatch function:

```python
async def process_chunks(
    session: AsyncSession,
    knowledge_base_version_id: int,
    course_id: int,
    document_id: int,
    document_version_id: int,
    pages: list[DocumentPage],
    strategy_code: str | None = None,
) -> list[KnowledgeChunk]:
    """Strategy-aware chunk dispatch.

    Reads the active strategy from ai.chunk_strategy table.
    Falls back to title@1 when no strategy is configured.
    """
    from app.repositories.config_repo import ChunkStrategyRepo

    repo = ChunkStrategyRepo(session)
    strategies = await repo.get_enabled()

    # Filter by code, or take first enabled
    chosen = None
    if strategy_code:
        chosen = next((s for s in strategies if s.strategy_code == strategy_code), None)
    else:
        chosen = strategies[0] if strategies else None

    if chosen is None:
        # Default fallback
        return await process_title_chunk(
            session, knowledge_base_version_id, course_id,
            document_id, document_version_id, pages,
            strategy_version="title@1",
        )

    if chosen.chunk_method == "title":
        from app.services.chunking import process_title_chunk as impl
    elif chosen.chunk_method == "fixed_size":
        from app.services.chunking import process_fixed_size_chunk as impl
    elif chosen.chunk_method == "semantic":
        from app.services.chunking.semantic import process_semantic_chunk as impl
    else:
        raise ValueError(f"未知 chunk_method: {chosen.chunk_method}")

    return await impl(
        session, knowledge_base_version_id, course_id,
        document_id, document_version_id, pages,
        chunk_size=chosen.chunk_size or 512,
        chunk_overlap=chosen.chunk_overlap or 64,
        strategy_version=chosen.strategy_version,
    )
```

- [ ] **Step 3: Update build_chunk_task to use process_chunks**

In `app/workers/handlers.py`, replace the line calling `process_title_chunk`:

```python
from app.services.chunking import process_chunks

# Inside build_chunk_task, replace:
#   chunks = await process_title_chunk(...)
# with:
    chunks = await process_chunks(
        session,
        knowledge_base_version_id=kb_version_id,
        course_id=course_id,
        document_id=document_id,
        document_version_id=document_version_id,
        pages=pages,
    )
```

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/test_chunking.py -v
```
Expected: PASS

---

## Task 2.2: Implement semantic chunk strategy

**Files:**
- Create: `app/services/chunking/semantic.py`
- Test: `tests/test_chunking.py`

- [ ] **Step 1: Write failing test**

```python
from app.services.chunking.semantic import process_semantic_chunk


@pytest.mark.asyncio
async def test_semantic_chunk_splits_at_paragraphs(mock_session):
    """Semantic 策略应在段落边界切分。"""
    from app.models.kb import DocumentPage

    pages = [
        DocumentPage(
            document_id=1, document_version_id=1, page_number=1,
            text="第一段内容。\n\n第二段内容。\n\n第三段内容。",
        ),
    ]

    chunks = await process_semantic_chunk(
        mock_session,
        knowledge_base_version_id=1, course_id=1,
        document_id=1, document_version_id=1,
        pages=pages,
        chunk_size=500, chunk_overlap=0,
    )
    assert len(chunks) >= 3  # At least 3 paragraph-based chunks
    assert "第一段" in chunks[0].chunk_text
    assert "第二段" in chunks[1].chunk_text
```

- [ ] **Step 2: Implement semantic chunking**

`app/services/chunking/semantic.py`:
```python
import hashlib
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb import DocumentPage, KnowledgeChunk


def _chunk_hash(text: str, strategy_version: str) -> str:
    return hashlib.sha256((text + strategy_version).encode("utf-8")).hexdigest()[:16]

_SECTION_BOUNDARY = re.compile(r"^(#{1,6}\s|```|```\w*$|---|___|\*\*\*)", re.MULTILINE)


async def process_semantic_chunk(
    session: AsyncSession,
    knowledge_base_version_id: int,
    course_id: int,
    document_id: int,
    document_version_id: int,
    pages: list[DocumentPage],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    strategy_version: str = "semantic@1",
) -> list[KnowledgeChunk]:
    """Semantic boundary chunking: split on markdown section/paragraph boundaries."""
    chunks: list[KnowledgeChunk] = []

    # Collect all text from pages
    full_text = "\n".join(page.text or "" for page in pages if page.text)
    if not full_text.strip():
        return chunks

    # Split on blank-line paragraphs first
    paragraphs = re.split(r"\n\n+", full_text)

    current_chunk_lines: list[str] = []
    current_page_start = pages[0].page_number if pages else 1
    current_page_end = current_page_start

    def _flush() -> None:
        nonlocal current_chunk_lines
        text = "\n\n".join(current_chunk_lines).strip()
        if text:
            chunks.append(
                KnowledgeChunk(
                    knowledge_base_version_id=knowledge_base_version_id,
                    course_id=course_id,
                    document_id=document_id,
                    document_version_id=document_version_id,
                    chunk_text=text,
                    page_start=current_page_start,
                    page_end=current_page_end,
                    chunk_hash=_chunk_hash(text, strategy_version),
                    chunk_strategy_version=strategy_version,
                    metadata_json={"strategy": "semantic"},
                )
            )
        current_chunk_lines = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Section boundary → always flush
        if _SECTION_BOUNDARY.match(para):
            if current_chunk_lines:
                _flush()

        current_chunk_lines.append(para)
        current_text = "\n\n".join(current_chunk_lines)

        # If accumulated text exceeds chunk_size, flush
        if len(current_text) > chunk_size:
            # Remove last paragraph and flush the rest
            current_chunk_lines.pop()
            if current_chunk_lines:
                _flush()
            # Start new chunk with the overflow paragraph
            current_chunk_lines.append(para)

    if current_chunk_lines:
        _flush()

    # Fallback: if no chunks were created (no paragraphs?), use fixed_size
    if not chunks:
        from app.services.chunking import process_fixed_size_chunk
        return await process_fixed_size_chunk(
            session, knowledge_base_version_id, course_id,
            document_id, document_version_id, pages,
            chunk_size=chunk_size, chunk_overlap=chunk_overlap,
            strategy_version="fixed_size@1",
        )

    return chunks
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_chunking.py::test_semantic_chunk_splits_at_paragraphs -v
```
Expected: PASS

---

## Task 2.3: Worker concurrency control

**Files:**
- Modify: `app/workers/worker.py`
- Add: Redis-based lock helper in `app/core/redis.py`
- Test: `tests/test_worker_concurrency.py`

- [ ] **Step 1: Write failing test**

`tests/test_worker_concurrency.py`:
```python
import pytest
from unittest.mock import AsyncMock
from app.workers.worker import acquire_task_lock


@pytest.mark.asyncio
async def test_acquire_lock_success():
    """获取锁成功应返回 True。"""
    mock_redis = AsyncMock()
    mock_redis.setnx.return_value = True
    result = await acquire_task_lock(mock_redis, "build_chunk", 1)
    assert result is True
    mock_redis.setnx.assert_called_once()


@pytest.mark.asyncio
async def test_acquire_lock_failure():
    """锁已存在应返回 False。"""
    mock_redis = AsyncMock()
    mock_redis.setnx.return_value = False
    result = await acquire_task_lock(mock_redis, "build_chunk", 1)
    assert result is False
```

- [ ] **Step 2: Implement lock helper in `app/workers/worker.py`**

```python
from redis.asyncio import Redis as AsyncRedis

_LOCK_TTL = 300  # 5 minutes

async def acquire_task_lock(redis: AsyncRedis, task_type: str, kb_version_id: int) -> bool:
    """Try to acquire a distributed lock for a task type on a KB version."""
    lock_key = f"lock:{task_type}:{kb_version_id}"
    return await redis.setnx(lock_key, "1") and await redis.expire(lock_key, _LOCK_TTL)


async def release_task_lock(redis: AsyncRedis, task_type: str, kb_version_id: int) -> None:
    """Release the distributed lock."""
    lock_key = f"lock:{task_type}:{kb_version_id}"
    await redis.delete(lock_key)
```

- [ ] **Step 3: Integrate lock into worker loop**

Modify `_claim_and_run_once` in `app/workers/worker.py`:

```python
async def _claim_and_run_once() -> bool:
    async with SessionLocal() as session:
        repo = KbBuildTaskRepo(session)
        task = await repo.claim_pending()
        if task is None:
            return False

        # Try to acquire task-level lock (Redis required; skip lock if Redis unavailable)
        lock_acquired = True
        try:
            lock_acquired = await acquire_task_lock(
                redis_client, task.task_type, task.knowledge_base_version_id
            )
        except Exception:  # noqa: BLE001
            lock_acquired = True  # Degrade to no-lock mode

        if not lock_acquired:
            # Another worker holds this lock; release claim
            task.status = "pending"  # Return to pending
            await session.commit()
            return True  # We did something (found task, couldn't lock)

        try:
            await dispatch(task.id, task.task_type, task.payload_json or {}, session)
            await repo.mark_success(task)
            log.info("worker.task_success", task_id=task.id)
        except NotImplementedError:
            await repo.mark_failed(task, "NOT_IMPLEMENTED", "handler not implemented")
            log.warning("worker.task_not_implemented", task_id=task.id, task_type=task.task_type)
        except Exception as exc:  # noqa: BLE001
            await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
            log.exception("worker.task_failed", task_id=task.id, task_type=task.task_type)
        finally:
            try:
                await release_task_lock(
                    redis_client, task.task_type, task.knowledge_base_version_id
                )
            except Exception:  # noqa: BLE001
                pass
            await session.commit()
    return True
```

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/test_worker_concurrency.py -v
```
Expected: PASS

---

## Task 2.4: Task failure retry with Redis ZSET

**Files:**
- Modify: `app/workers/worker.py`, `app/repositories/task_repo.py`

- [ ] **Step 1: Implement retry queue helpers**

In `app/workers/worker.py`:
```python
_RETRY_KEY = "retry:tasks"

async def schedule_retry(redis: AsyncRedis, task_id: int, delay_seconds: int) -> None:
    """Schedule a task for retry after delay_seconds."""
    import time
    score = time.time() + delay_seconds
    await redis.zadd(_RETRY_KEY, {str(task_id): score})


async def pop_due_retries(redis: AsyncRedis) -> list[int]:
    """Return task_ids whose retry time has passed."""
    import time
    now = time.time()
    ids = await redis.zrangebyscore(_RETRY_KEY, 0, now)
    if ids:
        await redis.zremrangebyscore(_RETRY_KEY, 0, now)
    return [int(i) for i in ids]
```

- [ ] **Step 2: Update claim logic in repo**

In `app/repositories/task_repo.py`, modify `claim_pending` to also accept a list of retryable task IDs:

```python
async def claim_pending(self, retryable_ids: list[int] | None = None) -> KbBuildTask | None:
    """Claim a pending task (or a retryable one)."""
    stmt = select(KbBuildTask).where(KbBuildTask.status == "pending").order_by(KbBuildTask.created_at).limit(1)

    # If specific retry IDs are given, prefer those
    if retryable_ids:
        stmt = select(KbBuildTask).where(
            KbBuildTask.id.in_(retryable_ids), KbBuildTask.status == "failed"
        ).order_by(KbBuildTask.created_at).limit(1)

    stmt = stmt.with_for_update(skip_locked=True)
    result = await self.session.execute(stmt)
    task = result.scalar_one_or_none()
    if task is not None:
        task.status = "running"
        task.started_at = datetime.now(UTC)
        await self.session.flush()
    return task
```

- [ ] **Step 3: Update worker error handling**

In `app/workers/worker.py`, update the exception handler in `_claim_and_run_once`:

```python
except Exception as exc:  # noqa: BLE001
    task.retry_count = (task.retry_count or 0) + 1
    if task.retry_count < 3 and not isinstance(exc, NotImplementedError):
        from app.core.errors import AppError
        if not isinstance(exc, AppError) or exc.code not in ("PARSE_UNSUPPORTED", "PARSE_ENCRYPTED", "PARSE_CORRUPTED"):
            await schedule_retry(redis_client, task.id, 5 * (4 ** (task.retry_count - 1)))
            task.status = "failed"  # Mark failed but will be picked up by retry queue
            task.error_code = "HANDLER_ERROR"
            task.error_message = str(exc)[:500]
            log.warning("worker.scheduled_retry", task_id=task.id, attempt=task.retry_count)
        else:
            await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
    else:
        await repo.mark_failed(task, "HANDLER_ERROR", str(exc))
    log.exception("worker.task_failed", task_id=task.id, task_type=task.task_type)
```

- [ ] **Step 4: Verify with tests**

```bash
uv run pytest tests/test_worker_concurrency.py -v
```
Expected: PASS

---

## Task 2.5: Transactional pipeline rollback

**Files:**
- Modify: `app/workers/handlers.py`

- [ ] **Step 1: Implement cleanup in build_knowledge_base_version_task**

```python
async def build_knowledge_base_version_task(
    task_id: int, task_type: str, payload: dict, session: AsyncSession
) -> None:
    """Run the MVP build chain with transactional rollback on failure."""
    from app.repositories.embedding_repo import EmbeddingIndexVersionRepo, KeywordIndexVersionRepo

    created_embedding_idx_id = None
    created_keyword_idx_id = None
    try:
        await build_chunk_task(task_id, "build_chunk", payload, session)

        await build_keyword_index_task(task_id, "build_keyword_index", payload, session)
        # Capture the keyword index version ID that was just created
        task_repo = KbBuildTaskRepo(session)
        task = await task_repo.get(task_id)
        if task:
            kw_repo = KeywordIndexVersionRepo(session)
            kw_idx = await kw_repo.get_latest_by_version(task.knowledge_base_version_id)
            if kw_idx:
                created_keyword_idx_id = kw_idx.id

        await build_embedding_index_task(task_id, "build_embedding_index", payload, session)
        task = await task_repo.get(task_id)
        if task:
            emb_repo = EmbeddingIndexVersionRepo(session)
            emb_idx = await emb_repo.get_latest_by_version(task.knowledge_base_version_id)
            if emb_idx:
                created_embedding_idx_id = emb_idx.id

    except Exception:
        # Cleanup: remove partial artifacts
        if created_embedding_idx_id:
            emb_repo = EmbeddingIndexVersionRepo(session)
            emb = await emb_repo.get(created_embedding_idx_id)
            if emb:
                await session.delete(emb)
        if created_keyword_idx_id:
            kw_repo = KeywordIndexVersionRepo(session)
            kw = await kw_repo.get(created_keyword_idx_id)
            if kw:
                await session.delete(kw)
        raise  # Re-raise for worker to handle
```

- [ ] **Step 2: Verify**

```bash
uv run pytest tests/test_worker_handlers.py -v
```
Expected: PASS

---

## Task 2.6: Snapshot-based document update

**Files:**
- Modify: `app/api/internal/v1/documents.py`
- Modify: `app/workers/handlers.py`
- Test: `tests/test_worker_handlers.py`

This task replaces the old "expire chunks in-place" plan. Do not mutate chunks in the currently published `knowledge_base_version`. The safe boundary is a new version snapshot.

- [ ] **Step 1: Preserve version boundary**

When Java updates one document, Java creates or chooses a new `knowledge_base_version_id` and calls the Phase 1 parse endpoint with that version ID. AI service writes parsed pages and later chunks/indexes against the new version only.

Rules:
- No `knowledge_base_version_id=0`.
- No `incremental` flag on `/documents/{document_version_id}/parse`.
- No `UPDATE ai.knowledge_chunk SET status='expired'` against an existing published version.
- Current published version continues serving until Java switches the active version after validation.

- [ ] **Step 2: Add snapshot build test**

Create or update a test proving that building with a new version ID writes chunks to the new version and leaves old-version chunks untouched.

```python
async def test_snapshot_build_does_not_expire_old_version_chunks(...):
    # Given old version 1 has active chunks
    # When version 2 is built for an updated document
    # Then old version 1 chunks remain active
    # And new version 2 chunks are active under knowledge_base_version_id=2
```

- [ ] **Step 3: Optional copy optimization**

If copying unchanged chunks from an old version is needed for speed, implement it as a separate helper that creates new `knowledge_chunk` rows under the new `knowledge_base_version_id`. Do not reuse IDs or mutate old rows.

```python
async def copy_unchanged_chunks_to_new_version(
    session: AsyncSession,
    *,
    from_kb_version_id: int,
    to_kb_version_id: int,
    exclude_document_ids: set[int],
) -> int:
    ...
```

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/test_worker_handlers.py -v
```

Expected: snapshot boundary tests PASS.

---

## Task 2.7: Pipeline observability / Prometheus metrics

**Files:**
- Create: `app/core/metrics.py`
- Modify: `app/main.py`, `pyproject.toml`

- [ ] **Step 1: Add prometheus-client dependency**

In `pyproject.toml`, add `"prometheus-client>=0.21"` to dependencies.

- [ ] **Step 2: Define metrics**

`app/core/metrics.py`:
```python
from prometheus_client import Counter, Gauge, Histogram

kb_build_tasks_total = Counter(
    "kb_build_tasks_total", "Total KB build tasks by status",
    ["status"],
)

kb_build_tasks_running = Gauge(
    "kb_build_tasks_running", "Currently running KB build tasks",
)

kb_build_task_duration_seconds = Histogram(
    "kb_build_task_duration_seconds", "KB build task duration in seconds",
    ["task_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

kb_build_tasks_failed_total = Counter(
    "kb_build_tasks_failed_total", "Failed KB build tasks by error code",
    ["error_code"],
)
```

- [ ] **Step 3: Mount /metrics endpoint**

In `app/main.py`, add:
```python
from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

metrics_router = APIRouter()

@metrics_router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(metrics_router)
```

- [ ] **Step 4: Instrument worker**

In `app/workers/worker.py`, add instrumentation calls:
```python
from app.core.metrics import kb_build_tasks_total, kb_build_tasks_running, kb_build_task_duration_seconds, kb_build_tasks_failed_total
import time

# In _claim_and_run_once, at start:
start_time = time.monotonic()
kb_build_tasks_running.inc()
kb_build_tasks_total.labels(status=task.status).inc()

# In finally block:
kb_build_tasks_running.dec()
duration = time.monotonic() - start_time
kb_build_task_duration_seconds.labels(task_type=task.task_type).observe(duration)
if task.status == "failed":
    kb_build_tasks_failed_total.labels(error_code=task.error_code or "UNKNOWN").inc()
```

- [ ] **Step 5: Verify**

```bash
uv run pytest -v
```
Expected: no regressions

---

## Task 2.8: Batch task query API

**Files:**
- Modify: `app/api/internal/v1/kb_tasks.py`

- [ ] **Step 1: Add batch query endpoint**

In `app/api/internal/v1/kb_tasks.py`:
```python
from app.schemas.common import Page


@router.get("")
async def list_tasks(
    kb_version_id: int | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> Page[dict]:
    """List KB build tasks with optional kb_version_id filter."""
    from sqlalchemy import func, select as sa_select

    filters = []
    if kb_version_id is not None:
        filters.append(KbBuildTask.knowledge_base_version_id == kb_version_id)

    repo = KbBuildTaskRepo(session)
    total = await repo.count(*filters)

    stmt = (
        sa_select(KbBuildTask)
        .where(*filters)
        .order_by(KbBuildTask.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    items = [
        {
            "task_id": t.id,
            "task_type": t.task_type,
            "status": t.status,
            "current_step": t.current_step,
            "progress": t.progress,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
        }
        for t in tasks
    ]

    return Page(items=items, total=total, page=page, page_size=size)
```

- [ ] **Step 2: Verify**

```bash
uv run pytest -v
```
Expected: no regressions

---

## Task 2.9: Run Phase 2 test suite

- [ ] **Step 1: Run all tests**

```bash
uv run pytest tests/ -v --tb=short
```
Expected: all PASS, ≥ 80% coverage

---

# Phase 3: Retrieval + RAG Enhancement

## Task 3.1: SSE streaming Q&A

**Files:**
- Modify: `app/api/internal/v1/qa.py`
- Modify: `app/services/rag/__init__.py`
- Test: `tests/test_rag_stream.py`

- [ ] **Step 1: Add stream method to LlmClient**

In `app/gateway/llm_client.py`, the `chat_stream` method already exists (verified). Confirm:

```bash
uv run python -c "from app.gateway.llm_client import LlmClient; print(dir(LlmClient))"
```
Expected: includes `chat_stream`

- [ ] **Step 2: Implement stream endpoint with real token-by-token SSE**

Replace the stub in `app/api/internal/v1/qa.py`:

```python
import json
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from app.gateway.llm_client import LlmClient
from app.services.rag import _build_rag_prompt, _MIN_SCORE_THRESHOLD


async def _stream_events(req: QaAnswerRequest, session: AsyncSession) -> AsyncIterator[str]:
    """Yield SSE events for streaming Q&A. Token by token."""
    from app.services.retrieval import hybrid_retrieve

    # Step 1: Query rewrite + retrieval (synchronous)
    try:
        _, fused, log_ref = await hybrid_retrieve(
            session,
            question=req.question,
            kb_version_id=req.kb_version_id,
            course_id=req.course_id,
        )
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Step 2: Load chunk text into fused results
    fused_with_text = []
    if fused:
        from sqlalchemy import select as sa_select
        from app.models.kb import KnowledgeChunk

        stmt = sa_select(
            KnowledgeChunk.id, KnowledgeChunk.chunk_text,
            KnowledgeChunk.source_file, KnowledgeChunk.page_start,
            KnowledgeChunk.page_end,
        ).where(KnowledgeChunk.id.in_([r["chunk_id"] for r in fused]))
        result = await session.execute(stmt)
        chunk_map = {row[0]: row for row in result.fetchall()}

        for r in fused:
            row = chunk_map.get(r["chunk_id"])
            if row:
                r["text"] = row[1]
                r["source_file"] = row[2]
                r["page_start"] = row[3]
                r["page_end"] = row[4]
            else:
                r["text"] = ""
            fused_with_text.append(r)

    # Step 3: Score threshold check (before streaming)
    scores = [c.get("final_score", 0) for c in fused_with_text]
    if max(scores) < _MIN_SCORE_THRESHOLD if fused_with_text else True:
        yield f"data: {json.dumps({'reject_reason': 'low_score'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Step 4: Build prompt and stream token by token
    messages = _build_rag_prompt(req.question, fused_with_text)
    llm = LlmClient()

    answer_chunks: list[str] = []
    try:
        async for token in llm.chat_stream(messages):
            answer_chunks.append(token)
            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Step 5: Send sources after the full answer
    full_answer = "".join(answer_chunks)
    sources = [
        {"chunk_id": c.get("chunk_id"), "score": c.get("final_score")}
        for c in fused_with_text
    ]
    yield f"data: {json.dumps({'answer': full_answer, 'sources': sources, 'retrieval_log_ref': log_ref}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/answer/stream")
async def answer_stream(
    req: QaAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """SSE streaming Q&A (query rewrite → hybrid retrieval → LLM stream token-by-token → sources)."""
    return StreamingResponse(
        _stream_events(req, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 3: Write test verifying SSE event content**

`tests/test_rag_stream.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_stream_events_yields_tokens(monkeypatch):
    """SSE 事件流应逐 token 输出，最后输出 sources 和 DONE。"""
    from app.api.internal.v1.qa import _stream_events
    from app.schemas.qa import QaAnswerRequest

    async def fake_retrieve(*a, **kw):
        return "query", [], None

    async def fake_chat_stream(*a, **kw):
        yield "你好"
        yield "世界"

    monkeypatch.setattr("app.api.internal.v1.qa.hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr("app.api.internal.v1.qa.LlmClient.chat_stream", fake_chat_stream)

    req = QaAnswerRequest(
        user_id=1, course_id=1, kb_version_id=1,
        session_id=1, message_id=1, question="test"
    )

    events = [e async for e in _stream_events(req, AsyncMock())]

    # Token events
    assert json.loads(events[0][6:]) == {"token": "你好"}
    assert json.loads(events[1][6:]) == {"token": "世界"}
    # Sources event
    assert "answer" in json.loads(events[2][6:])
    assert json.loads(events[2][6:])["answer"] == "你好世界"
    # DONE
    assert events[3] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_stream_returns_sse_content_type(monkeypatch):
    """流式端点应返回 text/event-stream。"""
    from app.api.internal.v1.qa import answer_stream
    from app.schemas.qa import QaAnswerRequest

    async def fake_retrieve(*a, **kw):
        return "query", [], None

    async def fake_chat_stream(*a, **kw):
        yield "token"

    monkeypatch.setattr("app.api.internal.v1.qa.hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr("app.api.internal.v1.qa.LlmClient.chat_stream", fake_chat_stream)

    req = QaAnswerRequest(
        user_id=1, course_id=1, kb_version_id=1,
        session_id=1, message_id=1, question="test"
    )

    resp = await answer_stream(req, AsyncMock())
    assert resp.media_type == "text/event-stream"
```

---

## Task 3.2: Query rewrite enhancement

**Files:**
- Create: `app/services/retrieval/synonyms.json`
- Modify: `app/services/retrieval/__init__.py`

- [ ] **Step 1: Create synonym dictionary**

`app/services/retrieval/synonyms.json`:
```json
{
  "ML": ["机器学习"],
  "AI": ["人工智能"],
  "NLP": ["自然语言处理"],
  "DL": ["深度学习"],
  "CNN": ["卷积神经网络"],
  "RNN": ["循环神经网络"],
  "LSTM": ["长短期记忆网络"],
  "SVM": ["支持向量机"],
  "PCA": ["主成分分析"],
  "API": ["接口"],
  "DB": ["数据库"]
}
```

- [ ] **Step 2: Enhance query_rewrite**

Modify `query_rewrite` in `app/services/retrieval/__init__.py`:

```python
import json
import os
import re

_SYNONYMS: dict[str, list[str]] | None = None

def _load_synonyms() -> dict[str, list[str]]:
    global _SYNONYMS
    if _SYNONYMS is None:
        path = os.path.join(os.path.dirname(__file__), "synonyms.json")
        try:
            with open(path, encoding="utf-8") as f:
                _SYNONYMS = json.load(f)
        except FileNotFoundError:
            _SYNONYMS = {}
    return _SYNONYMS


def _expand_synonyms(text: str) -> str:
    """Expand known acronyms/abbreviations with their full forms."""
    syns = _load_synonyms()
    words = text.split()
    expanded = []
    for w in words:
        expanded.append(w)
        if w.upper() in syns:
            expanded.extend(syns[w.upper()])
    return " ".join(expanded)


def _detect_language(text: str) -> str:
    """Detect if text is zh, en, or mixed."""
    has_zh = bool(re.search(r"[一-鿿]", text))
    has_en = bool(re.search(r"[a-zA-Z]{2,}", text))
    if has_zh and has_en:
        return "mixed"
    if has_zh:
        return "zh"
    return "en"


async def query_rewrite(raw: str) -> dict:
    """Query rewrite with synonym expansion and language-aware tokenization."""
    normalized = raw.strip().replace("\n", " ")
    lang = _detect_language(normalized)

    # Synonym expansion
    expanded = _expand_synonyms(normalized)

    if lang in ("zh", "mixed"):
        words = list(jieba.cut(expanded))
        keyword_query = " ".join(w for w in words if len(w) > 1)
    else:
        # English: lowercase space-split
        keyword_query = " ".join(
            w.lower() for w in expanded.split() if len(w) > 2
        )

    return {
        "raw_query": raw,
        "normalized_query": normalized,
        "keyword_query": keyword_query,
        "semantic_query": normalized,
        "language": lang,
    }
```

---

## Task 3.3: Multi-turn conversation context

**Files:**
- Modify: `app/services/rag/__init__.py`

- [ ] **Step 1: Add history loading to qa_answer**

In `app/services/rag/__init__.py`:
```python
from app.repositories.log_repo import QaRetrievalLogRepo


async def _load_conversation_history(
    session: AsyncSession,
    message_id: int | None,
    max_turns: int = 3,
) -> list[dict]:
    """Load recent Q&A history from qa_retrieval_log for multi-turn context."""
    if message_id is None:
        return []

    from sqlalchemy import select as sa_select
    from app.models.logs import QaRetrievalLog, ModelCallLog

    # Get current message's session_id from retrieval log
    repo = QaRetrievalLogRepo(session)
    stmt = (
        sa_select(QaRetrievalLog)
        .where(QaRetrievalLog.message_id == message_id)
        .order_by(QaRetrievalLog.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    current = result.scalar_one_or_none()
    if current is None or current.session_id is None:
        return []

    # Find recent messages in the same session (excluding current)
    stmt = (
        sa_select(QaRetrievalLog)
        .where(
            QaRetrievalLog.session_id == current.session_id,
            QaRetrievalLog.message_id < message_id,
        )
        .order_by(QaRetrievalLog.id.desc())
        .limit(max_turns)
    )
    result = await session.execute(stmt)
    logs = result.scalars().all()

    # For each retrieval log, find the corresponding model call to get the answer
    history: list[dict] = []
    for log in reversed(logs):
        m_stmt = sa_select(ModelCallLog).where(
            ModelCallLog.message_id == log.message_id,
            ModelCallLog.scenario == "qa",
            ModelCallLog.success.is_(True),
        ).order_by(ModelCallLog.id.desc()).limit(1)
        m_result = await session.execute(m_stmt)
        model_log = m_result.scalar_one_or_none()

        history.append({
            "role": "user",
            "content": log.raw_query or "",
        })
        # Note: model log doesn't store the actual answer text — the caller (Java)
        # holds the full Q&A. Here we can only reconstruct partial context.
        # The answer text is not available from our logs.

    return history
```

---

## Task 3.4: Citation validation

**Files:**
- Modify: `app/services/rag/__init__.py`

- [ ] **Step 1: Add citation validation**

Add to `app/services/rag/__init__.py`:
```python
import re

_CITATION_RE = re.compile(r"\[来源:(\d+)\]")


def validate_citations(answer: str, context_chunks: list[dict]) -> tuple[str, list[dict], list[str]]:
    """Validate [来源:N] citations in LLM answer.

    Returns:
        (cleaned_answer, validated_sources, warnings)
    """
    warnings = []
    valid_indices = set(range(1, len(context_chunks) + 1))
    seen = set()

    def _replace_citation(m: re.Match) -> str:
        idx = int(m.group(1))
        if idx in valid_indices and idx not in seen:
            seen.add(idx)
            return m.group(0)
        warnings.append(f"invalid citation [{m.group(0)}]")
        return ""

    cleaned = _CITATION_RE.sub(_replace_citation, answer)

    # Check for low-score citations
    for idx in seen:
        chunk = context_chunks[idx - 1]
        score = chunk.get("final_score", 1.0)
        if score < 0.2:
            warnings.append(f"weak citation [来源:{idx}] (score={score:.3f})")

    sources = [
        {
            "chunk_id": c.get("chunk_id"),
            "source_index": i + 1 if (i + 1) in seen else None,
            "score": c.get("final_score"),
            "invalid": (i + 1) not in seen,
        }
        for i, c in enumerate(context_chunks)
    ]

    return cleaned, sources, warnings
```

---

## Task 3.5: Retrieval degradation strategy

**Files:**
- Modify: `app/services/retrieval/__init__.py`

- [ ] **Step 1: Wrap hybrid_retrieve with degradation**

Wrap the vector search call in `hybrid_retrieve`:

```python
async def hybrid_retrieve(
    session: AsyncSession,
    question: str,
    kb_version_id: int,
    course_id: int | None = None,
    top_k: int | None = None,
) -> tuple[str, list[dict], int | None]:
    """Hybrid retrieval with degradation handling."""
    rewritten = await query_rewrite(question)
    kw_query = rewritten["keyword_query"]
    semantic_query = rewritten["semantic_query"]

    config_repo = RetrievalStrategyConfigRepo(session)
    strategy = await config_repo.get_default()
    v_top_k = top_k or (strategy.vector_top_k if strategy else 20)
    kw_top_k = top_k or (strategy.keyword_top_k if strategy else 20)
    final_top_k = top_k or (strategy.final_top_k if strategy else 5)
    v_weight = float(strategy.vector_weight) if strategy else 0.6
    kw_weight = float(strategy.keyword_weight) if strategy else 0.3

    emb_idx_repo = EmbeddingIndexVersionRepo(session)
    emb_idx = await emb_idx_repo.get_latest_by_version(kb_version_id)

    vector_hits: list[VectorHit] = []
    keyword_hits: list[tuple[int, float]] = []
    retrieval_channel = "hybrid"

    # Vector search (degradable)
    if emb_idx:
        try:
            filter_dict = {"course_id": course_id} if course_id else None
            vector_hits = await _vector_search(
                session, emb_idx.id, semantic_query, v_top_k, filter_dict
            )
        except Exception:  # noqa: BLE001
            retrieval_channel = "keyword_only"

    # Keyword search (degradable)
    try:
        keyword_hits = await _keyword_search(
            session, kw_query, kb_version_id, kw_top_k
        )
    except Exception:  # noqa: BLE001
        if retrieval_channel == "keyword_only":
            retrieval_channel = "empty"

    # Fusion
    if retrieval_channel == "empty":
        fused = []
    else:
        fused = _hybrid_fusion(
            vector_hits, keyword_hits, v_weight, kw_weight, final_top_k
        )

    # (rest of function unchanged: chunk text loading + logging)
    ...
```

---

## Task 3.6: MMR diversity

**Files:**
- Modify: `app/services/retrieval/__init__.py`

- [ ] **Step 1: Implement MMR**

```python
import math


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def mmr_diversify(
    items: list[dict],
    embeddings: list[list[float]],
    lambda_param: float = 0.5,
    top_k: int = 5,
) -> list[dict]:
    """Maximum Marginal Relevance to diversify retrieval results.

    Args:
        items: list of dicts with 'chunk_id' and 'final_score'
        embeddings: corresponding embedding vectors
        lambda_param: 1.0 = max relevance, 0.0 = max diversity
        top_k: max results to return

    Returns:
        Re-ranked items with diverse coverage.
    """
    if not items or len(items) <= 1:
        return items[:top_k]

    selected: list[int] = []
    remaining = list(range(len(items)))

    while len(selected) < min(top_k, len(items)):
        mmr_scores = {}
        for i in remaining:
            rel_score = items[i].get("final_score", 0)

            if selected:
                max_sim = max(
                    _cosine_sim(embeddings[i], embeddings[j])
                    for j in selected
                )
            else:
                max_sim = 0

            mmr = lambda_param * rel_score - (1 - lambda_param) * max_sim
            mmr_scores[i] = mmr

        best = max(mmr_scores, key=mmr_scores.get)
        selected.append(best)
        remaining.remove(best)

    return [items[i] for i in selected]
```

---

## Task 3.7: RAG prompt configuration from DB

**Files:**
- Modify: `app/services/rag/__init__.py`

- [ ] **Step 1: Load prompt from repository**

```python
from app.repositories.config_repo import PromptTemplateRepo

def _build_rag_prompt(
    question: str,
    context_chunks: list[dict],
    prompt_template: str | None = None,
    temperature: float | None = None,
) -> list[dict]:
    """Build RAG prompt, using custom template if provided."""
    if prompt_template:
        system = prompt_template
    else:
        system = (
            "你是一个专业的知识助教。请基于提供的参考资料，用中文回答用户问题。"
            "回答要求：\n"
            "1. 如果参考资料足够回答，请给出准确、完整的答案\n"
            "2. 如果参考资料不足以回答，请说明无法回答\n"
            "3. 在答案末尾注明引用的资料编号，格式为「[来源:N]」\n"
            "4. 不要编造信息\n"
        )

    context_parts = []
    for i, chunk in enumerate(context_chunks):
        ctx = f"[来源 {i + 1}]\n{chunk.get('text', '')}"
        if chunk.get("source_file"):
            ctx += f"\n(文件: {chunk['source_file']})"
        context_parts.append(ctx)

    context_block = "\n\n---\n\n".join(context_parts)
    user_prompt = f"参考资料：\n{context_block}\n\n问题：{question}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


async def qa_answer(
    session: AsyncSession,
    question: str,
    context_chunks: list[dict],
    message_id: int | None = None,
    prompt_version: str | None = None,
) -> dict:
    """RAG Q&A with configurable prompt from DB."""
    # Load prompt template from DB
    prompt_repo = PromptTemplateRepo(session)
    templates = await prompt_repo.get_by_scenario("qa")
    selected_template = None
    temperature = 0.7

    if prompt_version:
        selected_template = next(
            (t for t in templates if t.prompt_version == prompt_version),
            None
        )
    elif templates:
        selected_template = templates[0]

    if selected_template:
        temperature = 0.7  # Could be extended with a temperature column

    # Score threshold check
    scores = [c.get("final_score", 0) for c in context_chunks]
    if max(scores) < _MIN_SCORE_THRESHOLD:
        return {
            "answer": "",
            "reject_reason": "low_score",
            "model": settings.llm_model,
        }

    template_content = selected_template.prompt_content if selected_template else None
    messages = _build_rag_prompt(question, context_chunks, template_content)

    llm = LlmClient()
    log_repo = ModelCallLogRepo(session)

    try:
        answer = await llm.chat(messages, temperature=temperature)
        # ... citation validation ...
        await log_repo.log_call(scenario="qa", ...)
        ...
```

---

## Task 3.8: Phase 3 tests

- [ ] **Step 1: Run test suite**

```bash
uv run pytest tests/test_rag_stream.py tests/test_retrieval.py tests/test_mmr.py -v
```

Expected: all PASS

---

# Phase 4: Question Generation / Diagnosis / Grading

## Task 4.1: Prompt template integration for generation

**Files:**
- Modify: `app/services/generation/__init__.py`

Already covered in Task 3.7 pattern. The `generate_questions`, `diagnose`, and `grade_short_answer` functions will use `PromptTemplateRepo.get_by_scenario("generate_questions")`.

---

## Task 4.2: AI question generation

**Files:**
- Modify: `app/services/generation/__init__.py`
- Modify: `app/schemas/qa.py`

- [ ] **Step 1: Define schemas**

In `app/schemas/qa.py`:
```python
from typing import Literal
from pydantic import BaseModel


class QuestionDraft(BaseModel):
    type: Literal["choice", "fill", "true_false", "short_answer"]
    question: str
    options: list[str] | None = None
    answer: str
    explanation: str
    difficulty: Literal["easy", "medium", "hard"]
    knowledge_point_id: int | None = None


class GenerateQuestionsRequest(BaseModel):
    course_id: int
    knowledge_point_id: int | None = None
    count: int = 5
    difficulty: Literal["easy", "medium", "hard"] | None = None
    question_types: list[Literal["choice", "fill", "true_false", "short_answer"]] | None = None
```

- [ ] **Step 2: Implement generate_questions**

```python
async def generate_questions(
    session: AsyncSession,
    course_id: int,
    kb_version_id: int,
    knowledge_point_id: int | None = None,
    count: int = 5,
    question_types: list[str] | None = None,
) -> list[dict]:
    """Generate question drafts from knowledge base chunks."""
    # 1. Retrieve relevant chunks from the correct KB version
    from app.services.retrieval import hybrid_retrieve

    query = f"知识点 {knowledge_point_id}" if knowledge_point_id else f"课程 {course_id}"
    _, fused, _ = await hybrid_retrieve(
        session, question=query, kb_version_id=kb_version_id,
        course_id=course_id, top_k=10,
    )

    if not fused:
        from app.core.errors import AppError
        raise AppError("KNOWLEDGE_POINT_EMPTY", "该知识点暂无内容，无法出题", http_status=404)

    # 2. Build prompt
    context = "\n\n".join(c.get("text", "") for c in fused)
    q_types = question_types or ["choice", "fill", "true_false", "short_answer"]

    system = (
        "你是一个出题助手。请根据提供的教材内容，生成符合要求的题目。\n"
        f"题目类型：{', '.join(q_types)}\n"
        f"数量：{count}\n"
        "请以 JSON 数组格式返回，每道题包含：type, question, options(选择题才有), answer, explanation, difficulty。"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"教材内容：\n{context}\n\n请出 {count} 道题。"},
    ]

    # 3. Call LLM
    from app.gateway.llm_client import LlmClient
    llm = LlmClient()
    result = await llm.chat(messages, temperature=0.7)

    # 4. Parse and validate
    import json
    try:
        questions = json.loads(result)
        if not isinstance(questions, list):
            raise ValueError("not a list")
    except (json.JSONDecodeError, ValueError):
        raise AppError("SCHEMA_INVALID", "LLM 返回格式不合法", http_status=422)

    # Validate each question
    validated = []
    for q in questions:
        if not all(k in q for k in ("type", "question", "answer", "explanation", "difficulty")):
            continue  # Skip malformed items
        q["knowledge_point_id"] = knowledge_point_id
        validated.append(q)

    return validated
```

> **Note for API handler:** The updated `generate_questions` signature is `(session, course_id, kb_version_id, ...)`. The handler in `app/api/internal/v1/questions.py` must inject `Depends(get_session)` and pass `kb_version_id` from the request. The handler also needs a new request body field `kb_version_id`. See Task 4.6 for API parameter changes.

---

## Task 4.3: Schema design (DiagnoseRequest + GradeResult)

**Files:**
- Modify: `app/schemas/qa.py`

- [ ] **Step 1: Add DiagnoseRequest and GradeResult schemas**

In `app/schemas/qa.py`, add after `QuestionDraft`:

```python
class DiagnoseRequest(BaseModel):
    question: str
    student_answer: str
    correct_answer: str
    knowledge_point_id: int | None = None
    course_id: int
    kb_version_id: int


class DiagnoseResult(BaseModel):
    error_type: Literal["knowledge_gap", "concept_confusion", "misunderstanding", "careless"]
    error_type_label: str
    analysis: str
    suggestion: str
    related_chunks: list[dict] = []


class GradeResult(BaseModel):
    score: int  # 0-100
    dimensions: dict[str, int]  # {完整性, 准确性, 逻辑性}
    reason: str
    highlight: str | None = None
    model: str | None = None
```

- [ ] **Step 2: Update `app/schemas/qa.py` imports**

Ensure the file has:
```python
from typing import Literal
from pydantic import BaseModel
```

---

## Task 4.4: Diagnose implementation

**Files:**
- Modify: `app/services/generation/__init__.py`
- Test: `tests/test_generation.py`

- [ ] **Step 1: Write failing test**

```python
from app.services.generation import diagnose
from app.core.errors import AppError


@pytest.mark.asyncio
async def test_diagnose_identifies_confusion(mock_session, monkeypatch):
    """输入混淆概念的问题应返回 concept_confusion。"""
    async def fake_retrieve(*a, **kw):
        return "query", [{"chunk_id": 1, "text": "MSE 和 MAE 都是回归损失函数", "final_score": 0.9}], None

    monkeypatch.setattr("app.services.generation.hybrid_retrieve", fake_retrieve)

    async def fake_chat(*a, **kw):
        return '{"error_type": "concept_confusion", "analysis": "混淆了 MSE 和 MAE 的定义"}'

    monkeypatch.setattr("app.gateway.llm_client.LlmClient.chat", fake_chat)

    result = await diagnose(
        session=mock_session,
        question="MSE 和 MAE 有什么区别？",
        student_answer="它们是同一种损失函数",
        correct_answer="MSE 是均方误差，MAE 是平均绝对误差",
        course_id=1,
        kb_version_id=1,
    )
    assert result["error_type"] == "concept_confusion"
    assert "MSE" in result["analysis"]
```

- [ ] **Step 2: Implement diagnose**

```python
import json
from app.gateway.llm_client import LlmClient
from app.core.errors import AppError


async def diagnose(
    session: AsyncSession,
    question: str,
    student_answer: str,
    correct_answer: str,
    course_id: int,
    kb_version_id: int,
    knowledge_point_id: int | None = None,
) -> dict:
    """Diagnose wrong answer and classify error type."""
    from app.services.retrieval import hybrid_retrieve

    # Retrieve relevant chunks
    query = f"知识点 {knowledge_point_id}" if knowledge_point_id else question
    _, fused, _ = await hybrid_retrieve(
        session, question=query, kb_version_id=kb_version_id,
        course_id=course_id, top_k=5,
    )

    context = "\n\n".join(c.get("text", "") for c in fused) if fused else "（无相关教材内容）"

    system = (
        "你是一个教学诊断助手。分析学生的错误答案，判断错误类型。\n"
        "错误类型：\n"
        "- knowledge_gap: 知识盲区（完全未学过相关概念）\n"
        "- concept_confusion: 概念混淆（搞混了相似概念）\n"
        "- misunderstanding: 理解偏差（部分理解但有误）\n"
        "- careless: 粗心大意（非知识性错误）\n\n"
        "请以 JSON 格式返回：{\"error_type\": str, \"analysis\": str, \"suggestion\": str}"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"教材内容：\n{context}\n\n"
            f"题目：{question}\n"
            f"标准答案：{correct_answer}\n"
            f"学生回答：{student_answer}"
        )},
    ]

    llm = LlmClient()
    result = await llm.chat(messages, temperature=0.3)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        raise AppError("SCHEMA_INVALID", "诊断 LLM 返回格式不合法", http_status=422)

    return {
        **parsed,
        "related_chunks": [
            {"chunk_id": c["chunk_id"], "text": c.get("text", "")[:200]}
            for c in (fused or [])
        ],
    }
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_generation.py::test_diagnose_identifies_confusion -v
```
Expected: PASS

---

## Task 4.5: Grading implementation (upgrade from stub)

**Files:**
- Modify: `app/services/generation/__init__.py`
- Test: `tests/test_generation.py`

- [ ] **Step 1: Write failing test**

```python
from app.services.generation import grade_short_answer


@pytest.mark.asyncio
async def test_grade_short_answer_structured(monkeypatch):
    """简答评分应返回结构化 GradeResult。"""
    async def fake_chat(*a, **kw):
        return '{"score": 85, "dimensions": {"完整性": 80, "准确性": 90, "逻辑性": 85}, "reason": "基本正确，可更详细"}'

    monkeypatch.setattr("app.gateway.llm_client.LlmClient.chat", fake_chat)

    result = await grade_short_answer(
        question="什么是机器学习？",
        standard="机器学习是人工智能的一个分支...",
        student="机器学习是 AI 的一个分支...",
    )
    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert "dimensions" in result
    assert "完整性" in result["dimensions"]


@pytest.mark.asyncio
async def test_grade_short_answer_perfect(monkeypatch):
    """标准答案回传应得 100 分。"""
    async def fake_chat(*a, **kw):
        return '{"score": 100, "dimensions": {"完整性": 100, "准确性": 100, "逻辑性": 100}, "reason": "与标准答案完全一致"}'

    monkeypatch.setattr("app.gateway.llm_client.LlmClient.chat", fake_chat)

    result = await grade_short_answer(
        question="1+1=?",
        standard="2",
        student="2",
    )
    assert result["score"] == 100
```

- [ ] **Step 2: Implement grade_short_answer**

```python
import json


async def grade_short_answer(
    question: str,
    standard: str,
    student: str,
) -> dict:
    """Grade a short-answer question with structured result."""
    llm = LlmClient()
    system = (
        "你是一个评分助手。根据标准答案为学生回答打分（0-100），"
        "从完整性、准确性、逻辑性三个维度评分。\n"
        "以 JSON 格式返回：{\"score\": int, \"dimensions\": {\"完整性\": int, \"准确性\": int, \"逻辑性\": int}, \"reason\": str, \"highlight\": str | null}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"标准答案：{standard}\n\n学生回答：{student}\n\n题目：{question}"},
    ]

    result = await llm.chat(messages, temperature=0.3)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return {"score": 0, "dimensions": {}, "reason": "评分 LLM 返回格式异常", "highlight": None}

    return {
        "score": parsed.get("score", 0),
        "dimensions": parsed.get("dimensions", {}),
        "reason": parsed.get("reason", ""),
        "highlight": parsed.get("highlight"),
        "model": llm.model,
    }
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_generation.py::test_grade_short_answer_structured -v
uv run pytest tests/test_generation.py::test_grade_short_answer_perfect -v
```
Expected: all PASS

---

## Task 4.6: API parameter validation + session injection

**Files:**
- Modify: `app/api/internal/v1/questions.py`

- [ ] **Step 1: Update the generate endpoint with proper validation**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.qa import GenerateQuestionsRequest
from app.services.generation import generate_questions

router = APIRouter(tags=["generation"])


@router.post("/questions/generate")
async def generate(
    req: GenerateQuestionsRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """基于知识点检索 chunk → LLM 出题 → schema 校验 → 返回 ai_draft。"""
    result = await generate_questions(
        session=session,
        course_id=req.course_id,
        kb_version_id=req.kb_version_id,
        knowledge_point_id=req.knowledge_point_id,
        count=req.count,
        question_types=req.question_types,
    )
    return {"questions": result, "total": len(result)}


@router.post("/diagnose")
async def diagnose_endpoint(
    req: DiagnoseRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """错题诊断（错因分类）。"""
    from app.services.generation import diagnose
    return await diagnose(
        session=session,
        question=req.question,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        course_id=req.course_id,
        kb_version_id=req.kb_version_id,
        knowledge_point_id=req.knowledge_point_id,
    )


@router.post("/grade/short-answer")
async def grade(
    question: str = Query(..., min_length=1, max_length=2000),
    standard_answer: str = Query(..., min_length=1, alias="standard_answer"),
    student_answer: str = Query(..., min_length=1, alias="student_answer"),
) -> dict:
    """简答题 AI 辅助评分。"""
    from app.services.generation import grade_short_answer
    return await grade_short_answer(question, standard_answer, student_answer)
```

Also add `DiagnoseRequest` import:
```python
from app.schemas.qa import DiagnoseRequest, GenerateQuestionsRequest
```

---

## Task 4.7: Phase 4 tests

- [ ] **Step 1: Run all generation tests**

```bash
uv run pytest tests/test_generation.py -v --tb=short
```
Expected: all PASS

- [ ] **Step 2: Run API handler test**

```bash
uv run pytest tests/ -v -k "test_generate or test_diagnose or test_grade"
```
Expected: all PASS

# Phase 5: RAG Offline Evaluation

## Task 5.1: Evaluation runner

**Files:**
- Modify: `app/services/eval/__init__.py`
- Test: `tests/test_eval.py`

- [ ] **Step 1: Write failing test**

`tests/test_eval.py`:
```python
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_run_evaluation_processes_all_cases(mock_session, monkeypatch):
    """评估 runner 应处理所有 case。"""
    from app.services.eval import run_evaluation

    class FakeCase:
        def __init__(self, id, question):
            self.id = id
            self.question = question
            self.standard_answer = "答案"
            self.allow_reject = False
            self.expected_sources = None
            self.expected_knowledge_point_id = None

    fake_cases = [FakeCase(1, "问题1"), FakeCase(2, "问题2")]

    async def fake_list_by_dataset(*a, **kw):
        return fake_cases

    monkeypatch.setattr(
        "app.services.eval.RagEvalCaseRepo.list_by_dataset",
        fake_list_by_dataset,
    )

    async def fake_retrieve(*a, **kw):
        return "query", [{"chunk_id": 1, "final_score": 0.9}], 100

    async def fake_answer(*a, **kw):
        return {"answer": "回答", "reject_reason": None}

    monkeypatch.setattr("app.services.eval.hybrid_retrieve", fake_retrieve)
    monkeypatch.setattr("app.services.eval.qa_answer", fake_answer)

    results = await run_evaluation(
        session=mock_session, dataset_id=1, kb_version_id=1, run_id=1,
    )
    assert len(results) == 2
```

- [ ] **Step 2: Implement run_evaluation**

`app/services/eval/__init__.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eval import RagEvalResult
from app.repositories.eval_repo import RagEvalCaseRepo, RagEvalResultRepo
from app.services.retrieval import hybrid_retrieve
from app.services.rag import qa_answer


async def run_evaluation(
    session: AsyncSession,
    dataset_id: int,
    knowledge_base_version_id: int,
    run_id: int,
) -> list[dict]:
    """Run evaluation for all cases in a dataset. Returns raw results."""
    case_repo = RagEvalCaseRepo(session)
    result_repo = RagEvalResultRepo(session)
    cases = await case_repo.list_by_dataset(dataset_id)

    results: list[dict] = []

    for case in cases:
        try:
            _, fused, log_ref = await hybrid_retrieve(
                session,
                question=case.question,
                kb_version_id=knowledge_base_version_id,
                top_k=10,
            )

            retrieved_ids = [c["chunk_id"] for c in fused]

            answer_result = await qa_answer(
                session, case.question, fused, message_id=None,
            )
            answer = answer_result.get("answer", "")
            reject_reason = answer_result.get("reject_reason")

            hit_doc = bool(fused)
            recall = 1.0 if hit_doc else 0.0
            mrr_val = 1.0 if fused else 0.0

            eval_result = RagEvalResult(
                run_id=run_id,
                case_id=case.id,
                raw_query=case.question,
                normalized_query=case.question,
                hit_document=hit_doc,
                hit_page=None,
                hit_knowledge_point=None,
                recall_at_k=recall,
                mrr=mrr_val,
                answer_correct=(reject_reason is None),
                citation_correct=None,
                reject_correct=(
                    reject_reason is not None and case.allow_reject
                ) if case.allow_reject else None,
            )
            await result_repo.add(eval_result)

            results.append({
                "case_id": case.id,
                "status": "success",
                "hit_document": hit_doc,
                "answer_length": len(answer),
            })

        except Exception as exc:
            results.append({
                "case_id": case.id,
                "status": "failed",
                "failure_reason": str(exc)[:200],
            })

    await session.flush()
    return results


__all__ = ["run_evaluation"]
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_eval.py::test_run_evaluation_processes_all_cases -v
```
Expected: PASS

---

## Task 5.2: Retrieval metric calculations

**Files:**
- Modify: `app/services/eval/__init__.py`
- Test: `tests/test_eval.py`

- [ ] **Step 1: Write metric tests (pure functions, no mock needed)**

```python
from app.services.eval import calc_recall_at_k, calc_mrr, calc_hit_rate


def test_calc_recall_at_k_perfect():
    """所有相关文档都在 top-k 中。"""
    retrieved = [1, 2, 3, 4, 5]
    relevant = {1, 2, 3}
    assert calc_recall_at_k(retrieved, relevant, k=5) == 1.0


def test_calc_recall_at_k_partial():
    """部分相关文档在 top-k 中。"""
    retrieved = [1, 2, 3, 4, 5]
    relevant = {1, 6, 7}
    assert calc_recall_at_k(retrieved, relevant, k=5) == pytest.approx(1 / 3)


def test_calc_recall_at_k_empty_relevant():
    """无相关文档时 recall=0。"""
    assert calc_recall_at_k([1, 2], set(), k=5) == 0.0


def test_calc_mrr_first_is_relevant():
    """第一个结果就是相关。"""
    assert calc_mrr([1, 2, 3], {1}) == 1.0


def test_calc_mrr_third_is_relevant():
    """第三个结果相关。"""
    assert calc_mrr([1, 2, 3], {3}) == pytest.approx(1 / 3)


def test_calc_mrr_none_relevant():
    """没有相关结果。"""
    assert calc_mrr([1, 2, 3], {4}) == 0.0


def test_calc_hit_rate_all_hit():
    """全部命中。"""
    results = [{"hit_document": True}, {"hit_document": True}]
    assert calc_hit_rate(results, 5) == 1.0


def test_calc_hit_rate_half():
    """一半命中。"""
    results = [{"hit_document": True}, {"hit_document": False}]
    assert calc_hit_rate(results, 5) == 0.5


def test_calc_hit_rate_empty():
    """空结果。"""
    assert calc_hit_rate([], 5) == 0.0
```

- [ ] **Step 2: Implement metric calculations**

Add to `app/services/eval/__init__.py`:
```python
def calc_recall_at_k(retrieved_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Recall@k: proportion of relevant documents in top-k retrieved."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def calc_mrr(retrieved_ids: list[int], relevant_ids: set[int]) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant result."""
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def calc_hit_rate(results: list[dict], top_k: int) -> float:
    """Hit rate: proportion of cases with at least one relevant result."""
    if not results:
        return 0.0
    hits = sum(1 for r in results if r.get("hit_document"))
    return hits / len(results)
```

Update `__all__`:
```python
__all__ = ["run_evaluation", "calc_recall_at_k", "calc_mrr", "calc_hit_rate"]
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_eval.py::test_calc_recall_at_k_perfect -v
uv run pytest tests/test_eval.py::test_calc_mrr_first_is_relevant -v
uv run pytest tests/test_eval.py::test_calc_hit_rate_all_hit -v
```
Expected: all PASS

---

## Task 5.3: QA metric calculations (LLM-as-judge)

**Files:**
- Modify: `app/services/eval/__init__.py`
- Test: `tests/test_eval.py`

- [ ] **Step 1: Write test**

```python
from app.services.eval import calc_answer_correctness, calc_reject_accuracy


@pytest.mark.asyncio
async def test_calc_answer_correctness_match(monkeypatch):
    """语义等价的回答应返回 True。"""
    async def fake_chat(*a, **kw):
        return '{"is_correct": true, "confidence": 0.95}'

    monkeypatch.setattr("app.gateway.llm_client.LlmClient.chat", fake_chat)

    result = await calc_answer_correctness(
        question="1+1=?",
        answer="2",
        standard_answer="2",
    )
    assert result is True


@pytest.mark.asyncio
async def test_calc_answer_correctness_mismatch(monkeypatch):
    """语义不等价的回答应返回 False。"""
    async def fake_chat(*a, **kw):
        return '{"is_correct": false, "confidence": 0.90}'

    monkeypatch.setattr("app.gateway.llm_client.LlmClient.chat", fake_chat)

    result = await calc_answer_correctness(
        question="1+1=?",
        answer="3",
        standard_answer="2",
    )
    assert result is False


def test_calc_reject_accuracy():
    """拒答准确率计算。"""
    results = [
        {"reject_correct": True},
        {"reject_correct": True},
        {"reject_correct": False},
    ]
    assert calc_reject_accuracy(results) == pytest.approx(2 / 3)
```

- [ ] **Step 2: Implement QA metrics**

Add to `app/services/eval/__init__.py`:
```python
import json
from app.gateway.llm_client import LlmClient


async def calc_answer_correctness(
    question: str,
    answer: str,
    standard_answer: str,
) -> bool:
    """Use LLM-as-judge to determine if answer is semantically correct."""
    if not answer.strip():
        return False
    llm = LlmClient()
    system = (
        "你是一个评判助手。判断 AI 的回答是否与标准答案语义等价。"
        "注意同义表达也应被视为正确。"
        "以 JSON 格式返回：{\"is_correct\": bool, \"confidence\": float}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"问题：{question}\n标准答案：{standard_answer}\nAI 回答：{answer}"},
    ]
    result = await llm.chat(messages, temperature=0.2)
    try:
        parsed = json.loads(result)
        return bool(parsed.get("is_correct", False))
    except (json.JSONDecodeError, ValueError):
        return False


def calc_reject_accuracy(results: list[dict]) -> float:
    """Proportion of cases where reject decision was correct."""
    reject_cases = [r for r in results if r.get("reject_correct") is not None]
    if not reject_cases:
        return 0.0
    correct = sum(1 for r in reject_cases if r["reject_correct"])
    return correct / len(reject_cases)
```

Update `__all__`:
```python
__all__ = [
    "run_evaluation",
    "calc_recall_at_k", "calc_mrr", "calc_hit_rate",
    "calc_answer_correctness", "calc_reject_accuracy",
]
```

- [ ] **Step 3: Verify**

```bash
uv run pytest tests/test_eval.py::test_calc_answer_correctness_match -v
uv run pytest tests/test_eval.py::test_calc_reject_accuracy -v
```
Expected: all PASS

---

## Task 5.4: Report generation (with Alembic migration)

**Files:**
- Modify: `app/services/eval/__init__.py`
- Create: `alembic/versions/0004_eval_report_json.py`
- Test: `tests/test_eval.py`

- [ ] **Step 1: Add report_json column to RagEvalRun**

Create `alembic/versions/0004_eval_report_json.py`:
```python
"""add report_json to rag_eval_run

Revision ID: 0004
Revises: 0003
"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"


def upgrade():
    op.add_column(
        "rag_eval_run",
        sa.Column("report_json", JSONB, nullable=True),
        schema="ai",
    )


def downgrade():
    op.drop_column("rag_eval_run", "report_json", schema="ai")
```

- [ ] **Step 2: Write report test**

```python
from app.services.eval import generate_eval_report


def test_generate_report_empty():
    """空结果报告。"""
    report = generate_eval_report([])
    assert "error" in report


def test_generate_report_basic():
    """基本报告应包含所有聚合指标。"""
    results = [
        {"recall_at_k": 1.0, "mrr": 1.0, "hit_document": True, "answer_correct": True},
        {"recall_at_k": 0.5, "mrr": 0.5, "hit_document": True, "answer_correct": False},
        {"recall_at_k": 0.0, "mrr": 0.0, "hit_document": False, "answer_correct": False, "failure_reason": "超时"},
    ]
    report = generate_eval_report(results)
    assert report["total_cases"] == 3
    assert report["avg_recall_at_k"] == pytest.approx(0.5)
    assert report["avg_mrr"] == pytest.approx(0.5)
    assert report["hit_rate"] == pytest.approx(2 / 3)
    assert report["answer_correct_rate"] == pytest.approx(1 / 3)
    assert len(report["failed_cases"]) == 1
```

- [ ] **Step 3: Implement generate_eval_report**

Add to `app/services/eval/__init__.py`:
```python
def generate_eval_report(results: list[dict]) -> dict:
    """Aggregate individual evaluation results into a summary report."""
    n = len(results)
    if n == 0:
        return {"error": "no results"}
    return {
        "total_cases": n,
        "avg_recall_at_k": sum(r.get("recall_at_k", 0) or 0 for r in results) / n,
        "avg_mrr": sum(r.get("mrr", 0) or 0 for r in results) / n,
        "hit_rate": sum(1 for r in results if r.get("hit_document")) / n,
        "answer_correct_rate": (
            sum(1 for r in results if r.get("answer_correct")) / n
            if any(r.get("answer_correct") is not None for r in results)
            else None
        ),
        "reject_accuracy": (
            sum(1 for r in results if r.get("reject_correct")) / n
            if any(r.get("reject_correct") is not None for r in results)
            else None
        ),
        "failed_cases": [
            {"case_id": r.get("case_id"), "reason": r.get("failure_reason")}
            for r in results if r.get("failure_reason")
        ],
    }
```

Update `__all__`:
```python
__all__ = [
    "run_evaluation",
    "calc_recall_at_k", "calc_mrr", "calc_hit_rate",
    "calc_answer_correctness", "calc_reject_accuracy",
    "generate_eval_report",
]
```

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/test_eval.py::test_generate_report_basic -v
```
Expected: PASS

---

## Task 5.5: Evaluation API endpoints

**Files:**
- Modify: `app/api/internal/v1/eval.py`

- [ ] **Step 1: Add new endpoints**

```python
from fastapi import Query
from app.core.errors import AppError
from app.schemas.common import Page
from app.models.eval import RagEvalCase, RagEvalDataset, RagEvalResult, RagEvalRun
from app.repositories.eval_repo import RagEvalCaseRepo, RagEvalDatasetRepo, RagEvalResultRepo, RagEvalRunRepo


@router.get("/datasets")
async def list_datasets(
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> Page[dict]:
    """数据集列表。"""
    repo = RagEvalDatasetRepo(session)
    total = await repo.count()
    datasets = await repo.find(
        order_by=RagEvalDataset.id.desc(),
        limit=size, offset=(page - 1) * size,
    )
    items = [
        {"id": d.id, "name": d.name, "description": d.description, "status": d.status}
        for d in datasets
    ]
    return Page(items=items, total=total, page=page, page_size=size)


@router.get("/datasets/{dataset_id}/cases")
async def list_cases(
    dataset_id: int,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> Page[dict]:
    """数据集的所有 case。"""
    repo = RagEvalCaseRepo(session)
    total = await repo.count(RagEvalCase.dataset_id == dataset_id)
    cases = await repo.find(
        RagEvalCase.dataset_id == dataset_id,
        order_by=RagEvalCase.id, limit=size,
        offset=(page - 1) * size,
    )
    items = [
        {
            "id": c.id, "question": c.question,
            "difficulty": c.difficulty, "question_type": c.question_type,
        }
        for c in cases
    ]
    return Page(items=items, total=total, page=page, page_size=size)


@router.get("/runs/{run_id}/results")
async def list_results(
    run_id: int,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> Page[dict]:
    """运行结果明细。"""
    repo = RagEvalResultRepo(session)
    total = await repo.count(RagEvalResult.run_id == run_id)
    results = await repo.find(
        RagEvalResult.run_id == run_id,
        order_by=RagEvalResult.id, limit=size,
        offset=(page - 1) * size,
    )
    items = [
        {
            "case_id": r.case_id,
            "hit_document": r.hit_document,
            "recall_at_k": float(r.recall_at_k) if r.recall_at_k else None,
            "mrr": float(r.mrr) if r.mrr else None,
            "answer_correct": r.answer_correct,
            "failure_reason": r.failure_reason,
        }
        for r in results
    ]
    return Page(items=items, total=total, page=page, page_size=size)


@router.get("/runs/compare")
async def compare_runs(
    id1: int = Query(..., alias="id1"),
    id2: int = Query(..., alias="id2"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """两个 run 的指标对比。"""
    from app.services.eval import generate_eval_report

    result_repo = RagEvalResultRepo(session)
    repo = RagEvalRunRepo(session)

    run1 = await repo.get(id1)
    run2 = await repo.get(id2)
    if not run1 or not run2:
        raise AppError("NOT_FOUND", "评估运行不存在", http_status=404)

    r1_results = await result_repo.find(RagEvalResult.run_id == id1)
    r2_results = await result_repo.find(RagEvalResult.run_id == id2)

    return {
        "run1": {"id": id1, "report": generate_eval_report([vars(r) for r in r1_results])},
        "run2": {"id": id2, "report": generate_eval_report([vars(r) for r in r2_results])},
    }
```

- [ ] **Step 2: Verify**

```bash
uv run pytest tests/ -v -k "eval"
```
Expected: all PASS

---

## Task 5.6: Phase 5 tests

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v --tb=short
```
Expected: all 50+ tests PASS, coverage ≥ 80%

---

## Execution Order Summary

| Order | Task | Depends On |
|-------|------|-----------|
| 1 | 1.0 Parse task API contract | — |
| 2 | 1.1 Add dependencies | — |
| 3 | 1.2 PDF parser | 1.1 |
| 4 | 1.3 PPTX parser | 1.1 |
| 5 | 1.4 DOCX parser | 1.1 |
| 6 | 1.5 XLSX parser | 1.1 |
| 7 | 1.6 File downloader | — |
| 8 | 1.7 Dispatcher | 1.2-1.5 |
| 9 | 1.8 Retry decorator | — |
| 10 | 1.9 Update handler | 1.0, 1.6, 1.7 |
| 11 | 1.10 Phase 1 tests | 1.0-1.9 |
| 12 | 2.1 Chunk config | — |
| 13 | 2.2 Semantic chunk | — |
| 14 | 2.3 Concurrency | — |
| 15-17 | 2.4-2.6 Worker enhancements | 2.3 |
| 18 | 2.7 Metrics | — |
| 19 | 2.8 Batch API | — |
| 20 | 2.9 Phase 2 tests | 2.1-2.8 |
| 21 | 3.1 SSE streaming | — |
| 22 | 3.2 Query rewrite | — |
| 23 | 3.3 Multi-turn | — |
| 24 | 3.4 Citation | — |
| 25 | 3.5 Degradation | — |
| 26 | 3.6 MMR | — |
| 27 | 3.7 Prompt config | — |
| 28 | 3.8 Phase 3 tests | 3.1-3.7 |
| 29 | 4.1 Prompt integration | 3.7 |
| 30 | 4.2 AI question gen | 4.1 |
| 31 | 4.3 Schema design | — |
| 32 | 4.4 Diagnosis | 4.1 |
| 33 | 4.5 Grading | 4.1 |
| 34 | 4.6 API validation | — |
| 34 | 4.7 Phase 4 tests | 4.1-4.6 |
| 35 | 5.1 Eval runner | 3.5 |
| 36 | 5.2 Retrieval metrics | — |
| 37 | 5.3 QA metrics | — |
| 38 | 5.4 Report | 5.2, 5.3 |
| 39 | 5.5 Eval API | — |
| 40 | 5.6 Phase 5 tests | 5.1-5.5 |
