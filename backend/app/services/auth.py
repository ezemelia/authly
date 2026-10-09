from datetime import datetime, timedelta, timezone

import jwt

from app import config


def crear_token(usuario: dict) -> str:
    # "sub" (subject) identifica al usuario; "exp" es cuándo vence el token
    payload = {
        "sub": str(usuario["id"]),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRA_MINUTOS),
    }
    # se firma con la clave PRIVADA: solo quien la tiene puede crear tokens válidos
    return jwt.encode(payload, config.JWT_PRIVATE_KEY, algorithm=config.JWT_ALGORITMO)


def leer_token(token: str) -> int:
    """Devuelve el id del usuario del token; lanza jwt.InvalidTokenError si es falso o venció."""
    # se verifica con la clave PÚBLICA; decode revisa la firma y el vencimiento ("exp")
    payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=[config.JWT_ALGORITMO])
    return int(payload["sub"])
