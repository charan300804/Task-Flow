import redis.asyncio as aioredis
import redis as sync_redis
from typing import AsyncGenerator, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Async Redis Pool
async_redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    decode_responses=True
)

def get_async_redis_client() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=async_redis_pool)

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = get_async_redis_client()
    try:
        yield client
    finally:
        await client.aclose()

# Sync Redis client factory for sync worker tasks
def get_sync_redis_client() -> sync_redis.Redis:
    return sync_redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
