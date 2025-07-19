from fastapi import APIRouter
from ..utils import keyword_manager
import pydantic
from loguru import logger
from typing import Dict, List

router = APIRouter(prefix="/api/v1/keyword")


class KeywordAddRequest(pydantic.BaseModel):
    keywords: Dict[str, int]


class KeywordDeleteRequest(pydantic.BaseModel):
    keywords: List[str]


@router.post("/add", tags=["keyword"])
async def add_keyword(keyword_request: KeywordAddRequest):
    logger.info(f"Adding keywords: {keyword_request.keywords}")
    await keyword_manager.add_keywords(keyword_request.keywords)
    return {"message": f"Keywords {keyword_request.keywords} added"}


@router.post("/delete", tags=["keyword"])
async def delete_keyword(keyword_request: KeywordDeleteRequest):
    logger.info(f"Deleting keywords: {keyword_request.keywords}")
    await keyword_manager.delete_keywords(keyword_request.keywords.keys())
    return {"message": f"Keywords {keyword_request.keywords} deleted"}


@router.get("/list", tags=["keyword"])
async def list_keywords():
    logger.info("Listing keywords")
    keywords = await keyword_manager.get_all_keywords()
    return {"keywords": keywords}
