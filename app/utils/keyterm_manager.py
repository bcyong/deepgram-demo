from . import storage_client
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
