from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.security import hash_password
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.infrastructure.database.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)
from arutech_api.infrastructure.database.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from tests.integration.test_auth_flows import _PASSWORD, _make_admin, _register

pytestmark = pytest.mark.asyncio


async def _make_employee(
    db_session: AsyncSession, email: str = "employee@example.com"
) -> UserEntity:
    user_repo = SqlAlchemyUserRepository(db_session)
    rbac_repo = SqlAlchemyRbacRepository(db_session)

    user = await user_repo.create(
        UserEntity(
            email=email,
            hashed_password=hash_password(_PASSWORD),
            full_name="Employee User",
            role=UserRole.EMPLOYEE,
        )
    )
    role = await rbac_repo.get_role_by_name("employee")
    assert role is not None
    await rbac_repo.assign_role_to_user(user.id, role.id)
    await db_session.commit()
    return user


async def _login(client: AsyncClient, email: str, password: str = _PASSWORD) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token: str = response.json()["access_token"]
    return token


async def _submit_contact(
    client: AsyncClient,
    *,
    email: str = "lead@example.com",
    phone: str | None = "9876543210",
    subject: str = "Home loan enquiry",
    message: str = "I'd like to know more about your home loan interest rates and eligibility.",
    website: str = "",
) -> None:
    payload: dict[str, Any] = {
        "name": "Priya Sharma",
        "email": email,
        "subject": subject,
        "message": message,
        "website": website,
    }
    if phone is not None:
        payload["phone"] = phone
    response = await client.post("/api/v1/public/contact", json=payload)
    assert response.status_code == 200, response.text


class TestLeadCreationFromContactForm:
    async def test_submitting_the_contact_form_creates_a_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="ada@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/leads", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        leads = response.json()
        assert len(leads) == 1
        assert leads[0]["email"] == "ada@example.com"
        assert leads[0]["status"] == "new"
        assert leads[0]["score"] > 0

    async def test_honeypot_submission_does_not_create_a_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="bot@example.com", website="https://spam.example")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/leads", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json() == []


class TestLeadAccessControl:
    async def test_customer_cannot_read_leads(self, client: AsyncClient) -> None:
        await _register(client)
        token = await _login(client, "ada@example.com")

        response = await client.get(
            "/api/v1/leads", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    async def test_employee_can_read_and_manage_leads(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        employee = await _make_employee(db_session)
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/leads", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_unauthenticated_request_is_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/leads")
        assert response.status_code == 401


class TestLeadStatusTransitions:
    async def test_valid_pipeline_progression(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        for status in ("contacted", "qualified", "converted"):
            response = await client.post(
                f"/api/v1/leads/{lead_id}/status", json={"status": status}, headers=headers
            )
            assert response.status_code == 200, response.text
            assert response.json()["status"] == status

    async def test_skipping_a_pipeline_stage_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/status", json={"status": "converted"}, headers=headers
        )
        assert response.status_code == 409

    async def test_transitioning_out_of_a_terminal_status_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]
        await client.post(
            f"/api/v1/leads/{lead_id}/status", json={"status": "disqualified"}, headers=headers
        )

        response = await client.post(
            f"/api/v1/leads/{lead_id}/status", json={"status": "contacted"}, headers=headers
        )
        assert response.status_code == 409

    async def test_updating_an_unknown_lead_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            "/api/v1/leads/00000000-0000-0000-0000-000000000000/status",
            json={"status": "contacted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestLeadAssignment:
    async def test_assign_lead_to_an_employee(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        employee = await _make_employee(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/assign",
            json={"assignee_id": str(employee.id)},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["assigned_to"] == str(employee.id)

    async def test_cannot_assign_a_lead_to_a_customer(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        customer_body = await _register(client, email="customer@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/assign",
            json={"assignee_id": customer_body["id"]},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_assigning_to_an_unknown_user_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/assign",
            json={"assignee_id": "00000000-0000-0000-0000-000000000000"},
            headers=headers,
        )
        assert response.status_code == 404
