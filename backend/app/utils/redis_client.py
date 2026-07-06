import redis.asyncio as aioredis
from app.config import settings
import logging
import json
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        try:
            self._client = aioredis.from_url(
                settings.get_redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            await self._client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to no-cache mode.")
            self._client = None

    async def disconnect(self):
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    async def get(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET error for {key}: {e}")
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if not self._client:
            return False
        try:
            await self._client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for {key}: {e}")
            return False

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        if not self._client:
            return False
        try:
            await self._client.setex(key, seconds, value)
            return True
        except Exception as e:
            logger.warning(f"Redis SETEX error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE error for {key}: {e}")
            return False

    async def incr(self, key: str) -> Optional[int]:
        if not self._client:
            return None
        try:
            return await self._client.incr(key)
        except Exception as e:
            logger.warning(f"Redis INCR error for {key}: {e}")
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(value), ex=ex)

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False


redis_client = RedisClient()
