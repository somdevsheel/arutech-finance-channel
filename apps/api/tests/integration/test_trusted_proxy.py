"""Phase 4 wires the customer-portal BFF (apps/web) to call this API
server-to-server, so `request.client` stops being the real end user and
becomes the web app's own address. ProxyHeadersMiddleware (main.py) is
what recovers the real client IP from X-Forwarded-For — but only when the
immediate peer is in TRUSTED_PROXY_IPS. These tests exercise that trust
boundary end-to-end via the audit log, which is where a wrong client IP
would silently corrupt Phase 2's audit trail (and, via get_remote_address,
the per-route rate limits) rather than fail loudly.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import CapturingOtpDelivery
from tests.integration.test_auth_flows import _PASSWORD, _make_admin

pytestmark = pytest.mark.asyncio


async def _client_with_peer(
    db_session: AsyncSession, otp_delivery: CapturingOtpDelivery, peer: str
) -> AsyncClient:
    from arutech_api.api.deps import get_otp_delivery_channel
    from arutech_api.core.database import get_db
    from arutech_api.main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_otp_delivery_channel] = lambda: otp_delivery
    transport = ASGITransport(app=app, client=(peer, 123))
    return AsyncClient(transport=transport, base_url="http://test")


async def _registered_ip(client: AsyncClient, db_session: AsyncSession) -> str | None:
    await _make_admin(db_session)
    login = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": _PASSWORD}
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    entries = [e for e in response.json() if e["action"] == "user.registered"]
    assert entries, "expected a user.registered audit entry"
    result: str | None = entries[0]["extra_metadata"]["ip_address"]
    return result


class TestTrustedProxyHeaders:
    async def test_forwarded_ip_is_trusted_from_a_trusted_peer(
        self, db_session: AsyncSession, otp_delivery: CapturingOtpDelivery
    ) -> None:
        # 127.0.0.1 matches the default TRUSTED_PROXY_IPS.
        async with await _client_with_peer(db_session, otp_delivery, "127.0.0.1") as client:
            register = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "ada@example.com",
                    "password": _PASSWORD,
                    "full_name": "Ada Lovelace",
                },
                headers={"X-Forwarded-For": "203.0.113.5"},
            )
            assert register.status_code == 201

            ip = await _registered_ip(client, db_session)
            assert ip == "203.0.113.5"

    async def test_forwarded_ip_is_ignored_from_an_untrusted_peer(
        self, db_session: AsyncSession, otp_delivery: CapturingOtpDelivery
    ) -> None:
        # Not in TRUSTED_PROXY_IPS: the header must be ignored, or any
        # internet-facing caller could spoof its way past IP-based rate
        # limits and falsify the audit trail's ip_address field.
        async with await _client_with_peer(db_session, otp_delivery, "198.51.100.9") as client:
            register = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "ada@example.com",
                    "password": _PASSWORD,
                    "full_name": "Ada Lovelace",
                },
                headers={"X-Forwarded-For": "203.0.113.5"},
            )
            assert register.status_code == 201

            ip = await _registered_ip(client, db_session)
            assert ip == "198.51.100.9"
