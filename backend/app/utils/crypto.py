import base64
import hashlib
from importlib import import_module

from app.core.config import get_settings
from app.core.exceptions import AppException


def _get_fernet():
    try:
        module = import_module("cryptography.fernet")
    except ModuleNotFoundError as exc:
        raise AppException(
            status_code=500,
            code="crypto_dependency_missing",
            message="cryptography dependency is required for mailbox credential encryption",
        ) from exc

    secret = get_settings().mailbox_credentials_secret.encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return module.Fernet(key)


def encrypt_secret(value: str) -> str:
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")

