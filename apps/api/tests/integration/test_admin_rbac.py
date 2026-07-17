import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _PASSWORD, _make_admin, _register
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio


class TestUserManagementAccess:
    async def test_employee_can_list_users_but_not_manage_them(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="ro-employee@example.com")
        token = await _login(client, employee.email)

        list_response = await client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200

        manage_response = await client.post(
            f"/api/v1/admin/users/{employee.id}/deactivate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert manage_response.status_code == 403

    async def test_customer_cannot_list_users(self, client: AsyncClient) -> None:
        await _register(client, email="cust-rbac@example.com")
        token = await _login(client, "cust-rbac@example.com")

        response = await client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestUserManagement:
    async def test_list_users_filters_by_role_and_active(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="filt-cust@example.com")
        employee = await _make_employee(db_session, email="filt-emp@example.com")
        admin = await _make_admin(db_session, email="filt-admin@example.com")
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/users",
            params={"role": "employee"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        emails = {u["email"] for u in response.json()}
        assert employee.email in emails
        assert "filt-cust@example.com" not in emails

    async def test_deactivate_then_activate_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="toggle-cust@example.com")
        admin = await _make_admin(db_session, email="toggle-admin@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        deactivate_response = await client.post(
            f"/api/v1/admin/users/{customer['id']}/deactivate", headers=headers
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "toggle-cust@example.com", "password": _PASSWORD},
        )
        assert login_response.status_code == 401

        activate_response = await client.post(
            f"/api/v1/admin/users/{customer['id']}/activate", headers=headers
        )
        assert activate_response.status_code == 200
        assert activate_response.json()["is_active"] is True

    async def test_set_role_syncs_rbac_binding(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="promote-cust@example.com")
        admin = await _make_admin(db_session, email="promote-admin@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/admin/users/{customer['id']}/role",
            json={"role": "employee"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["role"] == "employee"

        # The promoted user should now be able to log in and immediately
        # exercise an employee-only permission (leads.read), proving the
        # RBAC binding was actually synced, not just the coarse column.
        promoted_token = await _login(client, "promote-cust@example.com")
        leads_response = await client.get(
            "/api/v1/leads", headers={"Authorization": f"Bearer {promoted_token}"}
        )
        assert leads_response.status_code == 200


class TestRoleManagement:
    async def test_create_and_delete_custom_role(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin1@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/admin/roles",
            json={"name": "auditor", "description": "Read-only compliance access"},
            headers=headers,
        )
        assert create_response.status_code == 200
        role = create_response.json()
        assert role["is_system"] is False

        delete_response = await client.delete(
            f"/api/v1/admin/roles/{role['id']}", headers=headers
        )
        assert delete_response.status_code == 204

    async def test_cannot_delete_a_system_role(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        roles = (
            await client.get("/api/v1/admin/roles", headers=headers)
        ).json()
        employee_role = next(r for r in roles if r["name"] == "employee")

        response = await client.delete(
            f"/api/v1/admin/roles/{employee_role['id']}", headers=headers
        )
        assert response.status_code == 409

    async def test_duplicate_role_name_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            "/api/v1/admin/roles", json={"name": "reviewer"}, headers=headers
        )
        response = await client.post(
            "/api/v1/admin/roles", json={"name": "reviewer"}, headers=headers
        )
        assert response.status_code == 409

    async def test_grant_and_revoke_permission_on_a_custom_role(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin4@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        role = (
            await client.post(
                "/api/v1/admin/roles", json={"name": "grant-test"}, headers=headers
            )
        ).json()

        grant_response = await client.post(
            f"/api/v1/admin/roles/{role['id']}/permissions",
            json={"permission_code": "leads.read"},
            headers=headers,
        )
        assert grant_response.status_code == 204

        permissions = (
            await client.get(
                f"/api/v1/admin/roles/{role['id']}/permissions", headers=headers
            )
        ).json()
        assert any(p["code"] == "leads.read" for p in permissions)

        revoke_response = await client.delete(
            f"/api/v1/admin/roles/{role['id']}/permissions/leads.read", headers=headers
        )
        assert revoke_response.status_code == 204

        permissions_after = (
            await client.get(
                f"/api/v1/admin/roles/{role['id']}/permissions", headers=headers
            )
        ).json()
        assert not any(p["code"] == "leads.read" for p in permissions_after)

    async def test_granting_an_unknown_permission_code_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin5@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        role = (
            await client.post(
                "/api/v1/admin/roles", json={"name": "unknown-perm-test"}, headers=headers
            )
        ).json()

        response = await client.post(
            f"/api/v1/admin/roles/{role['id']}/permissions",
            json={"permission_code": "not.a.real.permission"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_assign_and_remove_role_from_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="assign-cust@example.com")
        admin = await _make_admin(db_session, email="role-admin6@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        role = (
            await client.post(
                "/api/v1/admin/roles", json={"name": "extra-role"}, headers=headers
            )
        ).json()

        assign_response = await client.post(
            f"/api/v1/admin/roles/{role['id']}/users/{customer['id']}", headers=headers
        )
        assert assign_response.status_code == 204

        remove_response = await client.delete(
            f"/api/v1/admin/roles/{role['id']}/users/{customer['id']}", headers=headers
        )
        assert remove_response.status_code == 204

    async def test_assigning_a_role_to_an_unknown_user_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="role-admin7@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        role = (
            await client.post(
                "/api/v1/admin/roles", json={"name": "unknown-user-test"}, headers=headers
            )
        ).json()

        response = await client.post(
            f"/api/v1/admin/roles/{role['id']}/users/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_list_permissions(self, client: AsyncClient, db_session: AsyncSession) -> None:
        admin = await _make_admin(db_session, email="role-admin8@example.com")
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/permissions", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        codes = {p["code"] for p in response.json()}
        assert "loans.read" in codes
        assert "dashboard.read" in codes
