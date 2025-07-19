import storage_client
from loguru import logger


def add_keyterm(keyterm: str):
    """Store a keyterm with 'keyterm:' prefix"""
    key = f"keyterm:{keyterm}"
    storage_client.set_value(key, "1")
    logger.info(f"Stored keyterm: {keyterm}")


def delete_keyterm(keyterm: str):
    """Delete a keyterm with 'keyterm:' prefix"""
    key = f"keyterm:{keyterm}"
    storage_client.delete_value(key)
    logger.info(f"Deleted keyterm: {keyterm}")


def get_all_keyterms():
    """Get all keyterms with 'keyterm:' prefix"""
    return storage_client.get_all_keys_with_prefix("keyterm:")


def delete_all_keyterms():
    """Delete all keyterms with 'keyterm:' prefix"""
    redis_client = storage_client.get_redis_client()
    if redis_client:
        deleted_count = 0
        for key in redis_client.scan_iter(match="keyterm:*"):
            redis_client.delete(key)
            deleted_count += 1
        logger.info(f"Deleted {deleted_count} keyterms")
    else:
        logger.warning("Redis client not available, cannot delete all keyterms")
