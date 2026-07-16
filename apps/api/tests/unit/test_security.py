import pytest

from arutech_api.core.security import (
    TokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_the_plaintext(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert hashed != "correct horse battery staple"

    def test_verify_accepts_the_correct_password(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", hashed) is True

    def test_verify_rejects_the_wrong_password(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert verify_password("wrong password", hashed) is False

    def test_same_password_produces_different_hashes(self) -> None:
        # Argon2 salts each hash, so two hashes of the same input must differ.
        assert hash_password("same-password") != hash_password("same-password")


class TestJwtTokens:
    def test_access_token_round_trips_the_subject(self) -> None:
        token = create_access_token(subject="user-123")
        payload = decode_token(token, TokenType.ACCESS)
        assert payload["sub"] == "user-123"
        assert payload["type"] == TokenType.ACCESS.value

    def test_refresh_token_round_trips_the_subject(self) -> None:
        token, jti = create_refresh_token(subject="user-123")
        payload = decode_token(token, TokenType.REFRESH)
        assert payload["sub"] == "user-123"
        assert payload["type"] == TokenType.REFRESH.value
        assert payload["jti"] == jti

    def test_access_token_rejected_when_a_refresh_token_is_expected(self) -> None:
        token = create_access_token(subject="user-123")
        with pytest.raises(TokenError):
            decode_token(token, TokenType.REFRESH)

    def test_tampered_token_is_rejected(self) -> None:
        token = create_access_token(subject="user-123")
        # Flip a character in the middle of the signature rather than the
        # very last character of the token: base64url's final, incomplete
        # group can have low-order bits that don't affect the decoded
        # bytes, so mutating the last character is not reliably detected.
        mid = len(token) // 2
        flipped = "A" if token[mid] != "A" else "B"
        tampered = token[:mid] + flipped + token[mid + 1 :]
        with pytest.raises(TokenError):
            decode_token(tampered, TokenType.ACCESS)

    def test_expired_token_is_rejected(self) -> None:
        from datetime import timedelta

        from arutech_api.core.security import _create_token

        token, _ = _create_token("user-123", TokenType.ACCESS, timedelta(seconds=-1))
        with pytest.raises(TokenError):
            decode_token(token, TokenType.ACCESS)

    def test_extra_claims_are_included(self) -> None:
        token = create_access_token(subject="user-123", extra_claims={"role": "admin"})
        payload = decode_token(token, TokenType.ACCESS)
        assert payload["role"] == "admin"

    def test_each_token_has_a_unique_jti(self) -> None:
        token_a = create_access_token(subject="user-123")
        token_b = create_access_token(subject="user-123")
        payload_a = decode_token(token_a, TokenType.ACCESS)
        payload_b = decode_token(token_b, TokenType.ACCESS)
        assert payload_a["jti"] != payload_b["jti"]
