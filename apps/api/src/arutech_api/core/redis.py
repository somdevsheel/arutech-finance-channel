import redis.asyncio as redis

from arutech_api.core.config import settings

redis_client: redis.Redis = redis.from_url(  # type: ignore[no-untyped-call]
    settings.REDIS_URL, decode_responses=True
)


async def get_redis() -> redis.Redis:
    return redis_client


async def check_redis_connection() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False
