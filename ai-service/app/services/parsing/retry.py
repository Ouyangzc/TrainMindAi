"""Retry helpers for parsing pipeline."""

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from app.core.errors import AppError

P = ParamSpec("P")
T = TypeVar("T")


def parse_retry(
    retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 120.0,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry transient parser/downloader failures with exponential backoff."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(retries + 1):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except AppError:
                    raise
                except TimeoutError as exc:
                    raise AppError(
                        "PARSE_TIMEOUT",
                        f"解析超时 ({timeout}s)",
                        http_status=504,
                    ) from exc
                except (ConnectionError, OSError) as exc:
                    last_exc = exc
                    if attempt >= retries:
                        raise
                    if base_delay > 0:
                        await asyncio.sleep(base_delay * (4**attempt))
            if last_exc is not None:
                raise last_exc
            raise RuntimeError("parse retry exhausted without exception")

        return wrapper

    return decorator
