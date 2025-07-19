from fastapi import APIRouter
from ..utils import keyterm_manager
import pydantic
from loguru import logger
from typing import List

router = APIRouter(prefix="/api/v1/keyterm")


class KeytermRequest(pydantic.BaseModel):
    keyterms: List[str]


@router.post("/add", tags=["keyterm"])
async def add_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Adding keyterms: {keyterm_request.keyterms}")
    await keyterm_manager.add_keyterms(keyterm_request.keyterms)
    return {"message": f"Keyterms {keyterm_request.keyterms} added"}


@router.delete("/delete", tags=["keyterm"])
async def delete_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Deleting keyterms: {keyterm_request.keyterms}")
    await keyterm_manager.delete_keyterms(keyterm_request.keyterms)
    return {"message": f"Keyterms {keyterm_request.keyterms} deleted"}


@router.get("/list", tags=["keyterm"])
async def list_keyterms():
    logger.info("Listing keyterms")
    keyterms = await keyterm_manager.get_all_keyterms()
    return {"keyterms": keyterms}
