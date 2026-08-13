import logging
import uuid
from typing import Optional
import redis as sync_redis

logger = logging.getLogger(__name__)

# Lua script to release lock only if token matches
RELEASE_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

class DistributedLock:
    def __init__(self, redis_client: sync_redis.Redis, name: str, timeout_seconds: int = 60):
        self.redis = redis_client
        self.key = f"lock:job:{name}"
        self.timeout_ms = int(timeout_seconds * 1000)
        self.token = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        """Attempt to acquire distributed lock."""
        res = self.redis.set(self.key, self.token, nx=True, px=self.timeout_ms)
        self.acquired = bool(res)
        return self.acquired

    def release(self) -> bool:
        """Safely release distributed lock using Lua script."""
        if not self.acquired:
            return False
        try:
            res = self.redis.eval(RELEASE_LOCK_LUA, 1, self.key, self.token)
            self.acquired = False
            return bool(res)
        except Exception as e:
            logger.error(f"Error releasing lock {self.key}: {e}")
            return False

    def extend(self, additional_seconds: int = 30) -> bool:
        """Extend lock TTL if token still matches."""
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("pexpire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        try:
            res = self.redis.eval(script, 1, self.key, self.token, int(additional_seconds * 1000))
            return bool(res)
        except Exception as e:
            logger.error(f"Error extending lock {self.key}: {e}")
            return False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for {self.key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
