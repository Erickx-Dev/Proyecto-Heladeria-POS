from __future__ import annotations

import bcrypt

from src.core.exceptions import ValidacionError


def hash_password(plain_password: str) -> str:
    if not plain_password or not plain_password.strip():
        raise ValidacionError("La contraseña no puede estar vacía.")

    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    resultado: str = hashed.decode("utf-8")

    if len(resultado) != 60:
        raise ValidacionError(
            f"El hash bcrypt generado tiene {len(resultado)} caracteres; se esperaban 60."
        )

    return resultado


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
