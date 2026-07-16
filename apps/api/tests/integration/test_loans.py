from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin, _register
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio

_GOOD_APPLICATION: dict[str, Any] = {
    "loan_product_slug": "personal-loan",
    "requested_amount": 200_000,
    "tenure_months": 24,
    "monthly_income": 100_000,
    "interest_rate": 12,
}


async def _create_application(
    client: AsyncClient, token: str, **overrides: Any
) -> dict[str, Any]:
    payload = {**_GOOD_APPLICATION, **overrides}
    response = await client.post(
        "/api/v1/loan-applications",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


async def _submit(client: AsyncClient, token: str, application_id: str) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/loan-applications/mine/{application_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


async def _move_to_approved(
    client: AsyncClient, *, application_id: str, admin_token: str, employee_id: str
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        f"/api/v1/loan-applications/{application_id}/assign",
        json={"assignee_id": employee_id},
        headers=headers,
    )
    await client.post(
        f"/api/v1/loan-applications/{application_id}/kyc",
        json={"status": "verified"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/loan-applications/{application_id}/verification",
        json={"status": "verified"},
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/loan-applications/{application_id}/approve", headers=headers
    )
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


class TestApplicationCreation:
    async def test_create_draft_application(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="applicant1@example.com")
        login_token = await _login(client, "applicant1@example.com")

        body = await _create_application(client, login_token)
        assert body["status"] == "draft"
        assert body["eligibility_status"] == "pending"
        assert body["customer_user_id"] == customer["id"]

    async def test_amount_outside_product_bounds_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant2@example.com")
        token = await _login(client, "applicant2@example.com")

        response = await client.post(
            "/api/v1/loan-applications",
            json={**_GOOD_APPLICATION, "requested_amount": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_unknown_product_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant3@example.com")
        token = await _login(client, "applicant3@example.com")

        response = await client.post(
            "/api/v1/loan-applications",
            json={**_GOOD_APPLICATION, "loan_product_slug": "not-a-real-product"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_employee_cannot_create_an_application_for_themselves(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        token = await _login(client, employee.email)

        response = await client.post(
            "/api/v1/loan-applications",
            json=_GOOD_APPLICATION,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestOwnership:
    async def test_cannot_view_another_customers_application(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="owner@example.com")
        owner_token = await _login(client, "owner@example.com")
        application = await _create_application(client, owner_token)

        await _register(client, email="intruder@example.com")
        intruder_token = await _login(client, "intruder@example.com")

        response = await client.get(
            f"/api/v1/loan-applications/mine/{application['id']}",
            headers={"Authorization": f"Bearer {intruder_token}"},
        )
        assert response.status_code == 404

    async def test_unauthenticated_staff_list_is_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/loan-applications")
        assert response.status_code == 401

    async def test_customer_cannot_use_staff_routes(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant4@example.com")
        token = await _login(client, "applicant4@example.com")

        response = await client.get(
            "/api/v1/loan-applications", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestSubmission:
    async def test_submit_computes_eligibility_and_credit_and_seeds_documents(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant5@example.com")
        token = await _login(client, "applicant5@example.com")
        application = await _create_application(client, token)

        submitted = await _submit(client, token, application["id"])
        assert submitted["status"] == "submitted"
        assert submitted["eligibility_status"] == "eligible"
        assert submitted["credit_score"] is not None
        assert submitted["risk_category"] == "low"

        documents = await client.get(
            f"/api/v1/loan-applications/mine/{application['id']}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert documents.status_code == 200
        # personal-loan lists 4 required documents in domain/loans/products.py
        assert len(documents.json()) == 4
        assert all(doc["status"] == "pending" for doc in documents.json())

    async def test_ineligible_income_still_submits_but_is_flagged(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant6@example.com")
        token = await _login(client, "applicant6@example.com")
        application = await _create_application(
            client, token, requested_amount=3_000_000, monthly_income=30_000, tenure_months=60
        )

        submitted = await _submit(client, token, application["id"])
        assert submitted["eligibility_status"] == "ineligible"

    async def test_cannot_submit_twice(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant7@example.com")
        token = await _login(client, "applicant7@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        response = await client.post(
            f"/api/v1/loan-applications/mine/{application['id']}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409


class TestWithdraw:
    async def test_withdraw_a_draft(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _register(client, email="applicant8@example.com")
        token = await _login(client, "applicant8@example.com")
        application = await _create_application(client, token)

        response = await client.post(
            f"/api/v1/loan-applications/mine/{application['id']}/withdraw",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "withdrawn"

    async def test_cannot_withdraw_after_approval(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant9@example.com")
        token = await _login(client, "applicant9@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)
        await _move_to_approved(
            client,
            application_id=application["id"],
            admin_token=admin_token,
            employee_id=str(employee.id),
        )

        response = await client.post(
            f"/api/v1/loan-applications/mine/{application['id']}/withdraw",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409


class TestStaffPipeline:
    async def test_assigning_a_submitted_application_starts_review(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant10@example.com")
        token = await _login(client, "applicant10@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/loan-applications/{application['id']}/assign",
            json={"assignee_id": str(employee.id)},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "under_review"
        assert response.json()["assigned_to"] == str(employee.id)

    async def test_cannot_approve_before_kyc_and_verification(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant11@example.com")
        token = await _login(client, "applicant11@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/loan-applications/{application['id']}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    async def test_full_pipeline_to_closure(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant12@example.com")
        token = await _login(client, "applicant12@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {admin_token}"}

        approved = await _move_to_approved(
            client,
            application_id=application["id"],
            admin_token=admin_token,
            employee_id=str(employee.id),
        )
        assert approved["status"] == "approved"

        sanction = await client.post(
            f"/api/v1/loan-applications/{application['id']}/sanction",
            json={"sanctioned_amount": 180_000, "sanctioned_tenure_months": 24},
            headers=headers,
        )
        assert sanction.status_code == 200, sanction.text
        assert sanction.json()["status"] == "sanctioned"

        disburse = await client.post(
            f"/api/v1/loan-applications/{application['id']}/disburse",
            json={"disbursement_reference": "UTR123456"},
            headers=headers,
        )
        assert disburse.status_code == 200, disburse.text
        body = disburse.json()
        assert body["status"] == "disbursed"
        assert body["disbursed_amount"] == 180_000
        assert body["commission_amount"] == 1_800  # 1% of 180,000
        assert body["commission_status"] == "pending"

        commission = await client.post(
            f"/api/v1/loan-applications/{application['id']}/commission",
            json={"status": "paid"},
            headers=headers,
        )
        assert commission.status_code == 200
        assert commission.json()["commission_status"] == "paid"

        close = await client.post(
            f"/api/v1/loan-applications/{application['id']}/close",
            json={"closure_reason": "Loan fully repaid"},
            headers=headers,
        )
        assert close.status_code == 200
        assert close.json()["status"] == "closed"

    async def test_sanctioned_amount_cannot_exceed_requested(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant13@example.com")
        token = await _login(client, "applicant13@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)
        await _move_to_approved(
            client,
            application_id=application["id"],
            admin_token=admin_token,
            employee_id=str(employee.id),
        )

        response = await client.post(
            f"/api/v1/loan-applications/{application['id']}/sanction",
            json={"sanctioned_amount": 999_999_999, "sanctioned_tenure_months": 24},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    async def test_reject_with_reason(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant14@example.com")
        token = await _login(client, "applicant14@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {admin_token}"}
        await client.post(
            f"/api/v1/loan-applications/{application['id']}/assign",
            json={"assignee_id": str(admin.id)},
            headers=headers,
        )

        response = await client.post(
            f"/api/v1/loan-applications/{application['id']}/reject",
            json={"reason": "Insufficient documentation"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        assert response.json()["rejection_reason"] == "Insufficient documentation"


class TestDocuments:
    async def test_customer_submits_own_document_and_staff_reviews_it(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant15@example.com")
        token = await _login(client, "applicant15@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        documents = (
            await client.get(
                f"/api/v1/loan-applications/mine/{application['id']}/documents",
                headers={"Authorization": f"Bearer {token}"},
            )
        ).json()
        document_id = documents[0]["id"]

        submit_response = await client.post(
            f"/api/v1/loan-applications/mine/{application['id']}/documents/{document_id}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "submitted"

        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)
        review_response = await client.post(
            f"/api/v1/loan-applications/{application['id']}/documents/{document_id}/review",
            json={"status": "verified", "notes": "Looks good"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert review_response.status_code == 200
        assert review_response.json()["status"] == "verified"
        assert review_response.json()["notes"] == "Looks good"


class TestAnalytics:
    async def test_summary_reflects_pipeline_state(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="applicant16@example.com")
        token = await _login(client, "applicant16@example.com")
        application = await _create_application(client, token)
        await _submit(client, token, application["id"])

        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/loan-applications/analytics/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_applications"] == 1
        assert body["by_status"]["submitted"] == 1
        assert body["by_product"]["personal-loan"] == 1
