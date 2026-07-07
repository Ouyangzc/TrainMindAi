"""MinIO downloader tests."""

import hashlib
from pathlib import Path

import pytest

from app.core.errors import AppError


@pytest.mark.asyncio
async def test_download_from_minio_returns_local_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.parsing import file_downloader

    async def fake_get_file(bucket: str, object_name: str, local_path: str) -> None:
        Path(local_path).write_bytes(b"hello")

    monkeypatch.setattr(file_downloader.MinIOClient, "get_file", fake_get_file)

    path = await file_downloader.download_from_minio(
        bucket="kb-docs",
        object_name="docs/test.pdf",
        expected_md5=hashlib.md5(b"hello").hexdigest(),  # noqa: S324
    )

    try:
        assert path.endswith(".pdf")
        assert Path(path).read_bytes() == b"hello"
    finally:
        file_downloader.cleanup_download(path)


@pytest.mark.asyncio
async def test_download_from_minio_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from app.services.parsing import file_downloader

    async def fake_get_file(bucket: str, object_name: str, local_path: str) -> None:
        await asyncio.sleep(0.05)

    monkeypatch.setattr(file_downloader.MinIOClient, "get_file", fake_get_file)

    with pytest.raises(AppError) as exc:
        await file_downloader.download_from_minio(
            bucket="kb-docs",
            object_name="docs/test.pdf",
            timeout_seconds=0.001,
        )

    assert exc.value.code == "FILE_DOWNLOAD_TIMEOUT"


@pytest.mark.asyncio
async def test_download_from_minio_rejects_checksum_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.parsing import file_downloader

    async def fake_get_file(bucket: str, object_name: str, local_path: str) -> None:
        Path(local_path).write_bytes(b"actual")

    monkeypatch.setattr(file_downloader.MinIOClient, "get_file", fake_get_file)

    with pytest.raises(AppError) as exc:
        await file_downloader.download_from_minio(
            bucket="kb-docs",
            object_name="docs/test.pdf",
            expected_md5=hashlib.md5(b"expected").hexdigest(),  # noqa: S324
        )

    assert exc.value.code == "FILE_CHECKSUM_MISMATCH"
