"""MinIO file downloader for parsing tasks."""

import asyncio
import functools
import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from minio import Minio

from app.core.config import settings
from app.core.errors import AppError


class MinIOClient:
    """Lazy MinIO client wrapper."""

    _client: Minio | None = None

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
        """Download object from MinIO to local path."""
        client = MinIOClient.get_client()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            functools.partial(client.fget_object, bucket, object_name, local_path),
        )


def _md5(path: str) -> str:
    digest = hashlib.md5()  # noqa: S324
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cleanup_download(local_path: str | None) -> None:
    """Remove the temporary directory containing a downloaded file."""
    if not local_path:
        return
    tmp_dir = os.path.dirname(local_path)
    if tmp_dir:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def download_from_minio(
    bucket: str,
    object_name: str,
    expected_md5: str | None = None,
    timeout_seconds: float = 30,
) -> str:
    """Download an object to a temporary local path."""
    ext = os.path.splitext(object_name)[1] or ".bin"
    tmp_dir = tempfile.mkdtemp(prefix="ai_parse_")
    local_path = os.path.join(tmp_dir, f"file{ext}")

    try:
        await asyncio.wait_for(
            MinIOClient.get_file(bucket, object_name, local_path),
            timeout=timeout_seconds,
        )
    except TimeoutError as exc:
        cleanup_download(local_path)
        raise AppError(
            "FILE_DOWNLOAD_TIMEOUT",
            f"MinIO 下载超时 ({timeout_seconds}s)",
            http_status=504,
        ) from exc
    except Exception:
        cleanup_download(local_path)
        raise

    if expected_md5 and _md5(local_path).lower() != expected_md5.lower():
        cleanup_download(local_path)
        raise AppError(
            "FILE_CHECKSUM_MISMATCH",
            "文件 MD5 校验失败",
            http_status=400,
        )

    return local_path
