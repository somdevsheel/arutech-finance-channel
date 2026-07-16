from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from arutech_api.core.config import settings
from arutech_api.infrastructure.database.base import Base
from arutech_api.infrastructure.database.models.rbac import Permission, Role
from arutech_api.infrastructure.database.seed_data import PERMISSIONS, ROLE_PERMISSIONS


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


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    """The limiter's in-memory storage is a process-wide singleton (see
    `core.rate_limit.limiter`), not something `db_session`-style
    per-test isolation resets on its own. Without this, hit counts from
    earlier tests carry over and later tests get spuriously 429'd —
    every test client request comes from the same "127.0.0.1", so a
    5-per-minute limit like /auth/register's is exhausted after five
    tests total, not five calls within any single test.
    """
    from arutech_api.core.rate_limit import limiter

    limiter.reset()


async def _seed_rbac(session: AsyncSession) -> None:
    """Mirrors the seed data the Phase 2 migration inserts into a real
    database (see `infrastructure.database.seed_data`), so tests exercise
    the same roles/permissions the app actually ships with."""
    permissions = {
        code: Permission(code=code, description=description) for code, description in PERMISSIONS
    }
    session.add_all(permissions.values())

    roles = {
        name: Role(
            name=name,
            description=f"Built-in {name} role",
            is_system=True,
            permissions=[permissions[code] for code in codes],
        )
        for name, codes in ROLE_PERMISSIONS.items()
    }
    session.add_all(roles.values())
    await session.commit()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """An isolated in-memory SQLite database per test, so repository/service
    tests don't require a running Postgres instance."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        await _seed_rbac(session)
        yield session

    await engine.dispose()


class CapturingOtpDelivery:
    """Test double standing in for `LoggingOtpDeliveryChannel`: captures the
    plaintext code the service generated instead of just logging it, since
    the DB only ever stores an HMAC hash of it. Lets tests complete an
    OTP-based flow without weakening how codes are actually stored."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, object]] = []

    async def send(self, destination: str, code: str, purpose: object) -> None:
        self.sent.append((destination, code, purpose))

    @property
    def last_code(self) -> str:
        return self.sent[-1][1]


@pytest_asyncio.fixture
async def otp_delivery() -> CapturingOtpDelivery:
    return CapturingOtpDelivery()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, otp_delivery: CapturingOtpDelivery
) -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client wired to the app with the real DB dependency swapped
    for the isolated per-test SQLite session, and OTP delivery swapped for
    a capturing test double."""
    from arutech_api.api.deps import get_otp_delivery_channel
    from arutech_api.core.database import get_db
    from arutech_api.main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_otp_delivery_channel] = lambda: otp_delivery
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
