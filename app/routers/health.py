from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/health')

@router.get("/", tags=["health"])
async def health():
    return {"status": "ok"}

@router.get("/live", tags=["health"])
async def live():
    return {"status": "ok"}

@router.get("/ready", tags=["health"])
async def ready():
    return {"status": "ok"}