from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config import JWT_PUBLIC_KEY
from app.middleware.app_credentials import aplicacion_actual
from app.services.auth import crear_token
from app.services.users import autenticar_usuario_app, CredencialesInvalidas

router = APIRouter(prefix="/auth", tags=["API Externa - Auth"])


class LoginUsuarioEntrada(BaseModel):
    email: str
    password: str


@router.get("/public-key")
def obtener_clave_publica():
    """CU-08: Devuelve la clave pública RSA para verificar tokens JWT.
    Endpoint público — no requiere autenticación.
    """
    return {"public_key": JWT_PUBLIC_KEY}


@router.post("/login")
def login_usuario(datos: LoginUsuarioEntrada, app: dict = Depends(aplicacion_actual)):
    """CU-07: Login de usuario de una aplicación externa.
    Requiere X-Client-Id y X-Client-Secret en headers.
    """
    try:
        usuario = autenticar_usuario_app(datos.email, datos.password, app["id"])
    except CredencialesInvalidas as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = crear_token({
        "sub": usuario["id"],
        "type": "user",
        "org_id": app["organizacion_id"],
        "app_id": app["id"],
    })

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 28800,
    }