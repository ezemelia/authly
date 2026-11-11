from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import usuario_actual
from app.errors import ErrorPanel
from app.services import roles as servicio
from app.services.roles import (
    AplicacionNoEncontrada, NombreRolDuplicado, RolConUsuarios, RolInvalido, RolNoEncontrado,
)

router = APIRouter(prefix="/platform/applications/{client_id}/roles", tags=["Roles"])


class PermisoEntrada(BaseModel):
    recurso: str = Field(max_length=100)
    accion: str = Field(max_length=100)


class RolEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    descripcion: str = Field(default="", max_length=500)
    por_defecto: bool = False
    permisos: list[PermisoEntrada] = []


def _como_error(e: Exception) -> ErrorPanel:
    if isinstance(e, AplicacionNoEncontrada):
        return ErrorPanel(404, str(e), motivo="aplicacion-inexistente")
    if isinstance(e, RolNoEncontrado):
        return ErrorPanel(404, str(e), motivo="rol-inexistente")
    if isinstance(e, RolInvalido):
        return ErrorPanel(400, str(e), campo=e.campo)
    if isinstance(e, NombreRolDuplicado):
        return ErrorPanel(409, str(e), campo="nombre")
    if isinstance(e, RolConUsuarios):
        return ErrorPanel(
            409,
            f"{e} Cámbieles el rol o elimínelos desde la gestión de usuarios.",
            motivo="tiene-usuarios",
            cantidad_usuarios=e.cantidad,
        )
    raise e


@router.get("/")
def listar(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return {"roles": servicio.listar_roles(client_id, admin["organizacion_id"])}
    except (AplicacionNoEncontrada,) as e:
        raise _como_error(e)


@router.post("/", status_code=201)
def crear(client_id: UUID, datos: RolEntrada, admin: dict = Depends(usuario_actual)):
    try:
        return servicio.crear_rol(
            client_id, admin["organizacion_id"], datos.nombre, datos.descripcion, datos.por_defecto,
            [p.model_dump() for p in datos.permisos],
        )
    except (AplicacionNoEncontrada, RolInvalido, NombreRolDuplicado) as e:
        raise _como_error(e)


@router.put("/{rol_id}")
def editar(client_id: UUID, rol_id: UUID, datos: RolEntrada, admin: dict = Depends(usuario_actual)):
    try:
        return servicio.editar_rol(
            client_id, rol_id, admin["organizacion_id"], datos.nombre, datos.descripcion, datos.por_defecto,
            [p.model_dump() for p in datos.permisos],
        )
    except (AplicacionNoEncontrada, RolNoEncontrado, RolInvalido, NombreRolDuplicado) as e:
        raise _como_error(e)


@router.delete("/{rol_id}")
def eliminar(client_id: UUID, rol_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return servicio.eliminar_rol(client_id, rol_id, admin["organizacion_id"])
    except (AplicacionNoEncontrada, RolNoEncontrado, RolConUsuarios) as e:
        raise _como_error(e)
