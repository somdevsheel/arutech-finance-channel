"""Application-level rate limiting, backed by Redis so limits are shared
across every API instance rather than tracked per-process."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from arutech_api.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_uri,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)
