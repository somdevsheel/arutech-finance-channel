from fastapi import APIRouter, Response, status

from arutech_api.core.config import settings
from arutech_api.core.database import check_database_connection
from arutech_api.core.redis import check_redis_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness() -> dict[str, str]:
    """Liveness probe: process is up. No dependency checks — used by the
    orchestrator to decide whether to restart the container."""
    return {
        "status": "ok",
        "service": settings.OTEL_SERVICE_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness(response: Response) -> dict[str, object]:
    """Readiness probe: process is up AND its dependencies are reachable.
    Used to decide whether to route traffic to this instance."""
    checks = {
        "database": "ok" if await check_database_connection() else "error",
        "redis": "ok" if await check_redis_connection() else "error",
    }
    overall = "ok" if all(v == "ok" for v in checks.values()) else "error"

    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": overall, "checks": checks}
