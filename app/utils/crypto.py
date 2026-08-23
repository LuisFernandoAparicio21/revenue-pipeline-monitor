from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    """Cifra un token OAuth para almacenamiento seguro en DB."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Descifra un token OAuth almacenado en DB."""
    return _get_fernet().decrypt(encrypted.encode()).decode()
