import redis
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

REDIS_LINK = os.getenv("REDIS_LINK", "redis://localhost:6379")


def get_redis_client():
    try:
        return redis.Redis.from_url(REDIS_LINK)
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        return None


def set_value(key: str, value: str):
    redis_client = get_redis_client()
    if redis_client:
        redis_client.set(key, value)
    else:
        logger.warning(f"Redis client not available, cannot set value for key: {key}")


def get_value(key: str):
    redis_client = get_redis_client()
    if redis_client:
        return redis_client.get(key)
    else:
        logger.warning(f"Redis client not available, cannot get value for key: {key}")
        return None


def delete_value(key: str):
    redis_client = get_redis_client()
    if redis_client:
        redis_client.delete(key)
    else:
        logger.warning(f"Redis client not available, cannot delete key: {key}")


def delete_all_keys():
    redis_client = get_redis_client()
    if redis_client:
        redis_client.flushall()
    else:
        logger.warning("Redis client not available, cannot delete all keys.")


def get_all_keys():
    redis_client = get_redis_client()
    if redis_client:
        return redis_client.keys()
    else:
        logger.warning("Redis client not available, cannot get all keys.")
        return []


def get_all_keys_with_prefix(prefix: str):
    redis_client = get_redis_client()
    if redis_client:
        return redis_client.keys(f"{prefix}*")
    else:
        logger.warning("Redis client not available, cannot get all keys with prefix.")
        return []
