import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

from app.services.auth import crear_token, leer_token
from app.services.users import (
    registrar_usuario, autenticar_usuario, buscar_por_id, EmailYaRegistrado, CredencialesInvalidas,
)

app = FastAPI(title="Authly")
esquema_bearer = HTTPBearer()  # exige el header "Authorization: Bearer <token>" y habilita el botón Authorize en /docs


# Datos que esperamos recibir en el body del request
class RegistroEntrada(BaseModel):
    username: str
    email: EmailStr  # FastAPI rechaza con 422 si no tiene formato de email
    password: str


@app.post("/register", status_code=201)
def register(datos: RegistroEntrada):
    try:
        return registrar_usuario(datos.username, datos.email, datos.password)
    except EmailYaRegistrado as e:
        raise HTTPException(status_code=409, detail=str(e))  # conflicto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # password inválida


class LoginEntrada(BaseModel):
    email: EmailStr
    password: str


@app.post("/login")
def login(datos: LoginEntrada):
    try:
        usuario = autenticar_usuario(datos.email, datos.password)
    except CredencialesInvalidas as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"access_token": crear_token(usuario), "token_type": "bearer"}


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer)):
    # "guardia" que se ejecuta antes de la ruta: valida el token y busca al usuario
    try:
        id_usuario = leer_token(credenciales.credentials)
    except jwt.InvalidTokenError:  # token falso, alterado o vencido
        raise HTTPException(status_code=401, detail="Token inválido o vencido")
    usuario = buscar_por_id(id_usuario)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario


@app.get("/me")
def me(usuario: dict = Depends(usuario_actual)):
    return usuario
