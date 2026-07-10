"""S3-compatible file downloader for parsing tasks."""

import asyncio
import functools
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from app.core.config import settings
from app.core.errors import AppError


class ObjectStorageClient:
    """Lazy S3-compatible object storage client wrapper."""

    _client: Any = None

    @classmethod
    def get_client(cls) -> Any:
        if cls._client is None:
            addressing_style = "path" if settings.object_storage_path_style else "auto"
            s3_config = Config(s3={"addressing_style": addressing_style})
            cls._client = boto3.client(
                "s3",
                endpoint_url=settings.object_storage_endpoint,
                aws_access_key_id=settings.object_storage_access_key,
                aws_secret_access_key=settings.object_storage_secret_key,
                region_name=settings.object_storage_region,
                config=s3_config,
            )
        return cls._client

    @staticmethod
    async def get_file(bucket: str, object_name: str, local_path: str) -> None:
        """Download object from S3-compatible storage to local path."""
        client = ObjectStorageClient.get_client()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            functools.partial(client.download_file, bucket, object_name, local_path),
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


async def download_from_object_storage(
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
            ObjectStorageClient.get_file(bucket, object_name, local_path),
            timeout=timeout_seconds,
        )
    except TimeoutError as exc:
        cleanup_download(local_path)
        raise AppError(
            "FILE_DOWNLOAD_TIMEOUT",
            f"对象存储下载超时 ({timeout_seconds}s)",
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
