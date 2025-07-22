import redis.asyncio as redis
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

REDIS_LINK = os.getenv("REDIS_LINK", "redis://localhost:6379")

# Cache for Redis client
_redis_client = None


def get_redis_client():
    global _redis_client
    try:
        if _redis_client is None:
            _redis_client = redis.Redis.from_url(REDIS_LINK)
        return _redis_client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        return None


async def set_value(key: str, value: str):
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.set(key, value)
    else:
        logger.warning(f"Redis client not available, cannot set value for key: {key}")


async def get_value(key: str):
    redis_client = get_redis_client()
    if redis_client:
        return await redis_client.get(key)
    else:
        logger.warning(f"Redis client not available, cannot get value for key: {key}")
        return None


async def delete_value(key: str):
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.delete(key)
    else:
        logger.warning(f"Redis client not available, cannot delete key: {key}")


async def delete_all_keys():
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.flushall()
    else:
        logger.warning("Redis client not available, cannot delete all keys.")


async def get_all_keys():
    redis_client = get_redis_client()
    if redis_client:
        return await redis_client.keys()
    else:
        logger.warning("Redis client not available, cannot get all keys.")
        return []


async def get_all_keys_with_prefix(prefix: str):
    redis_client = get_redis_client()
    if redis_client:
        return await redis_client.keys(f"{prefix}*")
    else:
        logger.warning("Redis client not available, cannot get all keys with prefix.")
        return []
