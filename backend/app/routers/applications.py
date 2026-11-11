from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import usuario_actual
from app.errors import ErrorPanel
from app.services.applications import (
    crear_aplicacion, NombreAppDuplicado, regenerar_secret,
    listar_aplicaciones, editar_aplicacion, eliminar_aplicacion,
    AplicacionConUsuarios, obtener_aplicacion,
)

router = APIRouter(prefix="/platform/applications", tags=["Aplicaciones"])


class AplicacionEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    descripcion: str = Field(default="", max_length=500)


def _no_encontrada(e: ValueError) -> ErrorPanel:
    # los ValueError de applications.py son "Aplicación no encontrada." o "El nombre es obligatorio."
    if "nombre" in str(e).lower():
        return ErrorPanel(400, str(e), campo="nombre")
    return ErrorPanel(404, str(e), motivo="aplicacion-inexistente")


@router.post("/", status_code=201)
def crear_app(datos: AplicacionEntrada, admin: dict = Depends(usuario_actual)):
    if not datos.nombre.strip():
        raise ErrorPanel(400, "El nombre es obligatorio.", campo="nombre")
    try:
        return crear_aplicacion(datos.nombre, datos.descripcion, admin["organizacion_id"])
    except NombreAppDuplicado as e:
        raise ErrorPanel(409, str(e), campo="nombre")


@router.get("/")
def listar_apps(
    pagina: int = 1,
    tamanio: int = 10,
    admin: dict = Depends(usuario_actual),
):
    return listar_aplicaciones(admin["organizacion_id"], pagina, tamanio)


@router.get("/{client_id}")
def obtener_app(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return obtener_aplicacion(client_id, admin["organizacion_id"])
    except ValueError as e:
        raise _no_encontrada(e)


@router.post("/{client_id}/regenerar-secret")
def regenerar(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return regenerar_secret(client_id, admin["organizacion_id"])
    except ValueError as e:
        raise _no_encontrada(e)


@router.put("/{client_id}")
def editar_app(client_id: UUID, datos: AplicacionEntrada, admin: dict = Depends(usuario_actual)):
    if not datos.nombre.strip():
        raise ErrorPanel(400, "El nombre es obligatorio.", campo="nombre")
    try:
        return editar_aplicacion(client_id, datos.nombre, datos.descripcion, admin["organizacion_id"])
    except NombreAppDuplicado as e:
        raise ErrorPanel(409, str(e), campo="nombre")
    except ValueError as e:
        raise _no_encontrada(e)


@router.delete("/{client_id}", status_code=204)
def eliminar_app(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        eliminar_aplicacion(client_id, admin["organizacion_id"])
    except ValueError as e:
        raise _no_encontrada(e)
    except AplicacionConUsuarios as e:
        raise ErrorPanel(409, str(e), motivo="tiene-usuarios", cantidad_usuarios=e.cantidad)
