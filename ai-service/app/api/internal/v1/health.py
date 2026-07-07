"""健康检查（无需鉴权）。"""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine
from app.core.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    """存活探针：进程在即 200。"""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict[str, object]:
    """就绪探针：探测 DB 与 Redis。"""
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["db"] = f"error: {exc.__class__.__name__}"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc.__class__.__name__}"

    ready = all(v == "ok" for v in checks.values())
    return {"status": "ok" if ready else "degraded", "checks": checks}
