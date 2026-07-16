import re

from arutech_api.core.security import (
    generate_otp_code,
    hash_otp,
    hash_refresh_token,
    verify_otp,
)


class TestOtpCode:
    def test_generates_a_six_digit_numeric_code(self) -> None:
        code = generate_otp_code()
        assert re.fullmatch(r"\d{6}", code)

    def test_codes_are_not_all_identical(self) -> None:
        codes = {generate_otp_code() for _ in range(20)}
        assert len(codes) > 1


class TestOtpHashing:
    def test_hash_is_not_the_plaintext(self) -> None:
        assert hash_otp("123456") != "123456"

    def test_verify_accepts_the_correct_code(self) -> None:
        hashed = hash_otp("123456")
        assert verify_otp("123456", hashed) is True

    def test_verify_rejects_the_wrong_code(self) -> None:
        hashed = hash_otp("123456")
        assert verify_otp("654321", hashed) is False

    def test_hash_is_deterministic(self) -> None:
        # Unlike password hashing, OTP hashing must be deterministic (no
        # per-hash salt) since it's looked up by equality, not verified via
        # a constant-time comparison against a stored salted hash.
        assert hash_otp("123456") == hash_otp("123456")


class TestRefreshTokenHashing:
    def test_hash_is_deterministic(self) -> None:
        assert hash_refresh_token("some.jwt.token") == hash_refresh_token("some.jwt.token")

    def test_different_tokens_hash_differently(self) -> None:
        assert hash_refresh_token("token-a") != hash_refresh_token("token-b")
