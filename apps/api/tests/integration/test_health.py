import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_liveness_reports_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert "version" in body


async def test_readiness_is_ok_when_dependencies_are_reachable(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arutech_api.api.v1.endpoints.health.check_database_connection",
        _async_true,
    )
    monkeypatch.setattr("arutech_api.api.v1.endpoints.health.check_redis_connection", _async_true)

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"database": "ok", "redis": "ok"}


async def test_readiness_is_503_when_a_dependency_is_unreachable(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arutech_api.api.v1.endpoints.health.check_database_connection",
        _async_true,
    )
    monkeypatch.setattr("arutech_api.api.v1.endpoints.health.check_redis_connection", _async_false)

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["checks"] == {"database": "ok", "redis": "error"}


async def _async_true() -> bool:
    return True


async def _async_false() -> bool:
    return False
