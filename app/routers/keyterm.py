from fastapi import APIRouter
from ..utils import keyterm_manager
import pydantic
from loguru import logger

router = APIRouter(prefix="/api/v1/keyterm")


class KeytermRequest(pydantic.BaseModel):
    keyterm: str


@router.post("/add")
async def add_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Adding keyterm: {keyterm_request.keyterm}")
    keyterm_manager.add_keyterm(keyterm_request.keyterm)
    return {"message": "Keyterm added"}


@router.post("/delete")
async def delete_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Deleting keyterm: {keyterm_request.keyterm}")
    keyterm_manager.delete_keyterm(keyterm_request.keyterm)
    return {"message": "Keyterm deleted"}


@router.get("/list")
async def list_keyterms():
    logger.info("Listing keyterms")
    keyterms = keyterm_manager.get_all_keyterms()
    return {"keyterms": keyterms}
