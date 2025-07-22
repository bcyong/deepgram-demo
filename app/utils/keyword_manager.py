from . import storage_client
from loguru import logger
from typing import List, Dict


async def add_keyword(keyword: str, value: int):
    """Store a keyword with 'keyword:' prefix"""
    key = f"keyword:{keyword}"
    await storage_client.set_value(key, str(value))
    logger.info(f"Stored keyword: {keyword}:{value}")


async def add_keywords(keywords: Dict[str, int]):
    """Store a list of keywords with 'keyword:' prefix"""
    for keyword, value in keywords.items():
        key = f"keyword:{keyword}"
        await storage_client.set_value(key, str(value))
    logger.info(f"Stored {len(keywords)} keywords")


async def delete_keyword(keyword: str):
    """Delete a keyword with 'keyword:' prefix"""
    key = f"keyword:{keyword}"
    await storage_client.delete_value(key)
    logger.info(f"Deleted keyword: {keyword}")


async def delete_keywords(keywords: List[str]):
    """Delete a list of keywords with 'keyword:' prefix"""
    for keyword in keywords:
        key = f"keyword:{keyword}"
        await storage_client.delete_value(key)
    logger.info(f"Deleted {len(keywords)} keywords")


async def get_all_keywords():
    """Get all keywords with 'keyword:' prefix"""
    try:
        all_keys = await storage_client.get_all_keys_with_prefix("keyword:")

        if all_keys:
            result = []
            for key in all_keys:
                key_str = key.decode("utf-8").replace("keyword:", "")
                value = await storage_client.get_value(f"keyword:{key_str}")
                if value:
                    value_str = (
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )
                    result.append(f"{key_str}:{value_str}")
            return result
        else:
            return []
    except Exception as e:
        logger.warning(f"Error getting keywords: {e}")
        return []
