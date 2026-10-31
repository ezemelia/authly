import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth import leer_token
from app.services.users import buscar_por_id

esquema_bearer = HTTPBearer()  # exige el header "Authorization: Bearer <token>" y habilita el botón Authorize en /docs


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer)):
    """Dependency que valida el JWT y devuelve los datos del administrador.

    Rechaza tokens que no sean de tipo 'admin'.
    """
    try:
        payload = leer_token(credenciales.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")

    if payload.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Token no autorizado para esta operación")

    usuario = buscar_por_id(payload["sub"])
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario
