"""Redis 连接（异步）。用于任务信号、缓存、限流。"""

from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> Redis:
    return redis_client
