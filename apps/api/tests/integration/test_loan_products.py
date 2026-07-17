from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin, _register
from tests.integration.test_leads import _login, _make_employee
from tests.integration.test_loans import _create_application

pytestmark = pytest.mark.asyncio

_GOOD_PRODUCT: dict[str, Any] = {
    "slug": "top-up-loan",
    "name": "Top-Up Loan",
    "interest_rate_min": "11",
    "interest_rate_max": "18",
    "tenure_min_months": 12,
    "tenure_max_months": 60,
    "amount_min": 50_000,
    "amount_max": 1_000_000,
    "documents_required": ["PAN card", "Existing loan statement"],
}


class TestLoanProductAccess:
    async def test_employee_cannot_read_loan_products(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="lp-emp@example.com")
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/loan-products", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestLoanProductCrud:
    async def test_list_products_includes_the_seeded_catalog(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lp-admin1@example.com")
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/loan-products", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        slugs = {p["slug"] for p in response.json()}
        assert "personal-loan" in slugs
        assert "gold-loan" in slugs

    async def test_create_update_and_deactivate_product(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lp-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/loan-products", json=_GOOD_PRODUCT, headers=headers
        )
        assert create_response.status_code == 200
        product = create_response.json()
        assert product["documents_required"] == _GOOD_PRODUCT["documents_required"]

        update_payload = {**_GOOD_PRODUCT, "name": "Top-Up Loan v2", "amount_max": 1_500_000}
        del update_payload["slug"]
        update_response = await client.put(
            f"/api/v1/loan-products/{product['id']}", json=update_payload, headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Top-Up Loan v2"
        assert update_response.json()["amount_max"] == 1_500_000

        deactivate_response = await client.post(
            f"/api/v1/loan-products/{product['id']}/deactivate", headers=headers
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False

    async def test_duplicate_slug_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lp-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/loan-products",
            json={**_GOOD_PRODUCT, "slug": "personal-loan"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_inverted_bounds_are_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lp-admin4@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/loan-products",
            json={**_GOOD_PRODUCT, "slug": "bad-bounds", "amount_min": 100, "amount_max": 50},
            headers=headers,
        )
        assert response.status_code == 409


class TestLoanApplicationUsesDbBackedProduct:
    async def test_application_creation_validates_against_a_custom_product(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="lp-admin5@example.com")
        admin_token = await _login(client, admin.email)
        await client.post(
            "/api/v1/loan-products",
            json=_GOOD_PRODUCT,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        await _register(client, email="lp-applicant@example.com")
        applicant_token = await _login(client, "lp-applicant@example.com")

        application = await _create_application(
            client,
            applicant_token,
            loan_product_slug="top-up-loan",
            requested_amount=200_000,
            tenure_months=24,
            interest_rate=12,
        )
        assert application["loan_product_slug"] == "top-up-loan"

    async def test_application_rejects_an_unknown_product_slug(
        self, client: AsyncClient
    ) -> None:
        await _register(client, email="lp-applicant2@example.com")
        token = await _login(client, "lp-applicant2@example.com")

        response = await client.post(
            "/api/v1/loan-applications",
            json={
                "loan_product_slug": "does-not-exist",
                "requested_amount": 100_000,
                "tenure_months": 12,
                "monthly_income": 50_000,
                "interest_rate": 10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
