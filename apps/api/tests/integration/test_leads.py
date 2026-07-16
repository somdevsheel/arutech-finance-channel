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
    db_session: AsyncSession, email: str = "employee@example.com", *, active: bool = True
) -> UserEntity:
    user_repo = SqlAlchemyUserRepository(db_session)
    rbac_repo = SqlAlchemyRbacRepository(db_session)

    user = await user_repo.create(
        UserEntity(
            email=email,
            hashed_password=hash_password(_PASSWORD),
            full_name="Employee User",
            role=UserRole.EMPLOYEE,
            is_active=active,
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


class TestLeadAutoAssignment:
    async def test_lead_is_auto_assigned_when_one_employee_exists(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        leads = (
            await client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        ).json()
        assert leads[0]["assigned_to"] == str(employee.id)

    async def test_lead_is_unassigned_when_no_active_employees_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        leads = (
            await client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        ).json()
        assert leads[0]["assigned_to"] is None

    async def test_inactive_employees_are_not_assignment_candidates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _make_employee(db_session, "inactive@example.com", active=False)
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        leads = (
            await client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        ).json()
        assert leads[0]["assigned_to"] is None

    async def test_new_leads_go_to_the_least_loaded_employee(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee_a = await _make_employee(db_session, "a@example.com")
        employee_b = await _make_employee(db_session, "b@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await _submit_contact(client, email="one@example.com", phone="1000000001")
        await _submit_contact(client, email="two@example.com", phone="1000000002")
        await _submit_contact(client, email="three@example.com", phone="1000000003")

        leads = (await client.get("/api/v1/leads", headers=headers)).json()
        assignees = {lead["email"]: lead["assigned_to"] for lead in leads}

        # Lead 1: both at 0 -> earliest-created (A) wins the tie.
        assert assignees["one@example.com"] == str(employee_a.id)
        # Lead 2: A now has 1 open lead, B has 0 -> goes to B.
        assert assignees["two@example.com"] == str(employee_b.id)
        # Lead 3: tied at 1 each -> A wins the tie again.
        assert assignees["three@example.com"] == str(employee_a.id)


class TestLeadDuplicateDetection:
    async def test_resubmission_from_the_same_email_does_not_create_a_second_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="dup@example.com", phone="1111111111")
        await _submit_contact(client, email="dup@example.com", phone="1111111111")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        leads = (
            await client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        ).json()
        assert len(leads) == 1

    async def test_resubmission_bumps_the_existing_leads_score(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(
            client, email="dup2@example.com", phone=None, subject="Hi", message="short"
        )
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}
        first_score = (await client.get("/api/v1/leads", headers=headers)).json()[0]["score"]

        await _submit_contact(
            client, email="dup2@example.com", phone=None, subject="Hi", message="short"
        )
        second_score = (await client.get("/api/v1/leads", headers=headers)).json()[0]["score"]

        assert second_score > first_score

    async def test_same_phone_different_email_is_still_a_duplicate(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="alice@example.com", phone="2222222222")
        await _submit_contact(client, email="alice-alt@example.com", phone="2222222222")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        leads = (
            await client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        ).json()
        assert len(leads) == 1

    async def test_resubmission_after_conversion_creates_a_fresh_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="repeat@example.com", phone="3333333333")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]
        for status in ("contacted", "qualified", "converted"):
            await client.post(
                f"/api/v1/leads/{lead_id}/status", json={"status": status}, headers=headers
            )

        await _submit_contact(client, email="repeat@example.com", phone="3333333333")

        leads = (await client.get("/api/v1/leads", headers=headers)).json()
        assert len(leads) == 2


class TestLeadImportExport:
    async def test_import_creates_manual_leads(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/leads/import",
            json={
                "leads": [
                    {"name": "Bulk One", "email": "bulk1@example.com", "phone": "4444444444"},
                    {"name": "Bulk Two", "email": "bulk2@example.com"},
                ]
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        created = response.json()
        assert len(created) == 2
        assert all(lead["source"] == "manual" for lead in created)
        assert all(lead["contact_submission_id"] is None for lead in created)

    async def test_import_deduplicates_against_active_leads(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="existing@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            "/api/v1/leads/import",
            json={"leads": [{"name": "Existing Person", "email": "existing@example.com"}]},
            headers=headers,
        )

        leads = (await client.get("/api/v1/leads", headers=headers)).json()
        assert len(leads) == 1

    async def test_import_requires_manage_permission(self, client: AsyncClient) -> None:
        await _register(client)
        token = await _login(client, "ada@example.com")

        response = await client.post(
            "/api/v1/leads/import",
            json={"leads": [{"name": "X", "email": "x@example.com"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_export_returns_csv(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="csv@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/leads/export", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "csv@example.com" in response.text
        assert response.text.startswith("id,name,email,phone,source,status,score")


class TestLeadAnalytics:
    async def test_summary_reflects_pipeline_state(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="one@example.com", phone="1000000001")
        await _submit_contact(client, email="two@example.com", phone="1000000002")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]
        for status in ("contacted", "qualified", "converted"):
            await client.post(
                f"/api/v1/leads/{lead_id}/status", json={"status": status}, headers=headers
            )

        response = await client.get("/api/v1/leads/analytics/summary", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total_leads"] == 2
        assert body["by_status"]["converted"] == 1
        assert body["by_status"]["new"] == 1
        assert body["by_source"]["contact_form"] == 2
        assert body["conversion_rate"] == 0.5


class TestLeadActivity:
    async def test_activity_includes_creation_and_status_change(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]
        await client.post(
            f"/api/v1/leads/{lead_id}/status", json={"status": "contacted"}, headers=headers
        )

        response = await client.get(f"/api/v1/leads/{lead_id}/activity", headers=headers)
        assert response.status_code == 200
        actions = [entry["action"] for entry in response.json()]
        assert "lead.created" in actions
        assert "lead.status_changed" in actions

    async def test_activity_for_unknown_lead_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/leads/00000000-0000-0000-0000-000000000000/activity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestLeadTasks:
    async def test_create_and_list_task_for_a_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/tasks",
            json={
                "title": "Call back",
                "due_at": "2026-08-01T10:00:00Z",
                "assigned_to": str(employee.id),
                "notes": "Prefers evenings",
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "pending"

        listed = await client.get(f"/api/v1/leads/{lead_id}/tasks", headers=headers)
        assert len(listed.json()) == 1

    async def test_task_appears_in_assignees_mine_list(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        admin_token = await _login(client, admin.email)

        lead_id = (
            await client.get(
                "/api/v1/leads", headers={"Authorization": f"Bearer {admin_token}"}
            )
        ).json()[0]["id"]
        await client.post(
            f"/api/v1/leads/{lead_id}/tasks",
            json={
                "title": "Follow up",
                "due_at": "2026-08-01T10:00:00Z",
                "assigned_to": str(employee.id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        employee_token = await _login(client, employee.email)
        response = await client.get(
            "/api/v1/leads/tasks/mine", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_complete_task(self, client: AsyncClient, db_session: AsyncSession) -> None:
        employee = await _make_employee(db_session)
        await _submit_contact(client)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]
        task = (
            await client.post(
                f"/api/v1/leads/{lead_id}/tasks",
                json={
                    "title": "Call back",
                    "due_at": "2026-08-01T10:00:00Z",
                    "assigned_to": str(employee.id),
                },
                headers=headers,
            )
        ).json()

        response = await client.post(
            f"/api/v1/leads/tasks/{task['id']}/complete", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "done"
        assert response.json()["completed_at"] is not None

    async def test_cannot_assign_a_task_to_a_customer(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client)
        customer_body = await _register(client, email="customer2@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        lead_id = (await client.get("/api/v1/leads", headers=headers)).json()[0]["id"]

        response = await client.post(
            f"/api/v1/leads/{lead_id}/tasks",
            json={
                "title": "Call back",
                "due_at": "2026-08-01T10:00:00Z",
                "assigned_to": customer_body["id"],
            },
            headers=headers,
        )
        assert response.status_code == 409

    async def test_cannot_create_a_task_for_an_unknown_lead(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            "/api/v1/leads/00000000-0000-0000-0000-000000000000/tasks",
            json={
                "title": "Call back",
                "due_at": "2026-08-01T10:00:00Z",
                "assigned_to": str(employee.id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
