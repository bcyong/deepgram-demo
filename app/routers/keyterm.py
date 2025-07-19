from fastapi import APIRouter
from ..utils import keyterm_manager
import pydantic
from loguru import logger

router = APIRouter(prefix="/api/v1/keyterm")


class KeytermRequest(pydantic.BaseModel):
    keyterm: str


@router.post("/add", tags=["keyterm"])
async def add_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Adding keyterm: {keyterm_request.keyterm}")
    await keyterm_manager.add_keyterm(keyterm_request.keyterm)
    return {"message": "Keyterm added"}


@router.post("/delete", tags=["keyterm"])
async def delete_keyterm(keyterm_request: KeytermRequest):
    logger.info(f"Deleting keyterm: {keyterm_request.keyterm}")
    await keyterm_manager.delete_keyterm(keyterm_request.keyterm)
    return {"message": "Keyterm deleted"}


@router.get("/list", tags=["keyterm"])
async def list_keyterms():
    logger.info("Listing keyterms")
    keyterms = await keyterm_manager.get_all_keyterms()
    return {"keyterms": keyterms}
