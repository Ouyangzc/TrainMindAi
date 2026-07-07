"""pytest 共享 fixtures。使用 mock session 隔离外部依赖。"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def mock_session() -> AsyncGenerator[AsyncSession, None]:
    """提供一个 mock AsyncSession，所有 execute/flush/commit 均为 no-op。"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock()
    yield session
