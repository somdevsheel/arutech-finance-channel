import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio

_GOOD_LENDER = {
    "name": "HDFC Bank",
    "type": "bank",
    "code": "HDFC",
    "contact_email": "dsa-desk@hdfcbank.example",
    "commission_rate_percent": "1.5",
}


class TestLenderAccess:
    async def test_employee_cannot_read_lenders(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="lender-emp@example.com")
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/lenders", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestLenderCrud:
    async def test_create_list_update_and_deactivate_lender(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lender-admin1@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/lenders", json=_GOOD_LENDER, headers=headers
        )
        assert create_response.status_code == 200
        lender = create_response.json()
        assert lender["type"] == "bank"
        assert lender["commission_rate_percent"] == "1.50"

        list_response = await client.get("/api/v1/lenders", headers=headers)
        assert any(row["id"] == lender["id"] for row in list_response.json())

        update_response = await client.put(
            f"/api/v1/lenders/{lender['id']}",
            json={
                "name": "HDFC Bank Ltd",
                "contact_email": "new-desk@hdfcbank.example",
                "contact_phone": None,
                "commission_rate_percent": "2",
            },
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "HDFC Bank Ltd"
        assert update_response.json()["commission_rate_percent"] == "2.00"

        deactivate_response = await client.post(
            f"/api/v1/lenders/{lender['id']}/deactivate", headers=headers
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False

    async def test_duplicate_lender_code_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lender-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post("/api/v1/lenders", json=_GOOD_LENDER, headers=headers)
        response = await client.post("/api/v1/lenders", json=_GOOD_LENDER, headers=headers)
        assert response.status_code == 409

    async def test_filter_lenders_by_type(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lender-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post("/api/v1/lenders", json=_GOOD_LENDER, headers=headers)
        await client.post(
            "/api/v1/lenders",
            json={**_GOOD_LENDER, "code": "BAJAJ-FIN", "name": "Bajaj Finance", "type": "nbfc"},
            headers=headers,
        )

        response = await client.get(
            "/api/v1/lenders", params={"type": "nbfc"}, headers=headers
        )
        codes = {row["code"] for row in response.json()}
        assert "BAJAJ-FIN" in codes
        assert "HDFC" not in codes
