import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.infrastructure.database.models.contact import ContactSubmission

pytestmark = pytest.mark.asyncio


async def test_valid_submission_is_stored(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post(
        "/api/v1/public/contact",
        json={
            "name": "Grace Hopper",
            "email": "grace@example.com",
            "phone": "+919876543210",
            "subject": "Question about home loans",
            "message": "What documents do I need for a home loan?",
        },
    )
    assert response.status_code == 200

    result = await db_session.execute(select(ContactSubmission))
    submissions = result.scalars().all()
    assert len(submissions) == 1
    assert submissions[0].email == "grace@example.com"
    assert submissions[0].subject == "Question about home loans"


async def test_invalid_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/public/contact",
        json={
            "name": "Grace Hopper",
            "email": "not-an-email",
            "subject": "Question",
            "message": "Hello",
        },
    )
    assert response.status_code == 422


async def test_missing_required_field_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/public/contact",
        json={"name": "Grace Hopper", "email": "grace@example.com"},
    )
    assert response.status_code == 422


async def test_honeypot_filled_pretends_success_without_storing(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/api/v1/public/contact",
        json={
            "name": "Spam Bot",
            "email": "bot@example.com",
            "subject": "Cheap loans!!!",
            "message": "Click here",
            "website": "http://spam.example.com",
        },
    )
    assert response.status_code == 200

    result = await db_session.execute(select(ContactSubmission))
    assert result.scalars().all() == []
