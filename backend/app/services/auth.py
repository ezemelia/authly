from datetime import datetime, timedelta, timezone

import jwt

from app import config


def crear_token(claims: dict) -> str:
    """Genera un JWT RS256.

    claims debe incluir al menos 'sub'. 'iat' y 'exp' se agregan automáticamente.

    Ejemplos:
        Admin:   crear_token({"sub": admin_id, "type": "admin", "org_id": org_id})
        Usuario: crear_token({"sub": user_id, "type": "user", "org_id": org_id, "app_id": app_id})
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        **claims,
        "sub": str(claims["sub"]),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, config.JWT_PRIVATE_KEY, algorithm=config.JWT_ALGORITMO)


def leer_token(token: str) -> dict:
    """Decodifica y valida el JWT. Devuelve el payload completo (sub, type, org_id, …).

    Lanza jwt.InvalidTokenError si el token es inválido o venció.
    """
    return jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=[config.JWT_ALGORITMO])
