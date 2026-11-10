from __future__ import annotations

import bcrypt

from src.core.exceptions import ValidacionError


def hash_password(plain_password: str) -> str:
    """
    Genera un hash criptográfico seguro usando el algoritmo bcrypt con sal aleatoria.
    El resultado siempre es una cadena de 60 caracteres (ej. '$2b$12$...'), donde se
    incluyen versión del algoritmo, factor de costo (12 rondas), sal (22 chars) y hash (31 chars).
    """
    if not plain_password or not plain_password.strip():
        raise ValidacionError("La contraseña no puede estar vacía.")

    # gensalt() genera una semilla aleatoria única para evitar ataques de tablas Rainbow
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    resultado: str = hashed.decode("utf-8")

    if len(resultado) != 60:
        raise ValidacionError(
            f"El hash bcrypt generado tiene {len(resultado)} caracteres; se esperaban 60."
        )

    return resultado


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano contra un hash bcrypt almacenado en base de datos.
    Extrae automáticamente la sal incrustada en 'hashed_password' para verificar la igualdad.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Si el hash almacenado tiene un formato corrupto, devuelve False de forma segura
        return False
