from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from arutech_api.api.v1.router import api_router
from arutech_api.core.config import settings
from arutech_api.core.database import engine
from arutech_api.core.exceptions import register_exception_handlers
from arutech_api.core.logging import configure_logging, get_logger
from arutech_api.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from arutech_api.core.rate_limit import limiter
from arutech_api.core.redis import redis_client
from arutech_api.core.telemetry import configure_telemetry

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", environment=settings.ENVIRONMENT)
    yield
    logger.info("shutdown")
    await engine.dispose()
    await redis_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    register_exception_handlers(app)

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Outermost middleware (added last = runs first): rewrites request.client
    # from X-Forwarded-For/X-Forwarded-Proto, but only when the immediate
    # peer is in TRUSTED_PROXY_IPS. Everything downstream — rate limiting
    # (get_remote_address), audit logging (get_client_ip) — reads
    # request.client, so this must run before they do.
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.TRUSTED_PROXY_IPS)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    configure_telemetry(app)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "arutech_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
