import uuid
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
from tests.conftest import CapturingOtpDelivery

pytestmark = pytest.mark.asyncio

_PASSWORD = "s3cure-Passw0rd!"


async def _register(client: AsyncClient, email: str = "ada@example.com") -> dict[str, Any]:
    # No phone: it's unique-constrained, and tests that register more than
    # one account (e.g. cross-user session checks) would otherwise collide
    # on a shared hardcoded number.
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": _PASSWORD, "full_name": "Ada Lovelace"},
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


async def _make_admin(db_session: AsyncSession, email: str = "admin@example.com") -> UserEntity:
    user_repo = SqlAlchemyUserRepository(db_session)
    rbac_repo = SqlAlchemyRbacRepository(db_session)

    user = await user_repo.create(
        UserEntity(
            email=email,
            hashed_password=hash_password(_PASSWORD),
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
    )
    role = await rbac_repo.get_role_by_name("admin")
    assert role is not None
    await rbac_repo.assign_role_to_user(user.id, role.id)
    await db_session.commit()
    return user


class TestRegistration:
    async def test_register_creates_a_customer_account(self, client: AsyncClient) -> None:
        body = await _register(client)
        assert body["email"] == "ada@example.com"
        assert body["role"] == "customer"
        assert body["is_active"] is True

    async def test_register_rejects_duplicate_email(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "ada@example.com",
                "password": _PASSWORD,
                "full_name": "Someone Else",
            },
        )
        assert response.status_code == 409

    async def test_register_rejects_weak_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "password": "short", "full_name": "Weak Pw"},
        )
        assert response.status_code == 422


class TestPasswordLogin:
    async def test_login_with_correct_credentials(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["user"]["email"] == "ada@example.com"

    async def test_login_with_wrong_password_is_generic(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": "wrong-password"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_login_with_unknown_email_gives_same_generic_error(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_login_rejects_an_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        registered = await _register(client)
        user_repo = SqlAlchemyUserRepository(db_session)
        user = await user_repo.get_by_id(uuid.UUID(registered["id"]))
        assert user is not None
        await user_repo.update(
            UserEntity(
                id=user.id,
                email=user.email,
                hashed_password=user.hashed_password,
                full_name=user.full_name,
                phone=user.phone,
                role=user.role,
                is_active=False,
                is_verified=user.is_verified,
            )
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_me_requires_a_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_returns_the_authenticated_user(self, client: AsyncClient) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        token = login.json()["access_token"]

        response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "ada@example.com"


class TestOtpLogin:
    async def test_request_then_verify_otp_logs_in(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        await _register(client)

        request_response = await client.post(
            "/api/v1/auth/otp/request", json={"email": "ada@example.com"}
        )
        assert request_response.status_code == 200
        code = otp_delivery.last_code

        verify_response = await client.post(
            "/api/v1/auth/otp/verify", json={"email": "ada@example.com", "code": code}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["user"]["email"] == "ada@example.com"

    async def test_otp_request_for_unknown_email_is_silently_ok(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        response = await client.post(
            "/api/v1/auth/otp/request", json={"email": "nobody@example.com"}
        )
        assert response.status_code == 200
        assert otp_delivery.sent == []  # nothing was actually generated/sent

    async def test_verify_otp_for_unknown_email_is_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/otp/verify", json={"email": "nobody@example.com", "code": "123456"}
        )
        assert response.status_code == 401

    async def test_wrong_otp_code_is_rejected(self, client: AsyncClient) -> None:
        await _register(client)
        await client.post("/api/v1/auth/otp/request", json={"email": "ada@example.com"})

        response = await client.post(
            "/api/v1/auth/otp/verify", json={"email": "ada@example.com", "code": "000000"}
        )
        assert response.status_code == 401

    async def test_otp_cannot_be_reused(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        await _register(client)
        await client.post("/api/v1/auth/otp/request", json={"email": "ada@example.com"})
        code = otp_delivery.last_code

        first = await client.post(
            "/api/v1/auth/otp/verify", json={"email": "ada@example.com", "code": code}
        )
        assert first.status_code == 200

        second = await client.post(
            "/api/v1/auth/otp/verify", json={"email": "ada@example.com", "code": code}
        )
        assert second.status_code == 401


class TestPasswordReset:
    async def test_reset_request_for_unknown_email_is_silently_ok(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        response = await client.post(
            "/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"}
        )
        assert response.status_code == 200
        assert otp_delivery.sent == []

    async def test_reset_confirm_for_unknown_email_is_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"email": "nobody@example.com", "code": "123456", "new_password": "N3w-Pw0rd!"},
        )
        assert response.status_code == 401

    async def test_reset_then_login_with_new_password(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        await _register(client)
        await client.post("/api/v1/auth/password-reset/request", json={"email": "ada@example.com"})
        code = otp_delivery.last_code

        confirm = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "email": "ada@example.com",
                "code": code,
                "new_password": "N3w-Passw0rd!",
            },
        )
        assert confirm.status_code == 200

        old_login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        assert old_login.status_code == 401

        new_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "ada@example.com", "password": "N3w-Passw0rd!"},
        )
        assert new_login.status_code == 200

    async def test_reset_revokes_existing_sessions(
        self, client: AsyncClient, otp_delivery: CapturingOtpDelivery
    ) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        old_refresh_token = login.json()["refresh_token"]

        await client.post("/api/v1/auth/password-reset/request", json={"email": "ada@example.com"})
        code = otp_delivery.last_code
        await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"email": "ada@example.com", "code": code, "new_password": "N3w-Passw0rd!"},
        )

        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
        )
        assert refresh_response.status_code == 401


