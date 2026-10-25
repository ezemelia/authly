import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth import leer_token
from app.services.users import buscar_por_id

esquema_bearer = HTTPBearer()  # exige el header "Authorization: Bearer <token>" y habilita el botón Authorize en /docs


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer)):
    # "guardia" que se ejecuta antes de la ruta: valida el token y busca al administrador
    try:
        id_usuario = leer_token(credenciales.credentials)
    except jwt.InvalidTokenError:  # token falso, alterado o vencido
        raise HTTPException(status_code=401, detail="Token inválido o vencido")
    usuario = buscar_por_id(id_usuario)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario
