"""健康检查端点测试（无需鉴权）。"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_live(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
