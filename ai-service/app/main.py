"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.internal.v1.router import health_router, internal_router
from app.core.config import settings
from app.core.db import engine
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.redis import redis_client

setup_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("ai_service.startup", env=settings.app_env, vector_store=settings.vector_store)
    yield
    await engine.dispose()
    await redis_client.aclose()
    log.info("ai_service.shutdown")


app = FastAPI(
    title="TrainMindAi AI 服务",
    description="企业级知识助教系统 - 解析/RAG/出题/评估（内网服务，由 RuoYi 调用）",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(internal_router)
