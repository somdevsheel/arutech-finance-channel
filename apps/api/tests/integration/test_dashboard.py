import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin, _register
from tests.integration.test_leads import _login, _make_employee, _submit_contact
from tests.integration.test_loans import _create_application, _submit

pytestmark = pytest.mark.asyncio

_ENDPOINTS = [
    "/api/v1/admin/dashboard/kpis",
    "/api/v1/admin/dashboard/lead-funnel",
    "/api/v1/admin/dashboard/activity-heatmap",
    "/api/v1/admin/dashboard/alerts",
    "/api/v1/admin/dashboard/system-health",
]


class TestAccessControl:
    @pytest.mark.parametrize("path", _ENDPOINTS)
    async def test_unauthenticated_is_rejected(self, client: AsyncClient, path: str) -> None:
        response = await client.get(path)
        assert response.status_code == 401

    @pytest.mark.parametrize("path", _ENDPOINTS)
    async def test_customer_cannot_read_the_dashboard(
        self, client: AsyncClient, path: str
    ) -> None:
        await _register(client, email="customer-dash@example.com")
        token = await _login(client, "customer-dash@example.com")

        response = await client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    @pytest.mark.parametrize("path", _ENDPOINTS)
    async def test_employee_cannot_read_the_dashboard(
        self, client: AsyncClient, db_session: AsyncSession, path: str
    ) -> None:
        # dashboard.read is deliberately admin-only — see seed_data.py.
        employee = await _make_employee(db_session, email="employee-dash@example.com")
        token = await _login(client, employee.email)

        response = await client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    @pytest.mark.parametrize("path", _ENDPOINTS)
    async def test_admin_can_read_the_dashboard(
        self, client: AsyncClient, db_session: AsyncSession, path: str
    ) -> None:
        admin = await _make_admin(db_session, email="admin-dash@example.com")
        token = await _login(client, admin.email)

        response = await client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


class TestExecutiveKpis:
    async def test_kpis_reflect_leads_customers_and_loans(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="kpi-lead@example.com", phone="9000000001")

        await _register(client, email="kpi-customer@example.com")
        applicant_token = await _login(client, "kpi-customer@example.com")
        application = await _create_application(client, applicant_token)
        await _submit(client, applicant_token, application["id"])

        admin = await _make_admin(db_session, email="admin-kpi@example.com")
        admin_token = await _login(client, admin.email)
        # Lazily create a customer profile so customers_count picks it up.
        await client.get(
            f"/api/v1/customers/{application['customer_user_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = await client.get(
            "/api/v1/admin/dashboard/kpis", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["leads_total"] >= 1
        assert body["loans_total"] >= 1
        assert body["loans_pending_approval"] >= 1
        assert body["customers_count"] >= 1
        assert body["total_revenue"] == 0  # nothing disbursed yet
        assert body["total_commission"] == 0


class TestLeadFunnel:
    async def test_funnel_stages_are_in_pipeline_order(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="funnel-lead@example.com", phone="9000000002")

        admin = await _make_admin(db_session, email="admin-funnel@example.com")
        admin_token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/dashboard/lead-funnel",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert [stage["status"] for stage in body["stages"]] == [
            "new",
            "contacted",
            "qualified",
            "converted",
        ]
        new_stage = next(stage for stage in body["stages"] if stage["status"] == "new")
        assert new_stage["count"] >= 1


class TestActivityHeatmap:
    async def test_heatmap_is_a_dense_168_cell_grid(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _submit_contact(client, email="heatmap-lead@example.com", phone="9000000003")

        admin = await _make_admin(db_session, email="admin-heatmap@example.com")
        admin_token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/dashboard/activity-heatmap",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["cells"]) == 7 * 24
        assert sum(cell["lead_count"] for cell in body["cells"]) >= 1
        assert all(0 <= cell["day_of_week"] <= 6 for cell in body["cells"])
        assert all(0 <= cell["hour"] <= 23 for cell in body["cells"])


class TestAlerts:
    async def test_unassigned_customer_triggers_an_info_alert(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="alert-customer@example.com")

        admin = await _make_admin(db_session, email="admin-alerts@example.com")
        admin_token = await _login(client, admin.email)
        # Lazily create the profile (no relationship manager yet).
        await client.get(
            f"/api/v1/customers/{customer['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = await client.get(
            "/api/v1/admin/dashboard/alerts", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        codes = {alert["code"] for alert in response.json()}
        assert "customers_without_relationship_manager" in codes


class TestSystemHealth:
    async def test_system_health_ok_when_dependencies_are_reachable(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "arutech_api.services.dashboard_service.check_database_connection", _async_true
        )
        monkeypatch.setattr(
            "arutech_api.services.dashboard_service.check_redis_connection", _async_true
        )

        admin = await _make_admin(db_session, email="admin-health-ok@example.com")
        admin_token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/dashboard/system-health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database_ok"] is True
        assert body["redis_ok"] is True

    async def test_system_health_degraded_when_a_dependency_is_down(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "arutech_api.services.dashboard_service.check_database_connection", _async_true
        )
        monkeypatch.setattr(
            "arutech_api.services.dashboard_service.check_redis_connection", _async_false
        )

        admin = await _make_admin(db_session, email="admin-health-bad@example.com")
        admin_token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/admin/dashboard/system-health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
        assert body["redis_ok"] is False


async def _async_true() -> bool:
    return True


async def _async_false() -> bool:
    return False