class TestRefreshRotation:
    async def test_refresh_rejects_a_malformed_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-jwt"}
        )
        assert response.status_code == 401

    async def test_refresh_rejects_an_access_token_used_as_a_refresh_token(
        self, client: AsyncClient
    ) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        access_token = login.json()["access_token"]

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert response.status_code == 401

    async def test_logout_with_a_malformed_token_is_a_no_op(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": "not-a-real-jwt"}
        )
        assert response.status_code == 200

    async def test_refresh_issues_a_new_pair_and_rotates_the_old_one(
        self, client: AsyncClient
    ) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        old_refresh_token = login.json()["refresh_token"]

        refreshed = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
        )
        assert refreshed.status_code == 200
        new_refresh_token = refreshed.json()["refresh_token"]
        assert new_refresh_token != old_refresh_token

    async def test_reusing_a_rotated_refresh_token_revokes_all_sessions(
        self, client: AsyncClient
    ) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        old_refresh_token = login.json()["refresh_token"]

        first_refresh = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
        )
        assert first_refresh.status_code == 200
        new_refresh_token = first_refresh.json()["refresh_token"]

        # Replaying the already-rotated token is treated as token theft: it
        # should fail, AND burn the legitimately-issued token from the
        # rotation above too.
        replay = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
        )
        assert replay.status_code == 401

        followup = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
        )
        assert followup.status_code == 401

    async def test_logout_revokes_the_refresh_token(self, client: AsyncClient) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        refresh_token = login.json()["refresh_token"]

        logout = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert logout.status_code == 200

        refresh_after_logout = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_after_logout.status_code == 401


class TestSessions:
    async def test_list_and_revoke_a_session(self, client: AsyncClient) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        access_token = login.json()["access_token"]
        refresh_token = login.json()["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        sessions = await client.get("/api/v1/auth/sessions", headers=headers)
        assert sessions.status_code == 200
        assert len(sessions.json()) == 1
        session_id = sessions.json()[0]["id"]

        revoke = await client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers)
        assert revoke.status_code == 200

        refresh_after_revoke = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_after_revoke.status_code == 401

    async def test_revoking_someone_elses_session_is_rejected(self, client: AsyncClient) -> None:
        await _register(client, email="ada@example.com")
        await _register(client, email="grace@example.com")

        ada_login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        grace_login = await client.post(
            "/api/v1/auth/login", json={"email": "grace@example.com", "password": _PASSWORD}
        )
        grace_headers = {"Authorization": f"Bearer {grace_login.json()['access_token']}"}

        ada_sessions = await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {ada_login.json()['access_token']}"},
        )
        ada_session_id = ada_sessions.json()[0]["id"]

        response = await client.delete(
            f"/api/v1/auth/sessions/{ada_session_id}", headers=grace_headers
        )
        assert response.status_code == 401

    async def test_logout_all_revokes_every_session(self, client: AsyncClient) -> None:
        await _register(client)
        login_a = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        login_b = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        access_token = login_a.json()["access_token"]

        logout_all = await client.post(
            "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_all.status_code == 200

        for refresh_token in (login_a.json()["refresh_token"], login_b.json()["refresh_token"]):
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )
            assert response.status_code == 401


class TestAuditLogRbac:
    async def test_customer_cannot_read_audit_logs(self, client: AsyncClient) -> None:
        await _register(client)
        login = await client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
        )
        token = login.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    async def test_admin_can_read_audit_logs(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(client)  # generates at least one audit log entry
        await _make_admin(db_session)

        login = await client.post(
            "/api/v1/auth/login", json={"email": "admin@example.com", "password": _PASSWORD}
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        actions = [entry["action"] for entry in response.json()]
        assert "user.registered" in actions
