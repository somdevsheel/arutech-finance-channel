import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin
from tests.integration.test_leads import _login, _make_employee, _submit_contact

pytestmark = pytest.mark.asyncio


class TestSettingsAccess:
    async def test_employee_cannot_read_settings(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="settings-emp@example.com")
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/admin/settings", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestSettingsCrud:
    async def test_list_and_get_seeded_setting(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="settings-admin1@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        list_response = await client.get("/api/v1/admin/settings", headers=headers)
        assert list_response.status_code == 200
        keys = {s["key"] for s in list_response.json()}
        assert "leads.auto_assignment_enabled" in keys

        get_response = await client.get(
            "/api/v1/admin/settings/leads.auto_assignment_enabled", headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["value"] == "true"

    async def test_update_setting(self, client: AsyncClient, db_session: AsyncSession) -> None:
        admin = await _make_admin(db_session, email="settings-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put(
            "/api/v1/admin/settings/leads.auto_assignment_enabled",
            json={"value": "false"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["value"] == "false"

    async def test_invalid_boolean_value_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="settings-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put(
            "/api/v1/admin/settings/leads.auto_assignment_enabled",
            json={"value": "maybe"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_unknown_setting_key_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="settings-admin4@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            "/api/v1/admin/settings/not.a.real.setting", headers=headers
        )
        assert response.status_code == 404


class TestAutoAssignmentToggle:
    async def test_disabling_auto_assignment_leaves_new_leads_unassigned(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _make_employee(db_session, email="toggle-employee@example.com")
        admin = await _make_admin(db_session, email="settings-admin5@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.put(
            "/api/v1/admin/settings/leads.auto_assignment_enabled",
            json={"value": "false"},
            headers=headers,
        )

        await _submit_contact(client, email="toggle-lead@example.com", phone="9000000099")

        leads = (await client.get("/api/v1/leads", headers=headers)).json()
        lead = next(lead for lead in leads if lead["email"] == "toggle-lead@example.com")
        assert lead["assigned_to"] is None
