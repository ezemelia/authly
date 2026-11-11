from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from app.dependencies import usuario_actual
from app.services.auth import crear_token
from app.services.registro import pedir_codigo, confirmar_codigo, RegistroInvalido
from app.services.users import (
    autenticar_usuario, CredencialesInvalidas,
)

from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import manejar_error_http
from app.routers.applications import router as applications_router
from app.routers.recuperacion import router as recuperacion_router
from app.routers.roles import router as roles_router
from app.routers.usuarios import router as usuarios_router
from app.routers.auth_api import router as auth_api_router

app = FastAPI(title="Authly")

app.add_exception_handler(StarletteHTTPException, manejar_error_http)  # mismo formato de error en todo el panel

app.include_router(applications_router)
app.include_router(roles_router)
app.include_router(usuarios_router)
app.include_router(recuperacion_router)
app.include_router(auth_api_router)

class RegistroEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    email: EmailStr = Field(max_length=254)  # FastAPI rechaza con 422 si no tiene formato de email
    password: str = Field(max_length=128)
    organizacion: str = Field(max_length=200)
    cuit: str


class ConfirmacionEntrada(RegistroEntrada):
    codigo: str


def _error_registro(e: RegistroInvalido) -> JSONResponse:
    return JSONResponse(
        status_code=400, content={"detail": str(e), "campo": e.campo, "reinicio": e.reinicio}
    )


@app.post("/register/codigo")
def register_codigo(datos: RegistroEntrada):
    try:
        pedir_codigo(**datos.model_dump())
    except RegistroInvalido as e:
        return _error_registro(e)
    return {"detail": "Código enviado"}


@app.post("/register/confirmar", status_code=201)
def register_confirmar(datos: ConfirmacionEntrada):
    try:
        return confirmar_codigo(**datos.model_dump())
    except RegistroInvalido as e:
        return _error_registro(e)


class LoginEntrada(BaseModel):
    email: EmailStr
    password: str


@app.post("/login")
def login(datos: LoginEntrada):
    try:
        usuario = autenticar_usuario(datos.email, datos.password)
    except CredencialesInvalidas as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = crear_token({
        "sub": usuario["id"],
        "type": "admin",
        "org_id": str(usuario["organizacion_id"]),
    })
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
def me(usuario: dict = Depends(usuario_actual)):
    return usuario