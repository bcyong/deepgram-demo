from . import storage_client
from loguru import logger
from typing import List


async def add_keyterm(keyterm: str):
    """Store a keyterm with 'keyterm:' prefix"""
    key = f"keyterm:{keyterm}"
    await storage_client.set_value(key, "1")
    logger.info(f"Stored keyterm: {keyterm}")


async def add_keyterms(keyterms: List[str]):
    """Store a list of keyterms with 'keyterm:' prefix"""
    for keyterm in keyterms:
        key = f"keyterm:{keyterm}"
        await storage_client.set_value(key, "1")
    logger.info(f"Stored {len(keyterms)} keyterms")


async def delete_keyterm(keyterm: str):
    """Delete a keyterm with 'keyterm:' prefix"""
    key = f"keyterm:{keyterm}"
    await storage_client.delete_value(key)
    logger.info(f"Deleted keyterm: {keyterm}")


async def delete_keyterms(keyterms: List[str]):
    """Delete a list of keyterms with 'keyterm:' prefix"""
    for keyterm in keyterms:
        key = f"keyterm:{keyterm}"
        await storage_client.delete_value(key)
    logger.info(f"Deleted {len(keyterms)} keyterms")


async def get_all_keyterms():
    """Get all keyterms with 'keyterm:' prefix"""
    try:
        all_keys = await storage_client.get_all_keys_with_prefix("keyterm:")

        if all_keys:
            return [key.decode("utf-8").replace("keyterm:", "") for key in all_keys]
        else:
            return []
    except Exception as e:
        logger.warning(f"Error getting keyterms: {e}")
        return []
