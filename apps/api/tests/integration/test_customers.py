import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin, _register
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio


class TestCustomerProfile:
    async def test_get_customer_lazily_creates_a_profile(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust1@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            f"/api/v1/customers/{customer['id']}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["user"]["email"] == "cust1@example.com"
        assert body["segment"] == "new"
        assert body["tags"] == []
        assert body["relationship_manager_id"] is None

    async def test_getting_an_employee_as_a_customer_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            f"/api/v1/customers/{employee.id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 409

    async def test_getting_an_unknown_user_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.get(
            "/api/v1/customers/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestCustomerAccessControl:
    async def test_customer_cannot_read_the_crm(self, client: AsyncClient) -> None:
        await _register(client, email="selfserve@example.com")
        token = await _login(client, "selfserve@example.com")

        response = await client.get(
            "/api/v1/customers", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    async def test_unauthenticated_request_is_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/customers")
        assert response.status_code == 401

    async def test_employee_can_read_the_crm(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client, email="cust2@example.com")
        employee = await _make_employee(db_session)
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/customers", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestRelationshipManager:
    async def test_assign_relationship_manager(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust3@example.com")
        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/customers/{customer['id']}/relationship-manager",
            json={"relationship_manager_id": str(employee.id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["relationship_manager_id"] == str(employee.id)

    async def test_cannot_assign_a_customer_as_relationship_manager(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust4@example.com")
        other_customer = await _register(client, email="cust5@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/customers/{customer['id']}/relationship-manager",
            json={"relationship_manager_id": other_customer["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_assigning_an_unknown_relationship_manager_is_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust6@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/customers/{customer['id']}/relationship-manager",
            json={"relationship_manager_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestCustomerSegment:
    async def test_set_segment(self, client: AsyncClient, db_session: AsyncSession) -> None:
        customer = await _register(client, email="cust7@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/customers/{customer['id']}/segment",
            json={"segment": "high_value"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["segment"] == "high_value"


class TestCustomerTags:
    async def test_add_and_remove_tag(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust8@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        add_response = await client.post(
            f"/api/v1/customers/{customer['id']}/tags", json={"tag": "vip"}, headers=headers
        )
        assert add_response.status_code == 200
        assert add_response.json()["tags"] == ["vip"]

        list_response = await client.get("/api/v1/customers/tags", headers=headers)
        assert list_response.json() == ["vip"]

        remove_response = await client.delete(
            f"/api/v1/customers/{customer['id']}/tags/vip", headers=headers
        )
        assert remove_response.status_code == 200
        assert remove_response.json()["tags"] == []

    async def test_adding_the_same_tag_twice_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust9@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/customers/{customer['id']}/tags", json={"tag": "priority"}, headers=headers
        )
        response = await client.post(
            f"/api/v1/customers/{customer['id']}/tags", json={"tag": "priority"}, headers=headers
        )
        assert response.json()["tags"] == ["priority"]


class TestCustomerList:
    async def test_filter_by_segment(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        high_value = await _register(client, email="hv@example.com")
        await _register(client, email="plainnew@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/customers/{high_value['id']}/segment",
            json={"segment": "high_value"},
            headers=headers,
        )

        response = await client.get(
            "/api/v1/customers", params={"segment": "high_value"}, headers=headers
        )
        assert response.status_code == 200
        emails = [c["user"]["email"] for c in response.json()]
        assert emails == ["hv@example.com"]

    async def test_filter_by_relationship_manager(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        assigned = await _register(client, email="assigned@example.com")
        await _register(client, email="unassigned@example.com")
        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/customers/{assigned['id']}/relationship-manager",
            json={"relationship_manager_id": str(employee.id)},
            headers=headers,
        )

        response = await client.get(
            "/api/v1/customers",
            params={"relationship_manager_id": str(employee.id)},
            headers=headers,
        )
        assert response.status_code == 200
        emails = [c["user"]["email"] for c in response.json()]
        assert emails == ["assigned@example.com"]


class TestInteractions:
    async def test_log_and_list_interaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust10@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/v1/customers/{customer['id']}/interactions",
            json={
                "channel": "call",
                "summary": "Discussed loan options",
                "notes": "Interested in a personal loan",
                "direction": "outbound",
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["channel"] == "call"
        assert body["occurred_at"] is not None

        listed = await client.get(
            f"/api/v1/customers/{customer['id']}/interactions", headers=headers
        )
        assert len(listed.json()) == 1

    async def test_logging_an_interaction_for_a_non_customer_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session)
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)

        response = await client.post(
            f"/api/v1/customers/{employee.id}/interactions",
            json={"channel": "email", "summary": "N/A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409


class TestCustomerTimeline:
    async def test_timeline_includes_audit_and_interaction_entries(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer = await _register(client, email="cust11@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/customers/{customer['id']}/segment",
            json={"segment": "active"},
            headers=headers,
        )
        await client.post(
            f"/api/v1/customers/{customer['id']}/interactions",
            json={"channel": "note", "summary": "Called to follow up"},
            headers=headers,
        )

        response = await client.get(
            f"/api/v1/customers/{customer['id']}/timeline", headers=headers
        )
        assert response.status_code == 200
        kinds = {entry["kind"] for entry in response.json()}
        assert kinds == {"audit", "interaction"}


class TestCustomerAnalytics:
    async def test_summary_reflects_state(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        customer_a = await _register(client, email="analytics-a@example.com")
        await _register(client, email="analytics-b@example.com")
        admin = await _make_admin(db_session)
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Touch both so profiles exist for the count.
        await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers)
        await client.get(
            f"/api/v1/customers/{customer_a['id']}", headers=headers
        )  # idempotent re-touch
        await client.post(
            f"/api/v1/customers/{customer_a['id']}/segment",
            json={"segment": "high_value"},
            headers=headers,
        )
        await client.post(
            f"/api/v1/customers/{customer_a['id']}/interactions",
            json={"channel": "call", "summary": "hi"},
            headers=headers,
        )

        response = await client.get("/api/v1/customers/analytics/summary", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["by_segment"]["high_value"] == 1
        assert body["total_interactions"] == 1
        assert body["by_channel"]["call"] == 1
