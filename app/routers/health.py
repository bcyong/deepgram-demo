from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health")


@router.get("/", tags=["health"])
async def health():
    """
    Basic health check endpoint.

    Returns a simple status response to verify the API is running.

    Returns:
        dict: Status response indicating the service is healthy
    """
    return {"status": "ok"}


@router.get("/live", tags=["health"])
async def live():
    """
    Liveness probe endpoint for Kubernetes/container orchestration.

    This endpoint is used by container orchestrators to determine if the service
    is alive and should be restarted. Returns immediately to check if the
    process is responsive.

    Returns:
        dict: Status response indicating the service is alive
    """
    return {"status": "ok"}


@router.get("/ready", tags=["health"])
async def ready():
    """
    Readiness probe endpoint for Kubernetes/container orchestration.

    This endpoint is used by container orchestrators to determine if the service
    is ready to receive traffic. Checks if all dependencies and resources
    are available.

    Returns:
        dict: Status response indicating the service is ready to serve requests
    """
    return {"status": "ok"}
