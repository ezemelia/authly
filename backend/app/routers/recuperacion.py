from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.errors import ErrorPanel
from app.services.recuperacion import MENSAJE_GENERICO, RecuperacionInvalida, cambiar_password, pedir_codigo

router = APIRouter(prefix="/recovery", tags=["Recuperación de contraseña"])


class PedirCodigoEntrada(BaseModel):
    email: str = Field(max_length=254)  # str y no EmailStr: un formato inválido tampoco revela nada


class CambiarPasswordEntrada(BaseModel):
    email: str = Field(max_length=254)
    codigo: str = Field(max_length=6)
    password: str = Field(max_length=128)


@router.post("/codigo")
def pedir(datos: PedirCodigoEntrada):
    pedir_codigo(datos.email)
    return {"detail": MENSAJE_GENERICO}


@router.post("/confirmar")
def confirmar(datos: CambiarPasswordEntrada):
    try:
        cambiar_password(datos.email, datos.codigo, datos.password)
    except RecuperacionInvalida as e:
        raise ErrorPanel(400, str(e), campo=e.campo)
    return {"detail": "Su contraseña fue actualizada."}
