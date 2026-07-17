import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio

_GOOD_TEMPLATE = {
    "code": "loan.approved",
    "channel": "email",
    "subject": "Your loan has been approved",
    "body": "Hi {{customer_name}}, your {{loan_product}} application has been approved.",
}


class TestNotificationTemplateAccess:
    async def test_employee_cannot_read_templates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="notif-emp@example.com")
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/notification-templates", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestNotificationTemplateCrud:
    async def test_create_list_update_and_deactivate(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="notif-admin1@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/notification-templates", json=_GOOD_TEMPLATE, headers=headers
        )
        assert create_response.status_code == 200
        template = create_response.json()
        assert template["channel"] == "email"

        list_response = await client.get(
            "/api/v1/notification-templates",
            params={"channel": "email"},
            headers=headers,
        )
        assert any(t["code"] == "loan.approved" for t in list_response.json())

        update_response = await client.put(
            f"/api/v1/notification-templates/{template['id']}",
            json={"subject": "Great news!", "body": "Updated body {{customer_name}}"},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["subject"] == "Great news!"

        deactivate_response = await client.post(
            f"/api/v1/notification-templates/{template['id']}/deactivate", headers=headers
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False

    async def test_sms_template_has_no_subject(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="notif-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/notification-templates",
            json={"code": "otp.login", "channel": "sms", "body": "Your code is {{code}}"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["subject"] is None

    async def test_duplicate_code_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="notif-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post("/api/v1/notification-templates", json=_GOOD_TEMPLATE, headers=headers)
        response = await client.post(
            "/api/v1/notification-templates", json=_GOOD_TEMPLATE, headers=headers
        )
        assert response.status_code == 409
