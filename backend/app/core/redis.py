import logging
from typing import Optional
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
from app.core.config import settings

logger = logging.getLogger("TaskFlowRedis")

# Global Redis Async Connection Pool
pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True,
    max_connections=50,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    retry_on_timeout=True
)

async def get_redis() -> Redis:
    """FastAPI dependency for async Redis client."""
    return Redis(connection_pool=pool)

async def ping_redis(client: Redis) -> bool:
    """Helper method to verify active Redis connectivity."""
    try:
        return await client.ping()
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis connectivity check failed: {e}")
        return False
