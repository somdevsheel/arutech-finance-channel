from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from arutech_api.core.config import settings
from arutech_api.infrastructure.database.base import Base


@pytest.fixture(scope="session", autouse=True)
def _configure_test_settings() -> None:
    """Tests need a real RS256 keypair to exercise `core.security`; generate
    an ephemeral one instead of committing a fixed key pair to the repo.

    Also switches the rate limiter to in-process memory storage: it defaults
    to Redis so limits are shared across instances in real deployments, but
    the test suite shouldn't require a live Redis just to make requests
    against the app. This must run before `arutech_api.main` is first
    imported, since the Limiter reads this at import time.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings.JWT_PRIVATE_KEY = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    settings.JWT_PUBLIC_KEY = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    settings.RATE_LIMIT_STORAGE_URI = "memory://"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """An isolated in-memory SQLite database per test, so repository/service
    tests don't require a running Postgres instance."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client wired to the app with the real DB dependency swapped
    for the isolated per-test SQLite session."""
    from arutech_api.core.database import get_db
    from arutech_api.main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
