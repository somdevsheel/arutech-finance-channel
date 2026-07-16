"""Generates a dev-only RS256 keypair for JWT signing and prints .env lines.

Usage: uv run python scripts/generate_jwt_keypair.py >> .env

Production keys must come from a secrets manager (e.g. AWS Secrets Manager /
Vault), never from this script — `core.config.get_settings()` refuses to
start in staging/production without JWT_PRIVATE_KEY/JWT_PUBLIC_KEY set.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )

    print(f"JWT_PRIVATE_KEY=\"{private_pem.replace(chr(10), '\\n')}\"")
    print(f"JWT_PUBLIC_KEY=\"{public_pem.replace(chr(10), '\\n')}\"")


if __name__ == "__main__":
    main()
