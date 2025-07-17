from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

@router.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok"}

@router.get("/health/ready", tags=["health"])
async def ready():
    return {"status": "ok"}