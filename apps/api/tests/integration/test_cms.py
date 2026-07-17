from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_auth_flows import _make_admin
from tests.integration.test_leads import _login, _make_employee

pytestmark = pytest.mark.asyncio

_GOOD_POST: dict[str, Any] = {
    "slug": "how-emis-work",
    "title": "How EMIs Actually Work",
    "excerpt": "A short primer on reducing-balance EMI math.",
    "author": "Arutech Editorial Team",
    "reading_minutes": 4,
    "sections": [
        {"heading": "The basics", "paragraphs": ["An EMI is a fixed monthly payment."]}
    ],
    "tags": ["EMI", "Personal Finance"],
}


class TestCmsAccess:
    async def test_employee_cannot_read_cms(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        employee = await _make_employee(db_session, email="cms-emp@example.com")
        token = await _login(client, employee.email)

        response = await client.get(
            "/api/v1/cms/blog-posts", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestCmsCrud:
    async def test_draft_post_is_invisible_to_the_public_endpoint(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="cms-admin1@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers
        )
        assert create_response.status_code == 200
        post = create_response.json()
        assert post["is_published"] is False

        public_response = await client.get(f"/api/v1/public/blog-posts/{post['slug']}")
        assert public_response.status_code == 404

        public_list = await client.get("/api/v1/public/blog-posts")
        assert not any(p["slug"] == post["slug"] for p in public_list.json())

    async def test_publish_makes_a_post_publicly_visible(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="cms-admin2@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        post = (
            await client.post("/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers)
        ).json()

        publish_response = await client.post(
            f"/api/v1/cms/blog-posts/{post['id']}/publish", headers=headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["is_published"] is True
        assert publish_response.json()["published_at"] is not None

        public_response = await client.get(f"/api/v1/public/blog-posts/{post['slug']}")
        assert public_response.status_code == 200
        assert public_response.json()["title"] == _GOOD_POST["title"]
        assert public_response.json()["sections"][0]["heading"] == "The basics"

        unpublish_response = await client.post(
            f"/api/v1/cms/blog-posts/{post['id']}/unpublish", headers=headers
        )
        assert unpublish_response.status_code == 200
        assert (await client.get(f"/api/v1/public/blog-posts/{post['slug']}")).status_code == 404

    async def test_update_and_delete_post(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="cms-admin3@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        post = (
            await client.post("/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers)
        ).json()

        update_payload = {**_GOOD_POST, "title": "How EMIs Really Work"}
        del update_payload["slug"]
        update_response = await client.put(
            f"/api/v1/cms/blog-posts/{post['id']}", json=update_payload, headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "How EMIs Really Work"

        delete_response = await client.delete(
            f"/api/v1/cms/blog-posts/{post['id']}", headers=headers
        )
        assert delete_response.status_code == 204

        get_response = await client.get(
            f"/api/v1/cms/blog-posts/{post['id']}", headers=headers
        )
        assert get_response.status_code == 404

    async def test_duplicate_slug_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="cms-admin4@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        await client.post("/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers)
        response = await client.post(
            "/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers
        )
        assert response.status_code == 409


class TestPublicBlogListing:
    async def test_unauthenticated_visitor_can_list_and_read_published_posts(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _make_admin(db_session, email="cms-admin5@example.com")
        token = await _login(client, admin.email)
        headers = {"Authorization": f"Bearer {token}"}

        post = (
            await client.post("/api/v1/cms/blog-posts", json=_GOOD_POST, headers=headers)
        ).json()
        await client.post(f"/api/v1/cms/blog-posts/{post['id']}/publish", headers=headers)

        list_response = await client.get("/api/v1/public/blog-posts")
        assert list_response.status_code == 200
        assert any(p["slug"] == "how-emis-work" for p in list_response.json())
